## BACKEND MODULES (FastAPI)

**Core Models**
- CLIP Model: Encode images & text → 512-dim vectors
- Fusion Engine: Combine embeddings (α = image weight, 0-1)
- Formula: E_fusion = α·E_image + (1-α)·E_text

**API Layer**
- Search Endpoint: POST /api/v1/search (text + image)
- Auth Module: JWT login/register, secure endpoints
- Cart & Orders: Full e-commerce workflow

**Search Infrastructure**
- FAISS Index: HNSW algorithm for fast retrieval
- Performance: <250ms query latency
- Metric: InnerProduct (cosine similarity)

---

## DATA FLOW PIPELINE

User Input (Text/Image/Both)
    ↓
CLIP Encoding (Parallel)
    ├─ Text → 512-dim vector
    └─ Image → 512-dim vector
    ↓
Fusion Engine: Ef = α·Ei + (1-α)·Et
    ↓
FAISS Search: Return Top-K Products
    ↓
Frontend Results Display

---

## FRONTEND MODULES (Next.js + React)

**State Management**
- AuthContext: User login, JWT tokens, preferences
- CartContext: Shopping cart, checkout workflow

**Pages**
- Search (/): Text + image + alpha slider
- Product (/product/[id]): Details & recommendations
- Cart (/cart): Item management, total price
- Orders (/orders): Order history & tracking

**Components**
- ProtectedRoute: Auth-required pages
- UI Kit: Button, Dialog, Slider (alpha control)
- UserMenu: Profile, orders, logout

---

## KEY METRICS & TECH STACK

Query Latency: <250ms ✓
CLIP Encoding: <100ms ✓
FAISS Search: <50ms ✓
Throughput: 20 req/s ✓
Memory: <600MB ✓

Backend: FastAPI, PyTorch, CLIP, FAISS, JWT
Frontend: Next.js, React, TypeScript, Tailwind CSS
Deployment: Docker Compose, Nginx, ASGI

