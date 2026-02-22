# Postman Collection for Cross-Modal Recommendation API

This directory contains Postman collections and environments for testing the API.

## Files

- **cross-modal-recommendation.postman_collection.json** - Complete API collection with all endpoints
- **Local.postman_environment.json** - Local development environment (http://localhost:8000)
- **Production.postman_environment.json** - Production environment template

## Quick Start

### 1. Import Collection

1. Open Postman
2. Click **Import** in the top-left
3. Drag and drop `cross-modal-recommendation.postman_collection.json`
4. Collection will appear in the left sidebar

### 2. Import Environment

1. Click the **Environments** tab (left sidebar)
2. Click **Import**
3. Import `Local.postman_environment.json`
4. Select the "Local Development" environment from the top-right dropdown

### 3. Test Endpoints

Start your backend server:
```bash
cd backend
python start_server.py
```

Then run requests in this order:

#### Basic Health Check
- **GET** Health (root) - Verify server is running

#### Core Search Endpoints
- **POST** Workflow Search - Text-only search
- **POST** Enhanced Search - Live e-commerce search
- **POST** Advanced Search - Search with sentiment/occasion

#### E-commerce Integration
- **GET** Ecommerce Sources - List available sources
- **POST** Ecommerce Fetch - Fetch live products
- **POST** Ecommerce Search and Embed - Fetch and index products

#### Index Management
- **GET** Index Status - Check FAISS index stats
- **GET** Index Health - Health check
- **POST** Index Rebuild - Rebuild index (admin)

#### Cache
- **GET** Cache Stats - View cache statistics
- **POST** Cache Clear - Clear cache

## Variables

The collection uses these variables (set in environment):

- `{{baseUrl}}` - Base API URL (e.g., http://localhost:8000)
- `{{apiBase}}` - API prefix (e.g., /api/v1)

## Example Requests

### Text Search
```json
POST {{baseUrl}}{{apiBase}}/search/workflow
{
  "text": "blue summer dress",
  "top_k": 10,
  "text_weight": 1.0,
  "image_weight": 0.0
}
```

### Hybrid Search (Text + Image)
```json
POST {{baseUrl}}{{apiBase}}/search/workflow
{
  "text": "elegant dress",
  "image": "<base64-encoded-image>",
  "top_k": 12,
  "text_weight": 0.4,
  "image_weight": 0.6,
  "fusion_method": "weighted_avg"
}
```

### Live E-commerce Fetch
```
POST {{baseUrl}}{{apiBase}}/ecommerce/fetch?query=shoes&max_results_per_source=15
```

### Context-Aware Search
```json
POST {{baseUrl}}{{apiBase}}/search/advanced
{
  "text": "formal outfit",
  "top_k": 10,
  "enable_sentiment_scoring": true,
  "enable_occasion_ranking": true,
  "occasion": "business",
  "mood": "confident"
}
```

## Testing Multipart Requests

For endpoints accepting file uploads (e.g., `/search/workflow-multipart`, `/upload`):

1. Select **Body** tab
2. Choose **form-data**
3. For file field, change type to **File**
4. Click **Select Files** and choose an image

## Authentication

Currently, no authentication is required. When auth is added, set these environment variables:
- `{{apiKey}}` - API key
- `{{token}}` - Bearer token

## Notes

- All searches return product recommendations with similarity scores
- Image uploads must be JPEG, PNG, or WebP
- Text queries are limited to 500 characters
- Results include: product_id, title, price, category, image_url, similarity_score
- Live e-commerce sources: Amazon, Flipkart, Myntra, IKEA, Meesho, Platzi (all free APIs)

## Troubleshooting

**Connection Refused**
- Ensure backend server is running on port 8000
- Check `baseUrl` in your environment

**503 Service Unavailable**
- Models may not be loaded yet
- Wait ~30 seconds after server start for CLIP model initialization

**Empty Results**
- Index may be empty - run `/ecommerce/search-and-embed` first
- Try broader search queries

## Support

For API documentation, visit: http://localhost:8000/docs (when server is running)
