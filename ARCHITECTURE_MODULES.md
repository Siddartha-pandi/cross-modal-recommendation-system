# Hybrid Cross-Modal Recommendation System - Module Architecture

## System Overview
This is a production-ready hybrid recommendation engine using CLIP embeddings + FAISS similarity search for fashion products. The system combines text and image inputs through weighted fusion to deliver precise recommendations.

---

## Backend Architecture (FastAPI)

### 1. **Core Models Module** (`backend/app/models/`)

#### 1.1 CLIP Model (`clip_model.py`)
**Purpose:** Encode images and text into 512-dimensional vectors using OpenAI's CLIP

```
Module: CLIPModel
├── Methods:
│   ├── __init__(model_name, device)
│   ├── encode_image(image) → np.ndarray
│   ├── encode_text(text) → np.ndarray
│   ├── batch_encode_images(images) → List[np.ndarray]
│   └── batch_encode_text(texts) → List[np.ndarray]
├── Properties:
│   ├── device (cuda/cpu)
│   ├── model_name (ViT-B/32)
│   └── image_transform (ImageNet normalization)
└── Outputs:
    └── Normalized 512-dim embeddings
```

**Key Features:**
- Async encoding for high throughput
- GPU/CPU auto-detection
- Batch processing support
- Normalized outputs for similarity computation

---

#### 1.2 Fusion Engine (`fusion.py`)
**Purpose:** Combine image and text embeddings with adjustable dominance

```
Module: FusionEngine
├── Fusion Strategies:
│   ├── weighted_avg: Ef = α·Ei + (1-α)·Et
│   ├── gate_mechanism: learned gates for adaptive fusion
│   └── cross_modal_attention: attention-based fusion
├── Methods:
│   ├── fuse(image_emb, text_emb, alpha, method) → (fused_emb, scores)
│   ├── set_fusion_strategy(strategy)
│   └── compute_match_score(fused_emb, candidates)
├── Parameters:
│   ├── alpha ∈ [0.0, 1.0] (image weight)
│   └── default_alpha = 0.7
└── Outputs:
    ├── Fused embedding (512-dim)
    └── Explainability scores
```

**Alpha Values:**
- α = 0.0: Text-only search
- α = 0.5: Balanced image-text
- α = 1.0: Image-only search

---

#### 1.3 Product Cart Model (`cart.py`)
**Purpose:** User shopping cart management

```
Module: CartItem, Cart
├── CartItem:
│   ├── product_id
│   ├── quantity
│   ├── price
│   └── metadata
├── Cart:
│   ├── Methods:
│   │   ├── add_item(product_id, quantity)
│   │   ├── remove_item(product_id)
│   │   ├── update_quantity(product_id, quantity)
│   │   ├── get_total_price()
│   │   └── serialize() → dict
│   └── Properties:
│       ├── user_id
│       └── items: List[CartItem]
└── Storage:
    └── JSON: backend/data/carts.json
```

---

### 2. **Authentication Module** (`backend/app/auth/`)

#### 2.1 Auth Models (`models.py`)
```
Module: User, AuthToken
├── User:
│   ├── user_id
│   ├── email
│   ├── hashed_password
│   ├── created_at
│   └── preferences (alpha, search_history)
├── AuthToken:
│   ├── access_token
│   ├── token_type: "bearer"
│   └── expires_in
└── Storage:
    └── JSON: backend/data/users.json
```

#### 2.2 Auth Routes (`routes.py`)
```
Endpoints:
├── POST /auth/register
│   └── Creates new user account
├── POST /auth/login
│   └── Returns JWT token
├── POST /auth/logout
│   └── Invalidates session
└── GET /auth/me
    └── Returns current user info
```

#### 2.3 Auth Utilities (`utils.py`)
```
Functions:
├── hash_password(password) → str
├── verify_password(plain, hashed) → bool
├── create_jwt_token(user_id, expires_in) → str
├── decode_jwt_token(token) → dict
└── require_auth() → User (dependency)
```

---

### 3. **API Routes Module** (`backend/app/api/`)

