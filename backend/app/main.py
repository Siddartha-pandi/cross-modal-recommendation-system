from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
import os
from app.api.routes import router
from app.models.clip_model import CLIPModel
from app.utils.faiss_index import FAISSIndex
from app.utils.ecommerce_fetchers import EcommerceFetcher
import logging
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Cross-Modal Product Recommendation API",
    description="CLIP-based product recommendation system with image and text search",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "http://localhost:5173",  # Vite dev server
        "http://frontend:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for product images
if os.path.exists("/app/data/images"):
    app.mount("/images", StaticFiles(directory="/app/data/images"), name="images")

# Include API routes
app.include_router(router, prefix="/api/v1")

# Global variables for models
clip_model = None
faiss_index = None

@app.on_event("startup")
async def startup_event():
    """Initialize models on startup"""
    global clip_model, faiss_index
    
    from app.utils.redis_cache import RedisCacheManager
    from app.services.search_service import initialize_search_service
    import numpy as np
    
    logger.info("Starting up application...")
    
    try:
        # Initialize CLIP model
        logger.info("Loading CLIP model...")
        clip_model = CLIPModel(model_name="ViT-B/32")
        app.state.clip_model = clip_model
        
        # Initialize FAISS index
        logger.info("Loading FAISS index...")
        faiss_index = FAISSIndex(embedding_dim=512, index_type="HNSW")
        app.state.faiss_index = faiss_index
        
        # Initialize Redis cache (optional, non-blocking)
        logger.info("Connecting to Redis cache...")
        try:
            cache = RedisCacheManager()
            if cache.is_available():
                app.state.cache = cache
                logger.info("Redis cache connected successfully")
            else:
                app.state.cache = None
                logger.warning("Redis not available - caching disabled")
        except Exception as e:
            logger.warning(f"Redis initialization failed: {e} - continuing without cache")
            app.state.cache = None
        
        # Fetch and index products from external e-commerce APIs
        logger.info("Fetching products from external e-commerce APIs...")
        ecommerce_fetcher = EcommerceFetcher()
        
        try:
            # Fetch fashion products from external APIs
            external_products = await ecommerce_fetcher.search_all(
                query="fashion clothing dress shirt shoes", 
                max_results_per_source=30
            )
            
            logger.info(f"fetched {len(external_products)} products from external APIs")
            
            # Generate embeddings for external products if we have any
            if external_products and len(external_products) > 0:
                logger.info(f"Generating embeddings for {len(external_products)} products...")
                
                embeddings_list = []
                metadata_list = []
                
                for idx, product in enumerate(external_products):
                    try:
                        # Generate embedding from product title and description
                        # Text will be automatically truncated in encode_text() to fit CLIP's context limit
                        text = f"{product.title}. {product.description}"
                        embedding = await clip_model.encode_text(text)
                        
                        # Normalize embedding
                        embedding = embedding / np.linalg.norm(embedding)
                        embeddings_list.append(embedding)
                        
                        # Store metadata
                        metadata_list.append({
                            'product_id': product.product_id,
                            'title': product.title,
                            'description': product.description,
                            'image_url': product.image_url,
                            'price': product.price,
                            'category': product.category,
                            'source': product.source,
                            'buy_url': product.buy_url,
                            'brand': product.brand,
                            'rating': product.rating
                        })
                        
                        if (idx + 1) % 10 == 0:
                            logger.info(f"Processed {idx + 1}/{len(external_products)} products")
                    
                    except Exception as e:
                        logger.warning(f"Failed to generate embedding for {product.title}: {e}")
                        continue
                
                # Add all embeddings to FAISS index
                if embeddings_list and metadata_list:
                    embeddings_array = np.stack(embeddings_list).astype(np.float32)
                    faiss_index.add_batch_products(embeddings_array, metadata_list)
                    logger.info(f"Added {len(metadata_list)} products with embeddings to FAISS index")
            
        except Exception as e:
            logger.error(f"Error fetching/indexing external products: {e}")
            logger.info("Continuing with existing FAISS index...")
        
        # Initialize search service
        logger.info("Initializing search service...")
        search_service = initialize_search_service(clip_model, faiss_index, cache)
        app.state.search_service = search_service
        
        # Store fetcher for later use
        app.state.ecommerce_fetcher = ecommerce_fetcher
        
        logger.info("Application startup complete!")
        
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Cross-Modal Product Recommendation API",
        "status": "healthy",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    """Health check with model status"""
    return {
        "status": "healthy",
        "models": {
            "clip_loaded": hasattr(app.state, 'clip_model') and app.state.clip_model is not None,
            "faiss_loaded": hasattr(app.state, 'faiss_index') and app.state.faiss_index is not None
        }
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )