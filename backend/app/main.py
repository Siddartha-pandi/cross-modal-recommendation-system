"""
Simple, production-ready FastAPI server
For hybrid cross-modal fashion recommendation
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
from pathlib import Path
import logging

from app.api.routes import router
from app.api.cart_routes import router as cart_router, order_router
from app.api.recommend import recommend_router
from app.auth.routes import auth_router
from app.models.ml.clip_model import CLIPModel
from app.utils.faiss_index import FAISSIndex
from app.models.ml.fusion import FusionEngine
from app.services.product_catalog import initialize_product_catalog
from app.services.blip_caption import BlipCaptionService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Keep startup logs readable: BLIP/HF performs many optional-file probes that
# can return expected 404 responses and are not startup failures.
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("huggingface_hub").setLevel(logging.WARNING)

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
repo_root = None
for parent in [Path(__file__).resolve()] + list(Path(__file__).resolve().parents):
    if (parent / "data").exists() and (parent / "index").exists():
        repo_root = parent
        break
if repo_root is None:
    repo_root = Path(__file__).resolve().parents[2]

images_dir = repo_root / "data" / "images"
logger.info(f"Looking for images at: {images_dir}")
logger.info(f"Images dir exists: {images_dir.exists()}")

if images_dir.exists():
    app.mount("/images", StaticFiles(directory=str(images_dir)), name="images")
    logger.info(f"✓ Mounted static images from {images_dir}")
    # List sample images
    image_count = len(list(images_dir.glob("*.jpg")))
    logger.info(f"✓ Found {image_count} image files")
else:
    logger.warning(f"Images directory not found at {images_dir}")

# Include API routes
app.include_router(router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(cart_router, prefix="/api/v1")
app.include_router(order_router, prefix="/api/v1")
app.include_router(recommend_router, prefix="/api/v1")

@app.on_event("startup")
async def startup_event():
    """Load models on startup"""
    logger.info("="*50)
    logger.info("Starting Cross-Modal Recommendation System")
    logger.info("="*50)
    
    try:
        # ── CLIP ViT-B/32 for existing FAISS /search pipeline ─────────────
        logger.info("Loading CLIP model (ViT-B/32) for FAISS search...")
        clip_model = CLIPModel(model_name="ViT-B/32")
        app.state.clip_model = clip_model
        logger.info("✓ CLIP ViT-B/32 loaded successfully")

        # ── CLIP ViT-L/14 for live /recommend pipeline ─────────────────────
        logger.info("Loading CLIP model (ViT-L/14) for web-search recommend...")
        clip_model_large = CLIPModel(model_name="ViT-L/14")
        app.state.clip_model_large = clip_model_large
        logger.info("✓ CLIP ViT-L/14 loaded successfully (1024-dim)")

        # ── BLIP caption model for image-to-text query enrichment ──────────
        try:
            logger.info("Initializing BLIP caption service (lazy load)...")
            blip_captioner = BlipCaptionService()
            app.state.blip_captioner = blip_captioner
            logger.info("✓ BLIP caption service ready (model loads on first image request)")
        except Exception as e:
            logger.warning(f"⚠ BLIP caption model failed to load: {e}")
            logger.info("  Recommendation will continue without BLIP captions")

        # Initialize Fusion Engine
        logger.info("Initializing Fusion Engine...")
        fusion_engine = FusionEngine(default_alpha=0.5)
        app.state.fusion_engine = fusion_engine
        logger.info("✓ Fusion Engine initialized (α=0.5)")
        
        # Load FAISS index (512-dim, ViT-B/32 embeddings)
        logger.info("Loading FAISS index...")
        faiss_index = FAISSIndex(embedding_dim=512, index_type="HNSW")
        app.state.faiss_index = faiss_index
        
        total_products = faiss_index.get_total_products()
        logger.info(f"✓ FAISS index loaded: {total_products} products")
        
        if total_products == 0:
            logger.warning("⚠ No products in FAISS index. Run 'python backend/scripts/build_index.py' to build index.")
        
        # Initialize Product Catalog (for advanced recommendation)
        logger.info("Initializing Product Catalog for advanced recommendations...")
        try:
            product_catalog = initialize_product_catalog(embedding_dim=1024)  # ViT-L/14
            app.state.product_catalog = product_catalog
            
            catalog_stats = product_catalog.get_statistics()
            logger.info(f"✓ Product Catalog loaded: {catalog_stats['total_products']} products")
            logger.info(f"  - Categories: {catalog_stats['categories']}")
            logger.info(f"  - Indexed: {catalog_stats['indexed_products']}")
            
            if catalog_stats['indexed_products'] == 0:
                logger.warning("⚠ No products in catalog index. Run 'python -m backend.scripts.build_product_index' to build.")
        except Exception as e:
            logger.warning(f"⚠ Product Catalog initialization failed: {e}")
            logger.info("  Advanced recommendations will use web search only")
        
        # Validate search provider configuration
        logger.info("Validating search provider configuration...")
        from app.config.settings import settings
        provider = settings.SEARCH_PROVIDER.lower().strip()
        if provider in ["serapi", "serpapi"]:
            if not settings.SERP_API_KEY or settings.SERP_API_KEY.strip() == "":
                logger.warning("="*50)
                logger.warning("⚠ SERP_API_KEY is not configured!")
                logger.warning("  To use SerpAPI for web search:")
                logger.warning("  1. Get key from https://serpapi.com/")
                logger.warning("  2. Set SERP_API_KEY in backend/.env")
                logger.warning("  3. Restart server")
                logger.warning("  Fallback to DuckDuckGo will be used.")
                logger.warning("="*50)
            else:
                logger.info(f"✓ SerpAPI configured ({settings.SERP_API_KEY[:8]}...)")
        elif provider == "google":
            if not settings.GOOGLE_API_KEY or not settings.GOOGLE_CX:
                logger.warning("="*50)
                logger.warning("⚠ Google Custom Search API is not configured!")
                logger.warning("  To use Google CSE:")
                logger.warning("  1. Enable Custom Search JSON API at")
                logger.warning("     https://console.cloud.google.com/apis/library")
                logger.warning("  2. Create API key and Custom Search Engine ID")
                logger.warning("  3. Set GOOGLE_API_KEY and GOOGLE_CX in backend/.env")
                logger.warning("  4. Restart server")
                logger.warning("  Fallback to DuckDuckGo will be used.")
                logger.warning("="*50)
            else:
                logger.info(f"✓ Google CSE configured (Key: {settings.GOOGLE_API_KEY[:8]}..., CX: {settings.GOOGLE_CX[:8]}...)")
        else:
            logger.info(f"✓ Using {provider} (no API key required)")
        
        logger.info("="*50)
        logger.info("Server ready! 🚀")
        logger.info("Endpoints:")
        logger.info("  /api/v1/search - FAISS-based search")
        logger.info("  /api/v1/recommend - Standard web-based recommendation")
        logger.info("  /api/v1/recommend/advanced - Advanced multi-stage recommendation")
        logger.info("API Docs: http://localhost:8001/docs")
        logger.info("="*50)
        
    except MemoryError as e:
        logger.error(f"⚠ Memory error loading models: {e}")
        logger.warning("⚠ Server starting without ML models - Authentication will work, but search may not")
        logger.info("="*50)
        logger.info("Server ready (limited mode)! 🚀")
        logger.info("API Docs: http://localhost:8000/docs")
        logger.info("="*50)
    except Exception as e:
        logger.error(f"⚠ Error loading models: {e}", exc_info=True)
        logger.warning("⚠ Server starting without ML models - Authentication will work, but search may not")
        logger.info("="*50)
        logger.info("Server ready (limited mode)! 🚀")
        logger.info("API Docs: http://localhost:8000/docs")
        logger.info("="*50)

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
    import os
    port = int(os.environ.get("PORT", 8001))
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )
