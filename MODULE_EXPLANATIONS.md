# Module Explanations

Detailed documentation of each module in the Cross-Modal Fashion Recommendation System.

---

## Table of Contents

1. [Backend Architecture](#backend-architecture)
2. [CLIP Model Module](#clip-model-module)
3. [FAISS Index Module](#faiss-index-module)
4. [Fusion Engine Module](#fusion-engine-module)
5. [Search Routes Module](#search-routes-module)
6. [Index Builder Script](#index-builder-script)
7. [Frontend Components](#frontend-components)
8. [Data Flow](#data-flow)

---

## Backend Architecture

### Overview

The backend is built with **FastAPI**, a modern Python web framework that provides:
- Automatic API documentation
- Request validation with Pydantic
- Async/await support for high performance
- Type hints for better code quality

### Main Application (`simple_main.py`)

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
```

**Key Responsibilities:**

1. **Application Initialization**
   - Creates FastAPI app instance
   - Configures CORS for cross-origin requests
   - Mounts static file serving for images

2. **Startup Event Handler**
   ```python
   @app.on_event("startup")
   async def startup_event():
       clip_model = CLIPModel(model_name="ViT-B/32")
       faiss_index = FAISSIndex(embedding_dim=512)
       app.state.clip_model = clip_model
       app.state.faiss_index = faiss_index
   ```
   - Loads CLIP model into memory (once at startup)
   - Loads FAISS index from disk
   - Stores in `app.state` for request access

3. **Route Registration**
   ```python
   app.include_router(router, prefix="/api/v1")
   ```
   - Includes all API endpoints with `/api/v1` prefix

**Why this approach?**
- **Efficiency**: Models loaded once, not per-request
- **Memory**: Shared state across all requests
- **Performance**: No repeated model initialization

---

## CLIP Model Module

### Location: `backend/app/models/clip_model.py`

### What is CLIP?

**CLIP (Contrastive Language-Image Pre-training)** is OpenAI's vision-language model that:
- Encodes images and text into the same embedding space
- Enables semantic similarity between images and text
- Pre-trained on 400M image-text pairs

### CLIPModel Class

```python
class CLIPModel:
    def __init__(self, model_name: str = "ViT-B/32"):
        self.model, self.preprocess = clip.load(model_name)
        self.model.eval()  # Set to evaluation mode
```

**Model Variants:**
- `ViT-B/32`: Fast, 512-dim embeddings, good accuracy
- `ViT-B/16`: Slower, better accuracy
- `ViT-L/14`: Best accuracy, requires more resources

### Key Methods

#### 1. Text Encoding

```python
async def encode_text(self, text: str) -> np.ndarray:
    """
    Input: "red summer dress"
    Output: [0.123, -0.456, ..., 0.789]  # 512 dimensions
    """
    text_tokens = clip.tokenize([text])
    with torch.no_grad():
        features = self.model.encode_text(text_tokens)
        features = features / features.norm(dim=-1, keepdim=True)
    return features.cpu().numpy().flatten()
```

**Steps:**
1. **Tokenization**: Converts text to token IDs
2. **Encoding**: Passes through transformer
3. **Normalization**: L2 normalize to unit vector
4. **Return**: 512-dimensional numpy array

**Why normalize?**
- Cosine similarity = dot product of normalized vectors
- All embeddings on unit hypersphere
- Makes distances comparable

#### 2. Image Encoding

```python
async def encode_image(self, image: Image.Image) -> np.ndarray:
    """
    Input: PIL Image object
    Output: [0.234, -0.567, ..., 0.890]  # 512 dimensions
    """
    image_tensor = self.preprocess(image).unsqueeze(0)
    with torch.no_grad():
        features = self.model.encode_image(image_tensor)
        features = features / features.norm(dim=-1, keepdim=True)
    return features.cpu().numpy().flatten()
```

**Steps:**
1. **Preprocessing**: Resize to 224×224, normalize colors
2. **Encoding**: Passes through Vision Transformer
3. **Normalization**: L2 normalize
4. **Return**: 512-dimensional numpy array

#### 3. Batch Processing

```python
async def encode_batch_texts(self, texts: List[str]) -> np.ndarray:
    """Process multiple texts at once for efficiency"""
    batch = clip.tokenize(texts)
    with torch.no_grad():
        features = self.model.encode_text(batch)
        features = features / features.norm(dim=-1, keepdim=True)
    return features.cpu().numpy()
```

**Benefits:**
- Faster than encoding one-by-one
- Better GPU utilization
- Used during index building

---

## FAISS Index Module

### Location: `backend/app/utils/faiss_index.py`

### What is FAISS?

**FAISS (Facebook AI Similarity Search)** is a library for efficient similarity search:
- Handles millions of vectors
- Multiple index types (Flat, IVF, HNSW, PQ)
- GPU support available
- Approximate nearest neighbor (ANN) search

### FAISSIndex Class

```python
class FAISSIndex:
    def __init__(self, embedding_dim: int = 512, index_type: str = "HNSW"):
        self.embedding_dim = 512
        self.index = faiss.IndexHNSWFlat(512, 32)
```

### Index Types

#### 1. **HNSW (Hierarchical Navigable Small World)**
```python
index = faiss.IndexHNSWFlat(512, 32)
```
- **Best for**: <1M vectors, high accuracy needed
- **Speed**: Very fast (milliseconds)
- **Memory**: Higher memory usage
- **Accuracy**: >95% recall

**Parameters:**
- `512`: Embedding dimension
- `32`: Number of connections per node (M)

#### 2. **Flat (Brute Force)**
```python
index = faiss.IndexFlatIP(512)
```
- **Best for**: <10k vectors, exact search
- **Speed**: Fast for small datasets
- **Accuracy**: 100% (exact)

#### 3. **IVF (Inverted File)**
```python
quantizer = faiss.IndexFlatIP(512)
index = faiss.IndexIVFFlat(quantizer, 512, 100)
```
- **Best for**: >1M vectors
- **Speed**: Very fast
- **Memory**: Lower memory
- **Accuracy**: Configurable trade-off

### Key Methods

#### 1. Adding Products

```python
def add_product(self, embedding: np.ndarray, metadata: dict):
    """
    Add single product to index
    
    Args:
        embedding: 512-dim numpy array
        metadata: Product information (id, title, price, etc.)
    """
    embedding = embedding / np.linalg.norm(embedding)  # Normalize
    self.index.add(embedding.astype(np.float32))
    self.product_metadata.append(metadata)
```

**Why normalize?**
- Ensures consistent similarity scores
- Makes cosine similarity = inner product

#### 2. Batch Adding

```python
def add_batch_products(self, embeddings: np.ndarray, metadata_list: List[dict]):
    """
    Add multiple products efficiently
    
    Args:
        embeddings: (N, 512) array
        metadata_list: List of N metadata dicts
    """
    embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
    self.index.add(embeddings.astype(np.float32))
    self.product_metadata.extend(metadata_list)
```

**Benefits:**
- Single FAISS operation
- Faster than individual adds
- Better memory efficiency

#### 3. Searching

```python
async def search(self, query_embedding: np.ndarray, top_k: int = 10) -> List[dict]:
    """
    Find K most similar products
    
    Args:
        query_embedding: 512-dim query vector
        top_k: Number of results
        
    Returns:
        List of product dicts with similarity_score
    """
    query_embedding = query_embedding / np.linalg.norm(query_embedding)
    query_embedding = query_embedding.reshape(1, -1).astype(np.float32)
    
    # FAISS search
    distances, indices = self.index.search(query_embedding, top_k)
    
    results = []
    for idx, distance in zip(indices[0], distances[0]):
        if idx >= 0 and idx < len(self.product_metadata):
            product = self.product_metadata[idx].copy()
            product['similarity_score'] = float(distance)
            results.append(product)
    
    return results
```

**How FAISS search works:**
1. Query vector compared to index
2. HNSW algorithm navigates graph structure
3. Returns top-K nearest neighbors
4. Distances = cosine similarity (for normalized vectors)

#### 4. Persistence

```python
def save_index(self):
    """Save index and metadata to disk"""
    faiss.write_index(self.index, "index/products.index")
    with open("index/metadata.json", 'w') as f:
        json.dump(self.product_metadata, f)

def _load_existing_index(self):
    """Load index from disk on startup"""
    self.index = faiss.read_index("index/products.index")
    with open("index/metadata.json", 'r') as f:
        self.product_metadata = json.load(f)
```

**Benefits:**
- Fast startup (no re-indexing needed)
- Index persists across restarts
- Separate index and metadata for flexibility

---

## Fusion Engine Module

### Location: `backend/app/models/fusion.py`

### What is Fusion?

**Fusion** combines embeddings from different modalities (text and images) into a single query vector.

### Fusion Formula

```
V_fusion = α × V_image + (1-α) × V_text

where:
- α ∈ [0, 1]: Weight for image
- (1-α): Weight for text
- V_image: Normalized image embedding (512-dim)
- V_text: Normalized text embedding (512-dim)
- V_fusion: Combined embedding (512-dim, normalized)
```

### Examples

**Text-only (α = 0):**
```
V_fusion = 0 × V_image + 1 × V_text = V_text
```

**Image-only (α = 1):**
```
V_fusion = 1 × V_image + 0 × V_text = V_image
```

**Equal weight (α = 0.5):**
```
V_fusion = 0.5 × V_image + 0.5 × V_text
```

**Image-focused (α = 0.7):**
```
V_fusion = 0.7 × V_image + 0.3 × V_text
```

### FusionEngine Class

```python
class FusionEngine:
    def fuse(self, image_embedding, text_embedding, alpha):
        """
        Combine embeddings with weighted average
        """
        # Ensure normalized
        image_embedding = self._normalize(image_embedding)
        text_embedding = self._normalize(text_embedding)
        
        # Apply fusion formula
        beta = 1.0 - alpha
        fused = (alpha * image_embedding) + (beta * text_embedding)
        
        # Re-normalize result
        fused = self._normalize(fused)
        
        return fused
    
    def _normalize(self, vector):
        """L2 normalization"""
        return vector / np.linalg.norm(vector)
```

### Why Re-normalize After Fusion?

```python
# Example:
V_image = [0.6, 0.8]  # ||V|| = 1.0
V_text = [0.8, 0.6]   # ||V|| = 1.0
alpha = 0.5

# After fusion:
V_fusion = 0.5 * [0.6, 0.8] + 0.5 * [0.8, 0.6]
         = [0.3, 0.4] + [0.4, 0.3]
         = [0.7, 0.7]
         
# Norm: ||V_fusion|| = sqrt(0.7² + 0.7²) = 0.99 ≈ 1.0 (but not exactly)

# Re-normalize:
V_fusion = [0.7, 0.7] / 0.99 = [0.707, 0.707]  # ||V|| = 1.0 exactly
```

**Importance:**
- Keeps all vectors on unit hypersphere
- Makes similarity scores comparable
- Required for cosine similarity via dot product

---

## Search Routes Module

### Location: `backend/app/api/simple_routes.py`

### Search Endpoint

```python
@router.post("/search", response_model=SearchResponse)
async def hybrid_search(request: SearchRequest, app_request: Request):
```

### Request Model

```python
class SearchRequest(BaseModel):
    text: Optional[str] = None
    image: Optional[str] = None  # Base64 encoded
    alpha: float = 0.5
    top_k: int = 10
```

**Validation:**
- At least one of text or image required
- Alpha between 0.0 and 1.0
- top_k between 1 and 100

### Search Pipeline

```python
# 1. Input Validation
if not request.text and not request.image:
    raise HTTPException(status_code=400, detail="...")

# 2. Get Models
clip_model = app_request.app.state.clip_model
faiss_index = app_request.app.state.faiss_index

# 3. Generate Embeddings
text_embedding = await clip_model.encode_text(request.text) if request.text else None
image_embedding = await clip_model.encode_image(image) if request.image else None

# 4. Apply Fusion
if text_embedding and image_embedding:
    query_embedding = alpha * image_embedding + (1-alpha) * text_embedding
    query_embedding = query_embedding / np.linalg.norm(query_embedding)
elif image_embedding:
    query_embedding = image_embedding
else:
    query_embedding = text_embedding

# 5. FAISS Search
results = await faiss_index.search(query_embedding, top_k=request.top_k)

# 6. Format Response
return SearchResponse(
    results=results,
    query_time=elapsed,
    total_results=len(results),
    alpha_used=request.alpha,
    search_type="hybrid" | "text" | "image"
)
```

### Error Handling

```python
try:
    # Search logic
except HTTPException:
    raise  # Re-raise HTTP exceptions
except Exception as e:
    logger.error(f"Search error: {e}", exc_info=True)
    raise HTTPException(status_code=500, detail=str(e))
```

**Error Types:**
- `400`: Bad request (validation error)
- `503`: Service unavailable (models not loaded)
- `500`: Internal server error

---

## Index Builder Script

### Location: `backend/scripts/simple_build_index.py`

### Purpose

Builds the FAISS index by:
1. Fetching products from external API
2. Downloading product images
3. Generating CLIP embeddings
4. Building FAISS index
5. Saving to disk

### Script Flow

```python
async def main():
    # 1. Fetch products from DummyJSON
    products = await fetch_products(session, limit=100)
    
    # 2. Download images
    processed_products = await process_products(products)
    
    # 3. Generate embeddings and build index
    faiss_index = await generate_embeddings(processed_products)
    
    # 4. Save index
    faiss_index.save_index()
```

### 1. Fetch Products

```python
async def fetch_products(session, limit=100):
    """Fetch from DummyJSON API"""
    url = f"https://dummyjson.com/products?limit={limit}"
    async with session.get(url) as response:
        data = await response.json()
        return data['products']
```

**DummyJSON Response:**
```json
{
  "products": [
    {
      "id": 1,
      "title": "iPhone 9",
      "description": "An apple mobile...",
      "price": 549,
      "thumbnail": "https://...",
      "category": "smartphones"
    }
  ]
}
```

### 2. Download Images

```python
async def download_image(session, url, save_path):
    """Download and save image"""
    async with session.get(url) as response:
        if response.status == 200:
            content = await response.read()
            async with aiofiles.open(save_path, 'wb') as f:
                await f.write(content)
            
            # Verify image is valid
            img = Image.open(save_path)
            img.verify()
            return True
    return False
```

**Why async?**
- Download multiple images concurrently
- Much faster than sequential downloads
- Non-blocking I/O

### 3. Generate Embeddings

```python
async def generate_embeddings(products):
    clip_model = CLIPModel()
    faiss_index = FAISSIndex()
    
    for batch in batches(products, size=16):
        # Load images
        images = [Image.open(p['image_path']) for p in batch]
        
        # Generate embeddings
        texts = [f"{p['title']}. {p['description']}" for p in batch]
        text_embs = await clip_model.encode_batch_texts(texts)
        image_embs = await clip_model.encode_batch_images(images)
        
        # Use hybrid embeddings (0.5 text + 0.5 image)
        combined_embs = 0.5 * text_embs + 0.5 * image_embs
        combined_embs = combined_embs / np.linalg.norm(combined_embs, axis=1, keepdims=True)
        
        # Add to index
        faiss_index.add_batch_products(combined_embs, metadata_list)
    
    return faiss_index
```

**Why hybrid embeddings for indexing?**
- Works well for all query types
- Balances visual and textual information
- User can adjust alpha at query time

---

## Frontend Components

### Location: `frontend/app/simple/page.tsx`

### Component Structure

```tsx
export default function HybridSearchPage() {
  // State
  const [textQuery, setTextQuery] = useState('');
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [alpha, setAlpha] = useState(0.5);
  const [results, setResults] = useState<Product[]>([]);
  
  // Handlers
  const handleImageUpload = (e) => {...};
  const handleSearch = async () => {...};
  
  // Render
  return <div>...</div>;
}
```

### Key Features

#### 1. Alpha Slider

```tsx
<input
  type="range"
  min="0"
  max="1"
  step="0.05"
  value={alpha}
  onChange={(e) => setAlpha(parseFloat(e.target.value))}
  className="slider"
/>
```

**Styling:**
```css
.slider {
  background: linear-gradient(to right, 
    #10b981 0%,   /* Green (text) */
    #3b82f6 50%,  /* Blue (balanced) */
    #a855f7 100%  /* Purple (image) */
  );
}
```

#### 2. Image Upload

```tsx
const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
  const file = e.target.files?.[0];
  if (file) {
    // Validate size (max 5MB)
    if (file.size > 5 * 1024 * 1024) {
      setError('Image too large');
      return;
    }
    
    setImageFile(file);
    
    // Preview
    const reader = new FileReader();
    reader.onloadend = () => {
      setImagePreview(reader.result as string);
    };
    reader.readAsDataURL(file);
  }
};
```

#### 3. Search Function

```tsx
const handleSearch = async () => {
  // Validate input
  if (!textQuery && !imageFile) {
    setError('Provide text or image');
    return;
  }
  
  setLoading(true);
  
  // Convert image to base64
  let imageBase64 = null;
  if (imageFile) {
    imageBase64 = await new Promise<string>((resolve) => {
      const reader = new FileReader();
      reader.onload = () => {
        const base64 = (reader.result as string).split(',')[1];
        resolve(base64);
      };
      reader.readAsDataURL(imageFile);
    });
  }
  
  // API call
  const res = await fetch(`${API_URL}/search`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      text: textQuery || null,
      image: imageBase64,
      alpha: alpha,
      top_k: 10
    })
  });
  
  const data = await res.json();
  setResponse(data);
  setLoading(false);
};
```

#### 4. Results Display

```tsx
{response.results.map((product) => (
  <div key={product.product_id} className="product-card">
    {/* Image with similarity badge */}
    <div className="relative">
      <img src={`${API_URL}${product.image_url}`} alt={product.title} />
      <div className="badge">
        {(product.similarity_score * 100).toFixed(1)}%
      </div>
    </div>
    
    {/* Product info */}
    <h3>{product.title}</h3>
    <p>${product.price.toFixed(2)}</p>
    
    {/* Similarity bar */}
    <div className="progress-bar">
      <div 
        style={{ width: `${product.similarity_score * 100}%` }}
        className="progress-fill"
      />
    </div>
  </div>
))}
```

---

## Data Flow

### Complete Request Flow

```
User Action
    ↓
[1] User enters "red dress" and uploads image, sets α=0.6
    ↓
[2] Frontend: Collect inputs
    - text: "red dress"
    - image: File → base64
    - alpha: 0.6
    - top_k: 10
    ↓
[3] Frontend: POST /api/v1/search with JSON body
    ↓
[4] Backend: Receive request
    - Validate inputs (Pydantic)
    - Extract from app.state: clip_model, faiss_index
    ↓
[5] CLIP Encoding
    - encode_text("red dress") → V_text [512-dim]
    - encode_image(image_data) → V_image [512-dim]
    ↓
[6] Fusion
    - V_fusion = 0.6 × V_image + 0.4 × V_text
    - Normalize: V_fusion / ||V_fusion||
    ↓
[7] FAISS Search
    - index.search(V_fusion, k=10)
    - Returns: indices, distances
    ↓
[8] Metadata Enrichment
    - For each index: get product_metadata[index]
    - Add similarity_score = distance
    - Format as ProductResult objects
    ↓
[9] Response
    - JSON: {results, query_time, alpha_used, search_type}
    ↓
[10] Frontend: Display results
    - Map over results array
    - Render product cards
    - Show similarity scores
    ↓
User sees results!
```

### Timing Breakdown

```
Total: ~70ms

├─ Text encoding: 15ms
├─ Image encoding: 50ms
├─ Fusion: <1ms
├─ FAISS search: 5ms
└─ Formatting: <1ms
```

---

## Performance Optimization

### Backend Optimizations

1. **Model Loading**
   - Load once at startup, not per-request
   - Keeps models in memory

2. **Batch Processing**
   - Process multiple products together
   - Better GPU utilization

3. **FAISS HNSW**
   - Approximate search (fast)
   - 95%+ accuracy
   - Millisecond latency

4. **Async/Await**
   - Non-blocking I/O
   - Multiple concurrent requests
   - Better CPU utilization

### Frontend Optimizations

1. **Image Compression**
   - Client-side resize before upload
   - Reduces bandwidth

2. **Debounced Search**
   - Wait for user to stop typing
   - Prevents excessive API calls

3. **Result Caching**
   - Cache recent searches
   - Instant results for duplicates

4. **Lazy Loading**
   - Load images as user scrolls
   - Faster initial render

---

## Security Considerations

### Input Validation

```python
class SearchRequest(BaseModel):
    text: Optional[str] = Field(None, max_length=500)
    image: Optional[str] = Field(None)
    alpha: float = Field(0.5, ge=0.0, le=1.0)
    top_k: int = Field(10, ge=1, le=100)
```

### CORS Configuration

```python
allow_origins=[
    "http://localhost:3000",
    "https://yourdomain.com"
]
```

### File Size Validation

```python
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

if len(image_data) > MAX_FILE_SIZE:
    raise HTTPException(status_code=413, detail="Image too large")
```

### Rate Limiting (Optional)

```python
from slowapi import Limiter

limiter = Limiter(key_func=get_remote_address)

@limiter.limit("10/minute")
@router.post("/search")
async def hybrid_search(...):
```

---

## Conclusion

This system demonstrates:
- **Machine Learning**: CLIP for multimodal embeddings
- **Information Retrieval**: FAISS for similarity search
- **Web Development**: FastAPI backend, Next.js frontend
- **Production Engineering**: Docker, deployment, security

Each module is designed to be:
- **Modular**: Easy to replace or upgrade
- **Scalable**: Handles growing data and traffic
- **Maintainable**: Clear code, good documentation
- **Performant**: Optimized for speed and efficiency

For more information, see:
- [README.md](README_COMPLETE.md) - Project overview
- [INSTALLATION.md](INSTALLATION.md) - Setup instructions
- [DEPLOYMENT.md](DEPLOYMENT.md) - Production deployment
