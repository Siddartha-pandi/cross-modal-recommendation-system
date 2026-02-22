"""
Build FAISS index from external e-commerce API (DummyJSON)

This script:
1. Fetches products from DummyJSON API (https://dummyjson.com)
2. Downloads product images
3. Generates CLIP embeddings for each product
4. Builds FAISS index for similarity search
5. Saves index and metadata
"""
import os
import sys
import json
import asyncio
import aiohttp
import aiofiles
from pathlib import Path
from PIL import Image
import numpy as np
from tqdm import tqdm
import logging

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.clip_model import CLIPModel
from app.utils.faiss_index import FAISSIndex

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
DUMMYJSON_API = "https://dummyjson.com/products"
MAX_PRODUCTS = 100  # Fetch up to 100 products
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
IMAGES_DIR = DATA_DIR / "images"
INDEX_DIR = PROJECT_ROOT / "index"

async def fetch_products(session: aiohttp.ClientSession, limit: int = 100) -> list:
    """Fetch products from DummyJSON API"""
    logger.info(f"Fetching products from DummyJSON API...")
    
    try:
        # DummyJSON allows fetching all products at once
        url = f"{DUMMYJSON_API}?limit={limit}"
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                products = data.get('products', [])
                logger.info(f"✓ Fetched {len(products)} products")
                return products
            else:
                logger.error(f"Failed to fetch products: HTTP {response.status}")
                return []
    except Exception as e:
        logger.error(f"Error fetching products: {e}")
        return []

async def download_image(session: aiohttp.ClientSession, url: str, save_path: Path) -> bool:
    """Download an image from URL"""
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
            if response.status == 200:
                content = await response.read()
                async with aiofiles.open(save_path, 'wb') as f:
                    await f.write(content)
                
                # Verify image is valid
                try:
                    img = Image.open(save_path)
                    img.verify()
                    return True
                except:
                    save_path.unlink(missing_ok=True)
                    return False
            return False
    except Exception as e:
        logger.debug(f"Failed to download {url}: {e}")
        return False

async def process_products(products: list):
    """Process products: download images and prepare metadata"""
    logger.info("Processing products and downloading images...")
    
    # Create directories
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    
    processed_products = []
    
    async with aiohttp.ClientSession() as session:
        for product in tqdm(products, desc="Processing products"):
            try:
                product_id = product['id']
                
                # Get primary image
                image_url = product.get('thumbnail') or (
                    product['images'][0] if product.get('images') else None
                )
                
                if not image_url:
                    logger.warning(f"No image for product {product_id}")
                    continue
                
                # Download image
                image_filename = f"product_{product_id}.jpg"
                image_path = IMAGES_DIR / image_filename
                
                if not image_path.exists():
                    success = await download_image(session, image_url, image_path)
                    if not success:
                        logger.warning(f"Failed to download image for product {product_id}")
                        continue
                
                # Prepare product metadata
                processed_products.append({
                    'id': product_id,
                    'title': product.get('title', ''),
                    'description': product.get('description', ''),
                    'price': product.get('price', 0.0),
                    'category': product.get('category', ''),
                    'brand': product.get('brand', ''),
                    'rating': product.get('rating', 0.0),
                    'image': image_filename,
                    'image_url': f"/images/{image_filename}",
                    'external_url': image_url
                })
                
            except Exception as e:
                logger.warning(f"Error processing product {product.get('id', 'unknown')}: {e}")
                continue
    
    logger.info(f"✓ Processed {len(processed_products)} products with images")
    
    # Save products to JSON
    products_file = DATA_DIR / "products.json"
    with open(products_file, 'w') as f:
        json.dump(processed_products, f, indent=2)
    logger.info(f"✓ Saved products to {products_file}")
    
    return processed_products

async def generate_embeddings(products: list):
    """Generate CLIP embeddings for all products"""
    logger.info("Generating CLIP embeddings...")
    
    # Initialize CLIP model
    clip_model = CLIPModel(model_name="ViT-B/32")
    embedding_dim = 512
    
    # Initialize FAISS index
    faiss_index = FAISSIndex(embedding_dim=embedding_dim, index_type="HNSW")
    
    # Process in batches
    batch_size = 16
    total_indexed = 0
    
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
                text = f"{product['title']}. {product['description']}"
                
                text_emb = await clip_model.encode_text(text)
                image_emb = await clip_model.encode_image(image)
                
                # Use hybrid embedding (0.5 text + 0.5 image) for indexing
                # This gives good baseline that works for all search types
                combined_emb = 0.5 * text_emb + 0.5 * image_emb
                combined_emb = combined_emb / np.linalg.norm(combined_emb)
                
                batch_embeddings.append(combined_emb)
                batch_metadata.append({
                    'product_id': product['id'],
                    'title': product['title'],
                    'description': product['description'],
                    'image_url': product['image_url'],
                    'price': product['price'],
                    'category': product['category'],
                    'brand': product.get('brand', ''),
                    'rating': product.get('rating', 0.0)
                })
                
            except Exception as e:
                logger.warning(f"Failed to process product {product['id']}: {e}")
                continue
        
        # Add batch to index
        if batch_embeddings:
            embeddings_array = np.array(batch_embeddings)
            faiss_index.add_batch_products(embeddings_array, batch_metadata)
            total_indexed += len(batch_embeddings)
    
    logger.info(f"✓ Generated embeddings for {total_indexed} products")
    
    # Save index
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    faiss_index.save_index()
    logger.info(f"✓ Saved FAISS index to {INDEX_DIR}")
    
    # Print statistics
    stats = faiss_index.get_statistics()
    logger.info("Index Statistics:")
    for key, value in stats.items():
        logger.info(f"  {key}: {value}")
    
    return faiss_index

async def main():
    """Main function to build the index"""
    logger.info("="*60)
    logger.info("Building FAISS Index from External E-commerce API")
    logger.info("="*60)
    
    try:
        # Step 1: Fetch products from API
        async with aiohttp.ClientSession() as session:
            products = await fetch_products(session, limit=MAX_PRODUCTS)
        
        if not products:
            logger.error("No products fetched. Exiting.")
            return
        
        # Step 2: Process products (download images)
        processed_products = await process_products(products)
        
        if not processed_products:
            logger.error("No products processed. Exiting.")
            return
        
        # Step 3: Generate embeddings and build index
        faiss_index = await generate_embeddings(processed_products)
        
        logger.info("="*60)
        logger.info("✓ Index building complete!")
        logger.info(f"Total products indexed: {faiss_index.get_total_products()}")
        logger.info("="*60)
        logger.info("\nYou can now start the server with:")
        logger.info("  python backend/simple_main.py")
        
    except Exception as e:
        logger.error(f"Error building index: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    asyncio.run(main())
