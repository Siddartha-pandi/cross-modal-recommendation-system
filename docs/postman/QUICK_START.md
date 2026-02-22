# Quick Start: Using Postman with Cross-Modal Recommendation API

## Setup (2 minutes)

### Step 1: Import Collection
1. Open Postman Desktop or Web
2. Click **Import** button (top-left)
3. Drag `docs/postman/cross-modal-recommendation.postman_collection.json` into the import dialog
4. Click **Import**

### Step 2: Import Environment
1. Click **Environments** icon in left sidebar (or use icon in top-left)
2. Click **Import**
3. Drag `docs/postman/Local.postman_environment.json` into the import dialog
4. Click **Import**

### Step 3: Activate Environment
1. Click the environment dropdown in top-right corner
2. Select **"Local Development"**
3. You'll see a green checkmark next to it

## Test Your Setup

### 1. Health Check
- **Request:** GET Health (root)
- **Expected:** `{ "status": "healthy", "models": { "clip_loaded": true, "faiss_loaded": true } }`
- **If fails:** Make sure backend server is running on port 8000

### 2. Simple Text Search
- **Request:** POST Workflow Search
- **Body:** Already pre-filled with sample data
- **Click:** Send
- **Expected:** Returns ~6 product results with similarity scores

### 3. Check E-commerce Sources
- **Request:** GET Ecommerce Sources
- **Expected:** List of 6 integrated sources (Amazon, Flipkart, Myntra, etc.)

## Common Workflows

### Search for Products by Text
```
POST {{baseUrl}}{{apiBase}}/search/workflow
Body: JSON
{
  "text": "summer dress",
  "top_k": 10,
  "text_weight": 1.0,
  "image_weight": 0.0,
  "fusion_method": "weighted_avg"
}
```

### Search with Image Upload
```
POST {{baseUrl}}{{apiBase}}/search/workflow-multipart
Body: form-data
- text: "blue dress"
- image: [Select File from your computer]
- top_k: 10
- image_weight: 0.7
- text_weight: 0.3
```

### Fetch Live Products from E-commerce
```
POST {{baseUrl}}{{apiBase}}/ecommerce/fetch?query=shoes&max_results_per_source=15
```

### Context-Aware Search
```
POST {{baseUrl}}{{apiBase}}/search/advanced
Body: JSON
{
  "text": "wedding outfit",
  "top_k": 10,
  "enable_sentiment_scoring": true,
  "enable_occasion_ranking": true,
  "occasion": "wedding",
  "mood": "elegant",
  "season": "summer"
}
```

## Variables Reference

Your collection uses these variables (automatically set by environment):

| Variable | Value (Local) | Description |
|----------|---------------|-------------|
| `{{baseUrl}}` | http://localhost:8000 | API base URL |
| `{{apiBase}}` | /api/v1 | API version prefix |

## Tips

1. **View Raw Response:** Click the "Pretty" dropdown and select "Raw" to see the actual JSON
2. **Save Responses:** Click "Save Response" to save example responses for documentation
3. **Test Scripts:** You can add JavaScript tests in the "Tests" tab to automate validation
4. **Response Time:** Check the bottom-right for request duration (should be <500ms for most endpoints)

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Connection refused | Start backend: `cd backend && python start_server.py` |
| 503 Service Unavailable | Wait 30s for models to load, then retry |
| Empty search results | Run `/ecommerce/search-and-embed?query=dress&max_results=20` first |
| Invalid image format | Use JPEG, PNG, or WebP only |

## Next Steps

1. **Explore All Endpoints:** The collection has 18 requests organized by category
2. **Customize Requests:** Edit body/params to test different scenarios
3. **Run Collections:** Use Postman's Collection Runner to test all endpoints at once
4. **Export Results:** Generate API documentation from your collection

## API Documentation

Interactive docs available at: http://localhost:8000/docs (FastAPI Swagger UI)
