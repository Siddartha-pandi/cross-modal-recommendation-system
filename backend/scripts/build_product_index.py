"""
Build Product Embeddings Script
Creates CLIP embeddings for all products and builds FAISS index.

Usage:
    python -m backend.scripts.build_product_index

This script:
1. Loads all products from products.json
2. Generates CLIP embeddings for each product image
3. Builds FAISS index for fast similarity search
4. Saves index and metadata for later use
"""
import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.models.ml.clip_model import CLIPModel
from app.services.product_catalog import initialize_product_catalog
from app.config.settings import settings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def build_index():
    """Build product embeddings and FAISS index."""
    logger.info("="*80)
    logger.info("Building Product Embeddings and FAISS Index")
    logger.info("="*80)
    
    # Initialize CLIP model
    logger.info(f"Loading CLIP model: {settings.CLIP_MODEL_LARGE}")
    clip_model = CLIPModel(model_name=settings.CLIP_MODEL_LARGE)
    
    # Initialize product catalog
    logger.info("Initializing product catalog...")
    catalog = initialize_product_catalog(embedding_dim=1024)  # ViT-L/14 = 1024-dim
    
    logger.info(f"Found {len(catalog.products)} products")
    
    # Build embeddings
    logger.info("Building product embeddings (this may take a while)...")
    count = await catalog.build_product_embeddings(clip_model)
    
    logger.info("="*80)
    logger.info(f"✓ Successfully built embeddings for {count} products")
    logger.info(f"✓ FAISS index saved to: {catalog.faiss_index.index_path}")
    
    # Print statistics
    stats = catalog.get_statistics()
    logger.info("\nCatalog Statistics:")
    logger.info(f"  Total products: {stats['total_products']}")
    logger.info(f"  Categories: {stats['categories']}")
    logger.info(f"  Brands: {stats['brands']}")
    logger.info(f"  Indexed products: {stats['indexed_products']}")
    logger.info(f"  Average price: ₹{stats['avg_price']:.2f}")
    logger.info(f"  Average rating: {stats['avg_rating']:.2f}/5.0")
    logger.info("="*80)
    
    # Test search
    logger.info("\nTesting FAISS search...")
    test_query = "blue casual shirt"
    logger.info(f"Query: '{test_query}'")
    
    test_embedding = await clip_model.encode_text(test_query)
    results = await catalog.search_similar_products(
        query_embedding=test_embedding,
        top_k=5
    )
    
    logger.info(f"Found {len(results)} similar products:")
    for i, (product, score) in enumerate(results[:5]):
        logger.info(f"  {i+1}. {product.title} (similarity: {score:.4f})")
    
    logger.info("\n✓ Index building complete!")


if __name__ == "__main__":
    asyncio.run(build_index())
