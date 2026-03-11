# Quick Start Guide - Advanced Recommendation System

## Overview

This guide will help you get started with the advanced multi-stage recommendation system.

## Prerequisites

- Python 3.8+
- Node.js 16+
- 16GB RAM (for loading CLIP models)
- GPU (optional, but recommended)

## Installation

### 1. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Install dependencies
pip install -r requirements.txt

# Install additional dependencies for advanced features
pip install faiss-cpu  # or faiss-gpu if you have CUDA
pip install pillow numpy torch torchvision
pip install clip-by-openai
pip install duckduckgo-search
```

### 2. Build Product Index

Before using the advanced recommendation endpoint, you need to build the product embeddings:

```bash
# From the backend directory
python -m backend.scripts.build_product_index
```

This will:
- Load all products from `data/products.json`
- Generate CLIP embeddings for each product image
- Build a FAISS index for fast similarity search
- Save index to `index/products.index`

**Expected output:**
```
================================================================================
Building Product Embeddings and FAISS Index
================================================================================
Loading CLIP model: ViT-L/14
Initializing product catalog...
Found 150 products
Building product embeddings (this may take a while)...
Processed 100 products...
✓ Successfully built embeddings for 150 products
✓ FAISS index saved to: s:\...\index
================================================================================
```

**Time:** ~10-15 minutes for 150 products (depends on your hardware)

### 3. Start Backend Server

```bash
# From backend directory
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

**Expected startup log:**
```
==================================================
Starting Cross-Modal Recommendation System
==================================================
Loading CLIP model (ViT-B/32) for FAISS search...
✓ CLIP ViT-B/32 loaded successfully
Loading CLIP model (ViT-L/14) for web-search recommend...
✓ CLIP ViT-L/14 loaded successfully (1024-dim)
Initializing Fusion Engine...
✓ Fusion Engine initialized (α=0.5)
Loading FAISS index...
✓ FAISS index loaded: 150 products
Initializing Product Catalog for advanced recommendations...
✓ Product Catalog loaded: 150 products
  - Categories: 8
  - Indexed: 150
==================================================
Server ready! 🚀
Endpoints:
  /api/v1/search - FAISS-based search
  /api/v1/recommend - Standard web-based recommendation
  /api/v1/recommend/advanced - Advanced multi-stage recommendation
API Docs: http://localhost:8001/docs
==================================================
```

### 4. Frontend Setup (Optional)

```bash
cd frontend
npm install
npm run dev
```

Access at: `http://localhost:3000`

## Usage

### Option 1: Using cURL

#### Text-Only Query
```bash
curl -X POST "http://localhost:8001/api/v1/recommend/advanced" \
  -F "text_query=blue casual denim jacket for men" \
  -F "top_k=10" \
  -F "alpha=0.6" \
  -F "use_product_index=true" \
  -F "apply_filters=true"
```

#### Image-Only Query
```bash
curl -X POST "http://localhost:8001/api/v1/recommend/advanced" \
  -F "image=@path/to/jacket.jpg" \
  -F "top_k=10" \
  -F "alpha=0.6" \
  -F "use_product_index=true"
```

#### Hybrid Query (Image + Text)
```bash
curl -X POST "http://localhost:8001/api/v1/recommend/advanced" \
  -F "text_query=similar blue jacket" \
  -F "image=@path/to/jacket.jpg" \
  -F "top_k=10" \
  -F "alpha=0.6" \
  -F "use_product_index=true"
```

### Option 2: Using Python

```python
import requests

url = "http://localhost:8001/api/v1/recommend/advanced"

# Text-only query
response = requests.post(url, data={
    "text_query": "blue casual denim jacket for men",
    "top_k": 10,
    "alpha": 0.6,
    "use_product_index": True,
    "apply_filters": True
})

results = response.json()
print(f"Found {results['total_results']} products in {results['query_time']}s")

for product in results['results']:
    print(f"{product['rank']}. {product['title']}")
    print(f"   Scores: visual={product['visual_score']:.2f}, "
          f"text={product['text_score']:.2f}, "
          f"final={product['final_score']:.2f}")
```

### Option 3: Using Swagger UI

1. Navigate to `http://localhost:8001/docs`
2. Find `/api/v1/recommend/advanced` endpoint
3. Click "Try it out"
4. Fill in parameters:
   - `text_query`: "blue casual denim jacket for men"
   - `top_k`: 10
   - `alpha`: 0.6
   - `use_product_index`: true
   - `apply_filters`: true
