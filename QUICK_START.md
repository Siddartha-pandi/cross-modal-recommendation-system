# Quick Start Guide

Get the Cross-Modal Fashion Recommendation System running in **5 minutes**!

---

## Prerequisites

- Python 3.9+
- Node.js 18+
- 4GB+ RAM free

---

## Option 1: Local Development (Recommended for First Time)

### Step 1: Clone Repository

```bash
git clone <repository-url>
cd cross-modal-recommendation-system
```

### Step 2: Backend Setup (Terminal 1)

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (macOS/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Build product index (5-10 minutes)
python scripts/simple_build_index.py

# Start server
python simple_main.py
```

**Backend ready at:** http://localhost:8000

### Step 3: Frontend Setup (Terminal 2)

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

**Frontend ready at:** http://localhost:3000

### Step 4: Try It Out!

1. Open http://localhost:3000/simple
2. Enter a search query: "red dress"
3. Or upload an image
4. Adjust the alpha slider
5. Click "Search Products"

---

## Option 2: Docker Deployment

### Prerequisites
- Docker 20+
- Docker Compose 2+

### Step 1: Build Index First

```bash
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
python scripts/simple_build_index.py
cd ..
```

### Step 2: Build and Run with Docker

```bash
# Build images
docker-compose -f docker-compose.simple.yml build

# Start services
docker-compose -f docker-compose.simple.yml up -d

# Check status
docker-compose -f docker-compose.simple.yml ps

# View logs
docker-compose -f docker-compose.simple.yml logs -f
```

### Step 3: Access Application

- Frontend: http://localhost:3000/simple
- Backend API: http://localhost:8000/docs
- Health Check: http://localhost:8000/api/v1/health

### Stop Services

```bash
docker-compose -f docker-compose.simple.yml down
```

---

## Testing the System

### 1. Check Backend Health

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

### 2. Test Text Search

```bash
curl -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{
    "text": "laptop",
    "alpha": 0.0,
    "top_k": 5
  }'
```

### 3. Test via Web Interface

1. Go to http://localhost:3000/simple
2. Try these searches:
   - Text: "smartphone"
   - Text: "summer dress"
   - Text: "running shoes"
3. Upload a product image
4. Try hybrid search with both text and image

---

## Sample Queries to Try

### Text Queries
- "red summer dress"
- "leather shoes"
- "laptop computer"
- "smartphone"
- "blue jeans"
- "winter jacket"

### Alpha Settings
- **0.0**: Pure text search
- **0.5**: Balanced (recommended for hybrid)
- **1.0**: Pure image search

### Hybrid Search Tips
- Use text to specify color/style: "elegant black dress"
- Use image to specify visual details
- Adjust alpha to control which matters more

---

## Project Structure

```
cross-modal-recommendation-system/
├── backend/
│   ├── simple_main.py          # Main server
│   ├── app/
│   │   ├── api/
│   │   │   └── simple_routes.py   # Search endpoint
│   │   ├── models/
│   │   │   ├── clip_model.py     # CLIP wrapper
│   │   │   └── fusion.py         # Fusion logic
│   │   └── utils/
│   │       └── faiss_index.py    # FAISS manager
│   └── scripts/
│       └── simple_build_index.py # Index builder
├── frontend/
│   └── app/
│       └── simple/
│           └── page.tsx          # Search UI
├── data/
│   ├── products.json            # Product metadata
│   └── images/                  # Product images
└── index/
    ├── products.index          # FAISS index
    └── metadata.json           # Index metadata
```

---

## Common Issues & Solutions

### Issue: "Models not loaded"

**Cause**: Backend still loading CLIP model

**Solution**: Wait 30-60 seconds after starting backend

### Issue: "No products in index"

**Cause**: Index not built

**Solution**: 
```bash
cd backend
python scripts/simple_build_index.py
```

### Issue: Out of memory during index build

**Solution**: Reduce batch size in `simple_build_index.py`:
```python
batch_size = 8  # Change from 16 to 8
```

### Issue: Images not loading

**Solution**: 
1. Check backend is running: http://localhost:8000
2. Verify images exist: `ls backend/data/images/`
3. Check browser console for errors

### Issue: Slow search

**Cause**: CPU encoding, no GPU

**Solution**: Normal for CPU. Consider:
- Using smaller FAISS index
- Deploying to GPU instance
- Caching frequent queries

---

## What's Next?

After getting it running:

1. **Read Documentation**
   - [README_COMPLETE.md](README_COMPLETE.md) - Full overview
   - [MODULE_EXPLANATIONS.md](MODULE_EXPLANATIONS.md) - How it works
   - [DEPLOYMENT.md](DEPLOYMENT.md) - Production deployment

2. **Experiment**
   - Try different alpha values
   - Upload different images
   - Check API docs: http://localhost:8000/docs

3. **Customize**
   - Change to different e-commerce API
   - Adjust CLIP model variant
   - Modify fusion strategy

4. **Deploy**
   - Follow [DEPLOYMENT.md](DEPLOYMENT.md)
   - Deploy frontend to Vercel
   - Deploy backend to Render/AWS

---

## Performance Expectations

### Index Building
- **100 products**: ~5-10 minutes
- **1000 products**: ~30-60 minutes

### Search Performance
- **Text search**: ~15ms
- **Image search**: ~50ms
- **Hybrid search**: ~70ms

### Resource Usage
- **RAM**: ~2GB (backend)
- **Disk**: ~500MB (100 products)
- **CPU**: 2 cores recommended

---

## Getting Help

1. **Check logs**:
   ```bash
   # Backend logs
   # (see terminal output)
   
   # Docker logs
   docker-compose logs backend
   docker-compose logs frontend
   ```

2. **Check health endpoint**:
   ```bash
   curl http://localhost:8000/api/v1/health
   ```

3. **Review documentation**:
   - [INSTALLATION.md](INSTALLATION.md)
   - [MODULE_EXPLANATIONS.md](MODULE_EXPLANATIONS.md)

4. **API Documentation**:
   - http://localhost:8000/docs (interactive)
   - http://localhost:8000/redoc (reference)

---

## Success Checklist

- [ ] Backend running on port 8000
- [ ] Frontend running on port 3000
- [ ] Can access http://localhost:3000/simple
- [ ] Health check returns status "healthy"
- [ ] Text search returns results
- [ ] Image upload works
- [ ] Alpha slider adjustable
- [ ] Results display with similarity scores

---

**Congratulations! You have a working cross-modal fashion search system! 🎉**

Try searching for products and see the AI-powered similarity in action!
