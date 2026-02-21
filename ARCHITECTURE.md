# Hybrid Cross-Modal Recommendation System - Architecture

## 🎯 System Overview

A production-grade **Hybrid Cross-Modal Deep Learning Framework** for personalized fashion product recommendations using CLIP embeddings, FAISS vector similarity search, and real-time e-commerce data integration.

```
┌─────────────────┐
│  Frontend       │ (Next.js 14+ / React 18)
│  (Vercel)       │
└────────┬────────┘
         │ (REST API / Axios)
┌────────▼────────┐
│  API Gateway    │ (FastAPI)
├─────────────────┤
│ Request Handler │
│ Validation      │
│ Rate Limiter    │
└────────┬────────┘
         │
    ┌────┴────┬─────────────┬────────────┐
    │          │             │            │
┌───▼──┐   ┌──▼───┐   ┌────▼──┐   ┌───▼──┐
│ CLIP │   │FAISS │   │Cache  │   │Ranks │
│Model │   │Index │   │Redis  │   │Engine│
└──────┘   └──────┘   └───────┘   └──────┘
    │          │             │            │
    └────┬─────┴─────────────┴────────────┘
         │
    ┌────▼─────────────┐
    │ E-commerce API   │
    │ Product Metadata │
    └──────────────────┘
```

---

## 📐 Core Architecture Components

### 1. **Frontend Layer** (Next.js App Router)
- **Pages:**
  - `/` - Landing page (search interface)
  - `/results` - Product recommendations grid
  - `/products/[id]` - Product detail page
  - `/auth/login` - Authentication
  - `/auth/register` - User registration
  - `/admin/dashboard` - Analytics dashboard

- **Key Features:**
  - Responsive UI with Tailwind CSS + shadcn/ui
  - Client-side state management (Zustand)
  - Form validation (React Hook Form)
  - Image optimization (Next/Image)
  - Error boundaries & loading states
  - Dark/Light theme toggle

### 2. **API Layer** (FastAPI Backend)
- **Endpoints:**
  - `POST /api/v1/recommend` - Hybrid recommendations
  - `POST /api/v1/text-search` - Text-only search
  - `POST /api/v1/image-search` - Image-only search
  - `GET /api/v1/product/{id}` - Product details
  - `GET /api/v1/similar-products/{id}` - Similar items
  - `GET /api/v1/admin/stats` - Analytics

- **Middleware:**
  - CORS handling
  - Rate limiting
  - Request validation
  - Error handling
  - Logging

### 3. **CLIP Embedding Service** (Python)
- **Components:**
  - `CLIPModel` - Load & inference
  - `EmbeddingCache` - Redis caching
  - `FusionEngine` - Hybrid embedding fusion
  - `SimilaritySearch` - FAISS ranking

- **Algorithm:**
  ```
  Ef = α * Ei + (1 - α) * Et
  
  Where:
  Ei = normalized image embedding
  Et = normalized text embedding
  α = fusion weight (0.0-1.0)
  Ef = fused embedding
  ```

### 4. **Vector Database** (FAISS)
- **Index Structure:**
  - IVF (Inverted File) for large datasets
  - L2 distance metric
  - Product ID mapping
  - Persistence to disk

### 5. **Data Layer**
- **E-commerce API Integration:**
  - Real-time product fetching
  - Metadata enrichment
  - Image URL resolution
  - Inventory status

- **Caching Strategy:**
  - Redis for embeddings (TTL: 24hrs)
  - FAISS index persistence
  - Product metadata cache

---

## 🔄 Request Flow

### Hybrid Search (Text + Image)

```
1. User submits: text + image + weight (α)
   ↓
2. Frontend: Validate & upload image
   ↓
3. API: Parse FormData
   ↓
4. CLIP: 
   - Encode text → Et
   - Encode image → Ei
   - Normalize embeddings
   ↓
5. Fusion: Ef = α * Ei + (1-α) * Et
   ↓
6. FAISS: Search(Ef) → Top-K indices
   ↓
7. E-commerce API: Fetch metadata for Top-K
   ↓
8. Ranking: Sort by similarity + relevance
   ↓
9. Response: Return recommendations with scores
   ↓
10. Cache: Store query results (optional)
```

---