#### 3.1 Main Search Routes (`routes.py`)
```
Endpoint: POST /api/v1/search
├── Request:
│   ├── text: str (optional)
│   ├── image: str (base64, optional)
│   ├── alpha: float ∈ [0, 1]
│   └── top_k: int (1-20)
├── Processing Pipeline:
│   ├── 1. Encode inputs (CLIP)
│   ├── 2. Fuse embeddings (alpha)
│   ├── 3. Search FAISS index
│   ├── 4. Re-rank results
│   └── 5. Format response
└── Response:
    ├── results: List[ProductResult]
    ├── query_time_ms: float
    ├── search_type: str (text/image/hybrid)
    ├── alpha_used: float
    └── fusion_info: dict (explainability)

Response Time Target: <250ms
```

**Search Types:**
- **Text-only** (α=0.0): Pure text matching
- **Image-only** (α=1.0): Pure visual matching
- **Hybrid** (0<α<1): Combined modal search

#### 3.2 Cart Routes (`cart_routes.py`)
```
Endpoints:
├── GET /api/v1/cart
│   └── Get user's cart
├── POST /api/v1/cart
│   └── Add product to cart
├── PUT /api/v1/cart/{product_id}
│   └── Update quantity
├── DELETE /api/v1/cart/{product_id}
│   └── Remove from cart
├── POST /api/v1/orders
│   └── Create order from cart
└── GET /api/v1/orders
    └── Get user's order history
```

---

### 4. **Utils Module** (`backend/app/utils/`)

#### 4.1 FAISS Index Manager (`faiss_index.py`)
**Purpose:** High-speed similarity search using FAISS HNSW index

```
Module: FAISSIndex
├── Methods:
│   ├── __init__(index_path, dimension=512)
│   ├── load_index() → None
│   ├── build_index(embeddings, product_ids) → None
│   ├── search(query_embedding, k=3) → (distances, indices)
│   ├── add_embeddings(embeddings, ids) → None
│   └── save_index() → None
├── Index Configuration:
│   ├── Type: HNSW (Hierarchical Navigable Small World)
│   ├── Dimension: 512
│   ├── Metric: InnerProduct (cosine)
│   ├── M: 32 (neighbors per node)
│   ├── efConstruction: 200
│   └── efSearch: 100
└── Index File:
    └── index/products.index
```

**HNSW Advantages:**
- Sub-linear search time complexity
- Efficient memory usage
- Dynamic index updates
- High recall (≈99%)

---

### 5. **Main Application Module** (`main.py`)

```
Module: FastAPI App
├── Initialization:
│   ├── CORS configuration
│   ├── Middleware setup
│   ├── Model initialization (CLIP)
│   ├── FAISS index loading
│   └── Fusion engine setup
├── Routers:
│   ├── SearchRouter (/api/v1)
│   ├── AuthRouter (/auth)
│   ├── CartRouter (/api/v1)
│   └── OrderRouter (/api/v1)
├── Middleware:
│   ├── CORS (allow localhost:3000, *.vercel.app)
│   ├── Logging
│   └── Error handling
└── Configuration:
    ├── Title: Cross-Modal Fashion Recommendation API
    ├── Version: 1.0.0
    ├── Docs: /docs (Swagger UI)
    └── Port: 8000
```

---

## Frontend Architecture (Next.js + React)

### 1. **Context Module** (`frontend/app/contexts/`)

#### 1.1 Auth Context (`AuthContext.tsx`)
```
Context: AuthProvider
├── State:
│   ├── user: User | null
│   ├── isAuthenticated: boolean
│   ├── token: string | null
│   └── loading: boolean
├── Functions:
│   ├── login(email, password) → Promise<User>
│   ├── register(email, password, name) → Promise<User>
│   ├── logout() → void
│   └── getCurrentUser() → User
└── Hook:
    └── useAuth() → {user, login, logout, ...}
```

#### 1.2 Cart Context (`CartContext.tsx`)
```
Context: CartProvider
├── State:
│   ├── items: CartItem[]
│   ├── total: number
│   └── itemCount: number
├── Functions:
│   ├── addToCart(product_id, quantity) → void
│   ├── removeFromCart(product_id) → void
│   ├── updateQuantity(product_id, quantity) → void
│   ├── getCart() → CartItem[]
│   └── checkout() → Promise<Order>
└── Hook:
    └── useCart() → {items, total, addToCart, ...}
```

---

### 2. **Components Module** (`frontend/app/components/`)

