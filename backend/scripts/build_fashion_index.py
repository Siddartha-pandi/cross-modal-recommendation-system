"""
Build FAISS index from local products_fashion.json

This script:
1. Loads products from local products_fashion.json
2. Verifies product images exist
3. Generates CLIP embeddings for each product
4. Builds FAISS index for similarity search
5. Saves index and metadata
"""
import sys
import json
import asyncio
from pathlib import Path
from PIL import Image
import numpy as np
from tqdm import tqdm
import logging

# Add backend to path for app imports
backend_dir = Path(__file__).resolve().parents[1]
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.models.clip_model import CLIPModel
from app.utils.faiss_index import FAISSIndex

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
repo_root = None
for parent in [Path(__file__).resolve()] + list(Path(__file__).resolve().parents):
    if (parent / "data").exists() and (parent / "index").exists():
        repo_root = parent
        break
if repo_root is None:
    repo_root = backend_dir.parent

PROJECT_ROOT = repo_root
DATA_DIR = PROJECT_ROOT / "data"
IMAGES_DIR = DATA_DIR / "images"
INDEX_DIR = PROJECT_ROOT / "index"
PRODUCTS_FILE = DATA_DIR / "products_fashion.json"

def load_fashion_products() -> list:
    """Load products from products_fashion.json"""
    logger.info(f"Loading products from {PRODUCTS_FILE}...")
    
    try:
        with open(PRODUCTS_FILE, 'r', encoding='utf-8') as f:
            products = json.load(f)
        logger.info(f"✓ Loaded {len(products)} fashion products")
        return products
    except Exception as e:
        logger.error(f"Error loading products: {e}")
        return []

def verify_images(products: list) -> list:
    """Verify that product images exist"""
    logger.info("Verifying product images...")
    
    verified_products = []
    missing_images = []
    
    for product in products:
        image_filename = product.get('image')
        if not image_filename:
            logger.warning(f"Product {product['id']} has no image field")
            continue
        
        image_path = IMAGES_DIR / image_filename
        if not image_path.exists():
            missing_images.append(image_filename)
            continue
        
        # Verify image can be opened
        try:
            img = Image.open(image_path)
            img.verify()
            verified_products.append(product)
        except Exception as e:
            logger.warning(f"Invalid image {image_filename}: {e}")
            continue
    
    if missing_images:
        logger.warning(f"Missing {len(missing_images)} images: {missing_images[:5]}...")
    
    logger.info(f"✓ Verified {len(verified_products)} products with valid images")
    return verified_products

def prepare_metadata(products: list) -> list:
    """Prepare product metadata for indexing"""
    logger.info("Preparing product metadata...")
    
    processed_products = []
    
    for product in products:
        image_filename = product.get('image')
        
        processed_products.append({
            'id': product['id'],
            'title': product['title'],
            'description': product.get('description', ''),
            'price': product.get('price', 0.0),
            'category': product.get('category', ''),
            'subcategory': product.get('subcategory', ''),
            'brand': product.get('brand', ''),
            'color': product.get('color', ''),
            'pattern': product.get('pattern', ''),
            'material': product.get('material', ''),
            'rating': product.get('rating', 0.0),
            'tc_reference': product.get('tc_reference', ''),
            'image': image_filename,
            'image_url': f"/images/{image_filename}",
            'tags': product.get('tags', [])
        })
    
    logger.info(f"✓ Prepared metadata for {len(processed_products)} products")
    return processed_products

async def generate_embeddings(products: list):
    """Generate CLIP embeddings for all products"""
    logger.info("Generating CLIP embeddings...")
    
    # Initialize CLIP model
    clip_model = CLIPModel(model_name="ViT-B/32")
    embedding_dim = 512
    
    # Initialize FAISS index (don't load existing - we're rebuilding from scratch)
    faiss_index = FAISSIndex(embedding_dim=embedding_dim, index_type="HNSW", load_existing=False)
    
    # Process in batches
    batch_size = 16
    total_indexed = 0
    failed_products = []
    
    for i in tqdm(range(0, len(products), batch_size), desc="Generating embeddings"):
        batch = products[i:i + batch_size]
        
        batch_embeddings = []
        batch_metadata = []
        
        for product in batch:
            try:
                # Load image
                image_path = IMAGES_DIR / product['image']
                if not image_path.exists():
                    continue
                
                image = Image.open(image_path).convert('RGB')
                
                # Generate text and image embeddings
                # Combine title, description, and key attributes for better text embedding
                text_parts = [
                    product['title'],
                    product.get('description', ''),
                    product.get('category', ''),
                    product.get('color', ''),
                    product.get('pattern', ''),
                    product.get('material', '')
                ]
                text = '. '.join([part for part in text_parts if part])
                
                text_emb = await clip_model.encode_text(text)
                image_emb = await clip_model.encode_image(image)
                
                # IMPORTANT: Store pure image embeddings for indexing
                # This allows proper cross-modal matching via CLIP's joint embedding space
                # Text queries will naturally match visually similar products through CLIP
                
                batch_embeddings.append(image_emb)
                batch_metadata.append({
                    'product_id': product['id'],
                    'title': product['title'],
                    'description': product.get('description', ''),
                    'image_url': product['image_url'],
                    'price': product.get('price', 0.0),
                    'category': product.get('category', ''),
                    'subcategory': product.get('subcategory', ''),
                    'brand': product.get('brand', ''),
                    'color': product.get('color', ''),
                    'pattern': product.get('pattern', ''),
                    'material': product.get('material', ''),
                    'rating': product.get('rating', 0.0),
                    'tc_reference': product.get('tc_reference', ''),
                    'tags': product.get('tags', []),
                    # Store both embeddings in metadata for future hybrid search
                    'text_embedding': text_emb.tolist(),
                    'image_embedding': image_emb.tolist()
                })
                
            except Exception as e:
                logger.warning(f"Failed to process product {product['id']}: {e}")
                failed_products.append(product['id'])
                continue
        
        # Add batch to index
        if batch_embeddings:
            embeddings_array = np.array(batch_embeddings)
            faiss_index.add_batch_products(embeddings_array, batch_metadata)
            total_indexed += len(batch_embeddings)
    
    logger.info(f"✓ Generated embeddings for {total_indexed} products")
    if failed_products:
        logger.warning(f"Failed to process {len(failed_products)} products: {failed_products[:10]}...")
    
    # Save index
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    faiss_index.save_index()
    logger.info(f"✓ Saved FAISS index to {INDEX_DIR}")
    logger.info(f"✓ Index built with {len(faiss_index.product_metadata)} products")
    
    return faiss_index

async def main():
    """Main function to build the index"""
    logger.info("="*60)
    logger.info("Building FAISS Index from Fashion Products")
    logger.info("="*60)
    
    try:
        # Step 1: Load products from JSON
        products = load_fashion_products()
        
        if not products:
            logger.error("No products loaded. Exiting.")
            return
        
        # Step 2: Verify images exist
        verified_products = verify_images(products)
        
        if not verified_products:
            logger.error("No products with valid images. Exiting.")
            return
        
        # Step 3: Prepare metadata
        processed_products = prepare_metadata(verified_products)
        
        # Step 4: Generate embeddings and build index
        faiss_index = await generate_embeddings(processed_products)
        
        logger.info("="*60)
        logger.info("✓ Index building complete!")
        logger.info(f"Total products indexed: {len(faiss_index.product_metadata)}")
        logger.info("="*60)
        logger.info("\nYou can now start the server with:")
        logger.info("  cd backend")
        logger.info("  uvicorn app.main:app --reload")
        
    except Exception as e:
        logger.error(f"Failed to build index: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