5. Click "Execute"

## API Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `text_query` | string | None | Text description of fashion item |
| `image` | file | None | Fashion image to search from |
| `top_k` | int | 10 | Number of recommendations (1-20) |
| `alpha` | float | 0.6 | Image weight (0=text-only, 1=image-only) |
| `use_product_index` | bool | true | Use FAISS product index |
| `apply_filters` | bool | true | Apply quality filters |

**Note:** At least one of `text_query` or `image` must be provided.

## Response Format

```json
{
  "results": [
    {
      "id": 123,
      "title": "Men Blue Denim Jacket",
      "description": "Casual denim jacket...",
      "category": "jacket",
      "color": "blue",
      "price": 2499,
      "rating": 4.5,
      "brand": "Levi's",
      "image_url": "http://localhost:8001/images/product_123.jpg",
      
      // Ranking scores
      "visual_score": 0.94,
      "text_score": 0.87,
      "attribute_score": 0.90,
      "business_score": 0.75,
      "final_score": 0.89,
      "rank": 1
    }
  ],
  
  // Metadata
  "total_results": 10,
  "query_time": 2.34,
  
  // Query understanding
  "search_phrase": "blue casual denim jacket men",
  "expanded_query": "blue casual denim jacket coat outerwear men",
  "query_attributes": {
    "colors": ["blue"],
    "categories": ["jacket", "denim"],
    "occasions": ["casual"],
    "genders": ["men"]
  },
  
  // Configuration
  "alpha_used": 0.6,
  "search_type": "hybrid",
  "model_used": "ViT-L/14",
  
  // Candidate sources
  "total_candidates": 150,
  "indexed_candidates": 120,
  
  // Performance breakdown
  "pipeline_stages": {
    "input_processing": 0.02,
    "feature_extraction": 0.45,
    "fusion": 0.01,
    "query_understanding": 0.08,
    "candidate_generation": 0.67,
    "image_download": 0.89,
    "multi_stage_ranking": 0.18,
    "filtering": 0.04
  }
}
```

## Example Queries

### 1. Formal Wear
```bash
curl -X POST "http://localhost:8001/api/v1/recommend/advanced" \
  -F "text_query=black formal blazer for women office wear" \
  -F "top_k=10"
```

**Extracted attributes:**
- Color: black
- Category: blazer
- Gender: women
- Occasion: formal, office

### 2. Traditional Indian Wear
```bash
curl -X POST "http://localhost:8001/api/v1/recommend/advanced" \
  -F "text_query=red floral printed kurta for women" \
  -F "top_k=10"
```

**Extracted attributes:**
- Color: red
- Pattern: floral, printed
- Category: kurta
- Gender: women

### 3. Casual Streetwear
```bash
curl -X POST "http://localhost:8001/api/v1/recommend/advanced" \
  -F "text_query=oversized graphic tshirt men streetwear" \
  -F "top_k=10"
```

**Extracted attributes:**
- Style: oversized
- Pattern: graphic
- Category: tshirt
- Gender: men
- Occasion: casual

### 4. Image-Based Search
Upload an image of a dress and get similar recommendations:

```python
import requests

with open('my_dress.jpg', 'rb') as f:
    response = requests.post(
        'http://localhost:8001/api/v1/recommend/advanced',
        files={'image': f},
        data={'top_k': 10, 'alpha': 0.8}  # 80% image weight
    )
```

## Performance Tuning

### 1. Adjust Image Weight (α)

- **α = 0.0**: Pure text search (faster)
- **α = 0.6**: Balanced (recommended)
- **α = 1.0**: Pure image search (best for visual similarity)

Example for visual-first search:
```bash
curl -X POST "http://localhost:8001/api/v1/recommend/advanced" \
  -F "text_query=blue jacket" \
  -F "image=@jacket.jpg" \
  -F "alpha=0.8"  # 80% image, 20% text
```

### 2. Disable Product Index (Web-Only)

For real-time inventory without building index:
```bash
curl -X POST "http://localhost:8001/api/v1/recommend/advanced" \
  -F "text_query=blue jacket" \
  -F "use_product_index=false"
```

### 3. Disable Filters (Faster, More Results)

```bash
curl -X POST "http://localhost:8001/api/v1/recommend/advanced" \
  -F "text_query=blue jacket" \
  -F "apply_filters=false"
```

## Troubleshooting

### Issue: "CLIP ViT-L/14 model is not loaded"