#### 2.1 ProtectedRoute (`ProtectedRoute.tsx`)
```
Component: ProtectedRoute
├── Props:
│   ├── children: React.ReactNode
│   └── requiredRole?: "user" | "admin"
├── Behavior:
│   ├── Check authentication
│   ├── Redirect to /login if unauthorized
│   └── Render children if authorized
└── Usage:
    └── Wrap pages requiring auth
```

#### 2.2 UserMenu (`UserMenu.tsx`)
```
Component: UserMenu
├── Features:
│   ├── Display user name
│   ├── Dropdown menu
│   ├── Profile link
│   ├── Orders link
│   └── Logout button
└── Connected:
    └── useAuth() for user data
```

#### 2.3 UI Components (`components/ui/`)
```
├── button.tsx: Reusable button component
├── dialog.tsx: Modal dialog component
├── slider.tsx: Alpha value slider (0-1)
├── tabs.tsx: Tab navigation component
└── Search UI:
    ├── Text input
    ├── Image upload
    ├── Alpha slider
    └── Results display
```

---

### 3. **Pages Module** (`frontend/app/`)

#### 3.1 Home/Search (`page.tsx`)
```
Page: /
├── Features:
│   ├── Text search input
│   ├── Image upload
│   ├── Alpha slider (0-1)
│   ├── Search button
│   ├── Results grid
│   └── Add to cart buttons
├── API Calls:
│   └── POST /api/v1/search
└── State:
    ├── searchQuery: string
    ├── alpha: float
    ├── results: ProductResult[]
    └── loading: boolean
```

#### 3.2 Authentication Pages
```
├── Login (`login/page.tsx`)
│   ├── Email input
│   ├── Password input
│   └── Submit button
├── Register (`register/page.tsx`)
│   ├── Name input
│   ├── Email input
│   ├── Password input
│   └── Confirm password
└── Forgot Password (`forgot-password/page.tsx`)
    └── Password reset flow
```

#### 3.3 Cart (`cart/page.tsx`)
```
Page: /cart
├── Features:
│   ├── List cart items
│   ├── Update quantities
│   ├── Remove items
│   ├── Display total
│   └── Checkout button
└── Connected:
    └── useCart() for cart management
```

#### 3.4 Orders (`orders/page.tsx`)
```
Pages:
├── List page (`orders/page.tsx`)
│   ├── Show all user orders
│   ├── Order status
│   ├── Order date
│   └── Total amount
└── Detail page (`orders/[order_id]/page.tsx`)
    ├── Order items
    ├── Delivery address
    ├── Payment info
    └── Status timeline
```

#### 3.5 Product Detail (`product/[product_id]/page.tsx`)
```
Page: /product/{id}
├── Display:
│   ├── Product image
│   ├── Title & description
│   ├── Price
│   ├── Category
│   └── Similar products
├── Actions:
│   ├── Add to cart
│   └── View details
└── API Calls:
    └── GET /api/v1/products/{id}
```

---

### 4. **Contexts & Hooks**

```
Contexts:
├── AuthContext
│   └── Hook: useAuth()
├── CartContext
│   └── Hook: useCart()
└── Custom Hooks:
    ├── useSearch(query, alpha)
    ├── useProducts(category)
    └── useOrders()
```

---

## Data Models

### Product Schema
```json
{
  "product_id": "string",
  "title": "string",
  "description": "string",
  "image_url": "string",
  "price": "float",
  "category": "string",
  "embedding": "float[512]",  // CLIP embedding
  "tags": ["string"]
}
```

### User Schema
```json
{
  "user_id": "string",
  "email": "string",
  "hashed_password": "string",
  "name": "string",
  "created_at": "timestamp",
  "preferences": {
    "default_alpha": 0.5,
    "search_history": ["string"]
  }
}
```

### Order Schema
```json
{
  "order_id": "string",
  "user_id": "string",
  "items": [
    {
      "product_id": "string",
      "quantity": "int",
      "price": "float"
    }
  ],
  "total": "float",
  "status": "pending|processing|shipped|delivered",
  "created_at": "timestamp"
}
```

---

## Data Flow

