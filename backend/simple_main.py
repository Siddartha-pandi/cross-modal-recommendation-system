"""
Simple, production-ready FastAPI server
For hybrid cross-modal fashion recommendation
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
import os
import logging

from app.api.simple_routes import router
from app.models.clip_model import CLIPModel
from app.utils.faiss_index import FAISSIndex

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Cross-Modal Fashion Recommendation API",
    description="Hybrid search with text and images using CLIP + FAISS",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "https://*.vercel.app",  # Vercel deployments
        "*"  # Allow all origins (customize in production)
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Mount static files for images
images_dir = os.path.join(os.path.dirname(__file__), "data", "images")
if os.path.exists(images_dir):
    app.mount("/images", StaticFiles(directory=images_dir), name="images")
    logger.info(f"Mounted static images from {images_dir}")

# Include API routes
app.include_router(router, prefix="/api/v1")

@app.on_event("startup")
async def startup_event():
    """Load models on startup"""
    logger.info("="*50)
    logger.info("Starting Cross-Modal Recommendation System")
    logger.info("="*50)
    
    try:
        # Load CLIP model
        logger.info("Loading CLIP model (ViT-B/32)...")
        clip_model = CLIPModel(model_name="ViT-B/32")
        app.state.clip_model = clip_model
        logger.info("✓ CLIP model loaded successfully")
        
        # Load FAISS index
        logger.info("Loading FAISS index...")
        faiss_index = FAISSIndex(embedding_dim=512, index_type="HNSW")
        app.state.faiss_index = faiss_index
        
        total_products = faiss_index.get_total_products()
        logger.info(f"✓ FAISS index loaded: {total_products} products")
        
        if total_products == 0:
            logger.warning("⚠ No products in index. Run 'python backend/scripts/simple_build_index.py' to build index.")
        
        logger.info("="*50)
        logger.info("Server ready! 🚀")
        logger.info("API Docs: http://localhost:8000/docs")
        logger.info("="*50)
        
    except Exception as e:
        logger.error(f"Failed to load models: {e}", exc_info=True)
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down server...")

@app.get("/")
async def root():
    """Root endpoint with API info"""
    return {
        "name": "Cross-Modal Fashion Recommendation API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "search": "/api/v1/search",
            "health": "/api/v1/health",
            "stats": "/api/v1/stats",
            "docs": "/docs"
        }
    }

if __name__ == "__main__":
    uvicorn.run(
        "simple_main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
