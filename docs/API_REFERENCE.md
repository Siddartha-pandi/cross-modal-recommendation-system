# Cross-Modal Recommendation System - API Reference

## Table of Contents
1. [Base URL](#base-url)
2. [Authentication](#authentication)
3. [Search Endpoints](#search-endpoints)
4. [Product Endpoints](#product-endpoints)
5. [Cache Management](#cache-management)
6. [Admin Endpoints](#admin-endpoints)
7. [Error Codes](#error-codes)

---

## Base URL

**Development:** `http://localhost:8000/api/v1`  
**Production:** `https://your-domain.com/api/v1`

All API requests must be prefixed with the base URL.

---

## Authentication

The API uses **JWT (JSON Web Tokens)** for authentication.

### Register User

```http
POST /auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePass123",
  "full_name": "John Doe"
}
```

**Response (201 Created):**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "user": {
    "id": "user_123",
    "email": "user@example.com",
    "full_name": "John Doe"
  }
}
```

### Login

```http
POST /auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePass123"
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

### Get Current User

```http
GET /auth/me
Authorization: Bearer {access_token}
```

**Response (200 OK):**
```json
{
  "id": "user_123",
  "email": "user@example.com",
  "full_name": "John Doe",
  "created_at": "2024-01-15T10:30:00Z"
}
```

### Change Password

```http
PUT /auth/change-password
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "current_password": "SecurePass123",
  "new_password": "NewSecurePass456"
}
```

**Response (200 OK):**
```json
{
  "message": "Password changed successfully"
}
```

---

## Search Endpoints

### Text Search

Search products using text query only.

```http
POST /text-search?query={query}&top_k={k}
```

**Parameters:**
- `query` (string, required): Text search query
- `top_k` (integer, optional): Number of results to return (default: 10)

**Example:**
```http
POST /text-search?query=red%20summer%20dress&top_k=5
```

**Response (200 OK):**
```json
{
  "status": "success",
  "query": "red summer dress",
  "results": [
    {
      "product_id": "PROD_001",
      "title": "Red Floral Summer Dress",
      "category": "Dresses",
      "price": 49.99,
      "brand": "FashionBrand",
      "image_url": "https://example.com/dress1.jpg",
      "similarity_score": 0.95,
      "explanation": "Strong match based on text query..."
    }
  ],
  "query_time_ms": 145.3,
  "cached": false
}
```

### Image Search

Search products using uploaded image.

```http
POST /image-search
Content-Type: multipart/form-data

file: [image file]
top_k: 10
```

**Example (cURL):**
```bash
curl -X POST "http://localhost:8000/api/v1/image-search?top_k=5" \
  -F "file=@dress.jpg"
```

**Response (200 OK):**
```json
{
  "status": "success",
  "results": [
    {
      "product_id": "PROD_002",
      "title": "Similar Red Dress",
      "similarity_score": 0.92,
      ...
    }
  ],
  "query_time_ms": 234.7
}
```

### Hybrid Recommendation

Search using both text and image (multimodal fusion).

```http
POST /recommend
Content-Type: application/json

{
  "text": "red summer dress",
  "image": "base64_encoded_image_string",
  "alpha": 0.7,
  "top_k": 10,
  "filters": {
    "category": "Dresses",
    "price_min": 30.0,
    "price_max": 100.0
  },
  "enable_diversity": true
}
```

**Parameters:**
- `text` (string, optional): Text query
- `image` (string, optional): Base64-encoded image
- `alpha` (float, optional): Image-text fusion weight (0.0-1.0, default: 0.7)
  - `alpha=1.0`: Image-only search
  - `alpha=0.0`: Text-only search
  - `alpha=0.7`: 70% image, 30% text
- `top_k` (integer, optional): Number of results (default: 10)
- `filters` (object, optional): Filter criteria
- `enable_diversity` (boolean, optional): Enable diversity reranking (default: false)

**Response (200 OK):**
```json
{
  "status": "success",
  "query_id": "q_a8f3d92b",
  "results": [
    {
      "product_id": "PROD_001",
      "title": "Red Summer Dress",
      "price": 49.99,
      "similarity_score": 0.94,
      "match_scores": {
        "image_contribution": 0.7,
        "text_contribution": 0.3,
        "image_text_alignment": 0.85,
        "fusion_quality": 0.92
      },
      "explanation": "Excellent match: Visual similarity (70%) and description (30%) both align well..."
    }
  ],
  "metadata": {
    "query_time_ms": 187.5,
    "fusion_method": "weighted_avg",
    "cached": false,
    "total_candidates": 1000,
    "filtered_count": 250
  }
}
```

---

## Product Endpoints

### Get Product Details

```http
GET /products/{product_id}
```

**Response (200 OK):**
```json
{
  "product_id": "PROD_001",
  "title": "Red Summer Dress",
  "description": "Beautiful flowing red dress perfect for summer...",
  "price": 49.99,
  "brand": "FashionBrand",
  "category": "Dresses",
  "image_url": "https://example.com/dress1.jpg",
  "images": [
    "https://example.com/dress1.jpg",
    "https://example.com/dress1_alt1.jpg"
  ],
  "specifications": {
    "Material": "100% Cotton",
    "Size": "M",
    "Color": "Red"
  },
  "rating": 4.5,
  "review_count": 128,
  "in_stock": true
}
```

### Get Similar Products

```http
GET /products/{product_id}/similar?top_k={k}
```

**Parameters:**
- `top_k` (integer, optional): Number of similar products (default: 5)

**Response (200 OK):**
```json
{
  "status": "success",
  "original_product_id": "PROD_001",
  "similar_products": [
    {
      "product_id": "PROD_015",
      "title": "Similar Red Dress",
      "similarity_score": 0.88,
      ...
    }
  ]
}
```

---

## Cache Management

### Get Cache Statistics

```http
GET /cache/stats
Authorization: Bearer {admin_token}
```

**Response (200 OK):**
```json
{
  "cache_status": "healthy",
  "total_keys": 1523,
  "memory_used_mb": 45.3,
  "hit_rate": 0.78,
  "embedding_cache": {
    "text_embeddings": 856,
    "image_embeddings": 432
  },
  "search_results_cache": {
    "cached_queries": 235
  }
}
```

### Invalidate Cache

```http
POST /cache/invalidate
Authorization: Bearer {admin_token}
Content-Type: application/json

{
  "cache_type": "embeddings",
  "pattern": "text:*"
}
```

**Parameters:**
- `cache_type` (string): Cache type (`embeddings`, `search_results`, `all`)
- `pattern` (string, optional): Redis key pattern to match

**Response (200 OK):**
```json
{
  "status": "success",
  "invalidated_keys": 856
}
```

---

## Admin Endpoints

### System Health Check

```http
GET /health
```

**Response (200 OK):**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "services": {
    "clip_model": "loaded",
    "faiss_index": "ready",
    "redis_cache": "connected",
    "database": "connected"
  },
  "index_size": 10543,
  "uptime_seconds": 86400
}
```

### System Statistics

```http
GET /admin/stats
Authorization: Bearer {admin_token}
```

**Response (200 OK):**
```json
{
  "total_searches": 15234,
  "unique_users": 1823,
  "avg_response_time_ms": 187.5,
  "search_breakdown": {
    "text_only": 8234,
    "image_only": 3421,
    "hybrid": 3579
  },
  "top_categories": [
    {"category": "Dresses", "count": 4523},
    {"category": "Tops", "count": 3821}
  ],
  "cache_performance": {
    "hit_rate": 0.78,
    "avg_hit_time_ms": 12.3,
    "avg_miss_time_ms": 245.7
  }
}
```

---

## Error Codes

### HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Request successful |
| 201 | Created | Resource created successfully |
| 400 | Bad Request | Invalid request parameters |
| 401 | Unauthorized | Missing or invalid authentication |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 422 | Unprocessable Entity | Validation error |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |
| 503 | Service Unavailable | Service temporarily unavailable |

### Error Response Format

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request parameters",
    "details": {
      "field": "top_k",
      "issue": "Must be between 1 and 100"
    }
  }
}
```

### Common Error Codes

- `AUTHENTICATION_REQUIRED`: Missing JWT token
- `INVALID_TOKEN`: Expired or malformed JWT token
- `VALIDATION_ERROR`: Request validation failed
- `PRODUCT_NOT_FOUND`: Product ID doesn't exist
- `RATE_LIMIT_EXCEEDED`: Too many requests
- `SERVICE_UNAVAILABLE`: CLIP model or FAISS index not ready
- `CACHE_ERROR`: Redis connection failed

---

## Rate Limiting

**API Endpoints:** 10 requests/second/IP  
**Search Endpoints:** 5 requests/second/IP

Rate limit headers are included in responses:
```
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 7
X-RateLimit-Reset: 1642345678
```

---

## Best Practices

1. **Always cache access tokens** - Don't request new tokens for every API call
2. **Use hybrid search for best results** - Set `alpha=0.7` for balanced image-text fusion
3. **Enable diversity for browsing** - Set `enable_diversity=true` to avoid similar duplicates
4. **Apply filters early** - Use filters to reduce candidate set and improve speed
5. **Monitor rate limits** - Check `X-RateLimit-*` headers to avoid throttling
6. **Handle errors gracefully** - Always check for 503 errors and implement retry logic

---

## SDK Examples

### Python

```python
import requests

class RecommendationAPI:
    def __init__(self, base_url, token):
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {token}"}
    
    def search_text(self, query, top_k=10):
        response = requests.post(
            f"{self.base_url}/text-search",
            params={"query": query, "top_k": top_k}
        )
        return response.json()
    
    def recommend_hybrid(self, text, image_path, alpha=0.7):
        with open(image_path, 'rb') as f:
            image_b64 = base64.b64encode(f.read()).decode()
        
        response = requests.post(
            f"{self.base_url}/recommend",
            json={"text": text, "image": image_b64, "alpha": alpha},
            headers=self.headers
        )
        return response.json()

# Usage
api = RecommendationAPI("http://localhost:8000/api/v1", "your_token")
results = api.search_text("red dress", top_k=5)
```

### JavaScript

```javascript
class RecommendationAPI {
  constructor(baseUrl, token) {
    this.baseUrl = baseUrl;
    this.token = token;
  }

  async searchText(query, topK = 10) {
    const response = await fetch(
      `${this.baseUrl}/text-search?query=${encodeURIComponent(query)}&top_k=${topK}`
    );
    return await response.json();
  }

  async recommendHybrid(text, imageFile, alpha = 0.7) {
    const reader = new FileReader();
    const imageB64 = await new Promise((resolve) => {
      reader.onload = (e) => resolve(e.target.result.split(',')[1]);
      reader.readAsDataURL(imageFile);
    });

    const response = await fetch(`${this.baseUrl}/recommend`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.token}`
      },
      body: JSON.stringify({ text, image: imageB64, alpha })
    });

    return await response.json();
  }
}

// Usage
const api = new RecommendationAPI('http://localhost:8000/api/v1', 'your_token');
const results = await api.searchText('red dress', 5);
```

---

**For more information, visit:** [Interactive API Docs](http://localhost:8000/api/v1/docs)