### Search Pipeline
```
User Input (Text/Image/Both)
    ↓
Validation & Preprocessing
    ↓
CLIP Encoding (Parallel)
    ├─ encode_image()
    └─ encode_text()
    ↓
Fusion Engine
    └─ Ef = α·Ei + (1-α)·Et
    ↓
FAISS Search
    └─ find k-nearest products
    ↓
Re-ranking & Filtering
    ↓
Format Results
    ↓
Return to Frontend
```

### Cart → Order Pipeline
```
User Adds Products to Cart
    ↓
Cart Stored in Frontend & Backend
    ↓
User Proceeds to Checkout
    ↓
Create Order (POST /api/v1/orders)
    ↓
Update Inventory
    ↓
Send Confirmation
    ↓
Redirect to Order Detail
```

---

## API Contract

### Key Endpoints

| Method | Endpoint | Auth | Purpose |
|--------|----------|------|---------|
| POST | `/api/v1/search` | No | Hybrid search |
| GET | `/api/v1/products` | No | List products |
| GET | `/api/v1/products/{id}` | No | Product detail |
| POST | `/auth/register` | No | User registration |
| POST | `/auth/login` | No | User login |
| GET | `/api/v1/cart` | Yes | Get user cart |
| POST | `/api/v1/cart` | Yes | Add to cart |
| POST | `/api/v1/orders` | Yes | Create order |
| GET | `/api/v1/orders` | Yes | List user orders |

---

## Configuration Files

### Backend Config
- **`PROJECT_CONFIG.json`**: Model parameters, API config, test cases
- **`requirements.txt`**: Python dependencies (FastAPI, CLIP, FAISS, etc.)
- **`pytest.ini`**: Test runner configuration

### Frontend Config
- **`package.json`**: Node dependencies, scripts
- **`tsconfig.json`**: TypeScript configuration
- **`tailwind.config.js`**: Tailwind CSS settings
- **`next.config.js`**: Next.js runtime configuration

### Deployment
- **`docker-compose.yml`**: Multi-container orchestration
- **`Dockerfile`**: Backend image build
- **`nginx/nginx.unified.conf`**: Reverse proxy & static serving

---

## Dependencies Overview

### Backend
```
fastapi          → Web framework
uvicorn          → ASGI server
clip             → OpenAI's vision-language model
faiss-cpu/gpu    → Vector similarity search
torch            → Deep learning framework
pydantic         → Data validation
python-jose      → JWT authentication
```

### Frontend
```
next.js          → React framework
react-18         → UI library
typescript       → Type safety
tailwind-css     → Styling
axios            → HTTP client
zustand/context  → State management
```

---

## Performance Metrics

| Metric | Target | Status |
|--------|--------|--------|
| Single query latency | <250ms | ✓ |
| FAISS search | <50ms | ✓ |
| CLIP encoding | <100ms | ✓ |
| Fusion computation | <10ms | ✓ |
| Average throughput | 20 req/s | ✓ |
| Memory usage | <600MB | ✓ |

---

## Module Dependencies

```
Frontend Layer
    ├── API Calls → Backend Routes
    └── State Management → Contexts

Backend Routes
    ├── Auth Module → JWT validation
    ├── Search Module → Models (CLIP, Fusion, FAISS)
    ├── Cart Module → Cart Model
    └── Order Module → Database

Models Layer
    ├── CLIP → Torch, transformers
    ├── Fusion → NumPy
    ├── FAISS → Vector similarity
    └── Cart → JSON storage

Utils Layer
    └── FAISS Index → Embeddings storage
```

---

## Development Workflow

### Setup
```bash
# Backend
pip install -r backend/requirements.txt
python backend/scripts/build_fashion_index.py

# Frontend
npm install --prefix frontend
```

### Running
```bash
# Backend (port 8000)
uvicorn app.main:app --reload

# Frontend (port 3000)
npm run dev --prefix frontend

# Or use Docker
docker-compose up
```

### Testing
```bash
# Pytest
pytest backend/

# Test cases defined in PROJECT_CONFIG.json
# 20 structured test cases covering all modalities
```

---

## Summary

This modular architecture enables:
- **Scalability**: Independent module scaling
- **Maintainability**: Clear separation of concerns
- **Testability**: Each module independently testable
- **Extensibility**: Easy to add new fusion strategies, models, or API endpoints
- **Performance**: Optimized FAISS search + async processing
- **Type Safety**: Full TypeScript + Pydantic validation