## 📊 Database Schema

### PostgreSQL (Optional - for user data)

```sql
-- Users Table
CREATE TABLE users (
  id UUID PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  name VARCHAR(255),
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Search Logs
CREATE TABLE search_logs (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  query_type VARCHAR(50), -- 'text', 'image', 'hybrid'
  query_text TEXT,
  image_url VARCHAR(500),
  fusion_weight FLOAT,
  timestamp TIMESTAMP DEFAULT NOW(),
  results_count INT,
  top_result_id VARCHAR(100)
);

-- Favorites
CREATE TABLE favorites (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  product_id VARCHAR(100) NOT NULL,
  added_at TIMESTAMP DEFAULT NOW()
);

-- Embeddings Cache
CREATE TABLE embedding_cache (
  id UUID PRIMARY KEY,
  content_hash VARCHAR(64) UNIQUE NOT NULL,
  embedding BYTEA NOT NULL,
  content_type VARCHAR(20), -- 'text', 'image'
  created_at TIMESTAMP DEFAULT NOW(),
  expires_at TIMESTAMP
);
```

---

## 🔐 Security Architecture

### Authentication Flow
```
User Login → JWT Token → HTTP-Only Cookie
                    ↓
            Token Validation on each request
                    ↓
            Role-based Access Control (RBAC)
```

### API Security
- **Rate Limiting:** 100 req/min per IP
- **Input Validation:** Pydantic models
- **File Upload:** Size limits, MIME type checking
- **XSS Protection:** Content Security Policy headers
- **CORS:** Whitelist trusted domains

---

## 📦 Deployment Architecture

### Frontend (Vercel)
```
GitHub Push → GitHub Actions
           ↓
        Build & Test
           ↓
        Deploy to Vercel
           ↓
        Edge caching
```

### Backend (Render/Railway)
```
GitHub Push → GitHub Actions
           ↓
        Build Docker image
           ↓
        Run tests
           ↓
        Push to container registry
           ↓
        Deploy to Render
```

### Vector Database & Cache
```
FAISS Index → Persistent storage (S3)
Redis Cache → Managed Redis instance
```

---

## 🎯 Performance Targets

| Metric | Target |
|--------|--------|
| API Response Time | < 500ms |
| CLIP Inference | < 200ms |
| FAISS Search | < 100ms |
| Page Load Time (FCP) | < 1.2s |
| Time to Interactive (TTI) | < 2.5s |
| Lighthouse Score | > 90 |

---

## 📋 Technology Stack Summary

| Layer | Technology |
|-------|-----------|
| **Frontend** | Next.js 14+, React 18, TypeScript, Tailwind CSS, shadcn/ui |
| **State Management** | Zustand |
| **Form Handling** | React Hook Form |
| **HTTP Client** | Axios |
| **Backend API** | FastAPI, Uvicorn |
| **ML Framework** | PyTorch |
| **CLIP Model** | OpenAI CLIP |
| **Vector DB** | FAISS |
| **Cache** | Redis |
| **Database** | PostgreSQL (optional) |
| **Storage** | AWS S3 |
| **Deployment** | Docker, GitHub Actions |
| **Frontend Hosting** | Vercel |
| **Backend Hosting** | Render/Railway |

---

## 📅 Implementation Timeline

- **Phase 0:** Architecture & Design (1-2 days)
- **Phase 1:** Frontend Foundation (2-3 days)
- **Phase 2:** CLIP Microservice (3-4 days)
- **Phase 3:** E-commerce Integration (2-3 days)
- **Phase 4:** Full Stack Integration (2-3 days)
- **Phase 5:** Advanced Features (3-5 days)
- **Phase 6-10:** Auth, Optimization, Testing, Deployment (4-5 days)

**Total Duration:** ~4-5 weeks for production-ready system

---

## 🚀 Next Steps

1. ✅ **Phase 0 Complete:** Architecture documented
2. **Phase 1:** Convert to Next.js 14+ with App Router
3. **Phase 2:** Enhance CLIP service with caching & fusion
4. **Phase 3:** Integrate real e-commerce API
5. **Phase 4-10:** Progressive enhancement & deployment

---

**Last Updated:** February 21, 2026
**Status:** Production Ready - Architecture Phase Complete
