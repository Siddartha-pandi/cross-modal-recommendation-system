# Installation Instructions

## Prerequisites

- **Python**: 3.9 or higher
- **Node.js**: 18.x or higher
- **npm** or **yarn**
- **Git**

## Backend Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd cross-modal-recommendation-system
```

### 2. Create Python Virtual Environment

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. Install Python Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

This will install:
- FastAPI (API framework)
- PyTorch (deep learning)
- CLIP (OpenAI's vision-language model)
- FAISS (similarity search)
- Pillow (image processing)
- And other dependencies

### 4. Build Product Index

The system needs to fetch products from an external API and build a FAISS index:

```bash
python scripts/simple_build_index.py
```

This script will:
1. Fetch products from DummyJSON API (https://dummyjson.com)
2. Download product images to `data/images/`
3. Generate CLIP embeddings for all products
4. Build FAISS index for similarity search
5. Save index to `index/` directory

**Note**: This may take 5-15 minutes depending on your hardware and internet speed.

### 5. Start Backend Server

```bash
# Development mode
python simple_main.py

# Or using uvicorn directly
uvicorn simple_main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/v1/health

## Frontend Setup

### 1. Navigate to Frontend Directory

```bash
cd frontend
```

### 2. Install Dependencies

```bash
npm install
# or
yarn install
```

### 3. Configure Environment Variables

Create a `.env.local` file in the `frontend/` directory:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

### 4. Start Frontend Development Server

```bash
npm run dev
# or
yarn dev
```

The frontend will be available at:
- http://localhost:3000

### 5. Access Simple Search Interface

Navigate to:
- http://localhost:3000/simple

## Verify Installation

### Backend Health Check

```bash
curl http://localhost:8000/api/v1/health
```

Expected response:
```json
{
  "status": "healthy",
  "clip_model_loaded": true,
  "faiss_index_loaded": true,
  "total_products": 100
}
```

### Test Search

```bash
curl -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{
    "text": "red dress",
    "alpha": 0.5,
    "top_k": 5
  }'
```

## Common Issues

### Issue: CLIP model download fails

**Solution**: The first time you run the backend, CLIP will download model weights (~350MB). Ensure you have:
- Stable internet connection
- At least 1GB free disk space

### Issue: Out of memory when building index

**Solution**: Reduce batch size in `simple_build_index.py`:
```python
batch_size = 8  # Reduce from 16
```

### Issue: Images not loading in frontend

**Solution**: Check that:
1. Backend is running on port 8000
2. Images are in `backend/data/images/`
3. CORS is properly configured

### Issue: Search returns no results

**Solution**: 
1. Verify index was built: Check `index/products.index` exists
2. Check index stats: `curl http://localhost:8000/api/v1/stats`

## Development Tips

### Hot Reload

- **Backend**: Use `--reload` flag with uvicorn
- **Frontend**: Next.js has hot reload by default

### Debugging

Enable debug logging in backend:
```python
# In simple_main.py
logging.basicConfig(level=logging.DEBUG)
```

### Running Tests

```bash
# Backend tests
cd backend
pytest

# Frontend type checking
cd frontend
npm run type-check
```

## Next Steps

After installation:
1. Try different search queries (text, image, hybrid)
2. Adjust alpha slider to see fusion effects
3. Review the [Deployment Guide](DEPLOYMENT.md) for production setup
4. Read [Module Explanations](MODULE_EXPLANATIONS.md) to understand the architecture

## Support

For issues or questions:
1. Check the [README](README.md)
2. Review API documentation at http://localhost:8000/docs
3. Check logs in console outputs