**Solution:** Server is still loading. Wait 30-60 seconds after startup.

### Issue: "No products in catalog index"

**Solution:** Run the index build script:
```bash
python -m backend.scripts.build_product_index
```

### Issue: "All candidate images failed to download"

**Possible causes:**
- No internet connection
- Web search provider rate-limited
- Invalid image URLs

**Solution:** 
- Check internet connection
- Try again after a few minutes
- Use product index: `use_product_index=true`

### Issue: Slow response times (>5 seconds)

**Solutions:**
1. Reduce `top_k` (fewer results = faster)
2. Disable filters: `apply_filters=false`
3. Use web search only: `use_product_index=false`
4. Use GPU if available
5. Reduce concurrent downloads in `settings.py`:
   ```python
   MAX_CONCURRENT_DOWNLOADS: int = 5  # Default: 10
   ```

### Issue: Out of memory

**Solutions:**
1. Close other applications
2. Use smaller CLIP model (ViT-B/32 instead of ViT-L/14)
3. Reduce batch size in ranking
4. Process fewer candidates

## Advanced Features

### Query Understanding

The system automatically extracts:
- **Colors**: blue, red, black, navy, etc.
- **Categories**: jacket, shirt, dress, shoes, etc.
- **Patterns**: floral, striped, solid, etc.
- **Gender**: men, women, unisex, kids
- **Occasions**: casual, formal, party, wedding, etc.
- **Styles**: slim fit, oversized, vintage, etc.

These attributes are used for:
1. Filtering candidates from product index
2. Boosting scores in attribute matching stage
3. Improving result relevance

### Multi-Stage Ranking

Each product receives 4 separate scores:

1. **Visual Score (55%)**: CLIP embedding similarity
2. **Text Score (25%)**: Title/description matching
3. **Attribute Score (10%)**: Fashion attribute matching
4. **Business Score (10%)**: Popularity, ratings, price, brand

Final score is weighted combination.

### Recommendation Filtering

Automatically removes:
- Duplicate products (similar titles)
- Low-quality results (short titles, spam)
- Non-fashion items
- Invalid images

Ensures diversity:
- Max 5 products per source website
- Balanced across categories

## Comparison: Standard vs Advanced

### Standard Endpoint (`/api/v1/recommend`)

```bash
curl -X POST "http://localhost:8001/api/v1/recommend" \
  -F "text_query=blue jacket" \
  -F "top_k=10"
```

**Features:**
- ✅ CLIP embeddings
- ✅ Web search
- ✅ Simple cosine similarity ranking
- ❌ No query understanding
- ❌ No product index
- ❌ No multi-stage ranking
- ❌ No filtering

**Use case:** Quick, simple recommendations

### Advanced Endpoint (`/api/v1/recommend/advanced`)

```bash
curl -X POST "http://localhost:8001/api/v1/recommend/advanced" \
  -F "text_query=blue jacket" \
  -F "top_k=10"
```

**Features:**
- ✅ CLIP embeddings
- ✅ Web search
- ✅ Query understanding with attribute extraction
- ✅ Product index candidate generation
- ✅ Multi-stage ranking (4 signals)
- ✅ Quality filtering and deduplication
- ✅ Detailed score explanations

**Use case:** Production-quality recommendations

## Next Steps

1. **See detailed architecture:** Read `docs/ADVANCED_ARCHITECTURE.md`

2. **Customize ranking weights:** Edit `backend/app/services/multi_stage_ranking.py`:
   ```python
   MultiStageRankingEngine(
       visual_weight=0.55,    # Adjust these
       text_weight=0.25,
       attribute_weight=0.10,
       business_weight=0.10,
   )
   ```

3. **Add more products:** Add to `data/products.json` and rebuild index

4. **Extend query understanding:** Add vocabulary in `backend/app/services/query_understanding.py`

5. **Deploy to production:** See deployment guide

## Resources

- **API Documentation**: http://localhost:8001/docs
- **Architecture Guide**: docs/ADVANCED_ARCHITECTURE.md
- **CLIP Paper**: https://arxiv.org/abs/2103.00020
- **FAISS Documentation**: https://github.com/facebookresearch/faiss

## Support

For issues or questions:
- Check server logs: Look for ERROR or WARNING messages
- Test with Swagger UI: http://localhost:8001/docs
- Verify index exists: `ls index/products.index`
- Check product count: Look at startup logs

---

**Happy Recommending! 🚀**
