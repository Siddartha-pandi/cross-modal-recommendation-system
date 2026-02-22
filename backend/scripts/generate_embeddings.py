"""
Generate embeddings for product catalog using CLIP
"""
import os
import sys
import json
import asyncio
from pathlib import Path
from PIL import Image
import numpy as np
from tqdm import tqdm
import logging

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.clip_model import CLIPModel
from app.utils.faiss_index import FAISSIndex

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def generate_embeddings():
    """
    Generate embeddings for all products in the catalog
    """
    # Initialize CLIP model
    clip_model = CLIPModel()
    
    # Load product catalog - use relative path from backend directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.dirname(script_dir)
    project_dir = os.path.dirname(backend_dir)
    catalog_path = os.path.join(project_dir, "data", "products.json")
    
    if not os.path.exists(catalog_path):
        logger.error(f"Product catalog not found at {catalog_path}")
        return
    
    with open(catalog_path, 'r') as f:
        products = json.load(f)
    
    logger.info(f"Processing {len(products)} products")
    
    # Initialize FAISS index
    embedding_dim = clip_model.get_embedding_dim()
    faiss_index = FAISSIndex(embedding_dim=embedding_dim)
    
    # Process products in batches
    batch_size = 32
    embeddings_list = []
    metadata_list = []
    
    for i in tqdm(range(0, len(products), batch_size), desc="Processing batches"):
        batch = products[i:i + batch_size]
        
        # Prepare batch data
        images = []
        texts = []
        batch_metadata = []
        
        for product in batch:
            # Always add product (with text or combined text+image)
            text = f"{product['title']}. {product.get('description', '')}"
            texts.append(text)
            
            # Load image if available
            image_path = os.path.join(project_dir, "data", "images", product['image'])
            if os.path.exists(image_path):
                try:
                    image = Image.open(image_path).convert('RGB')
                    images.append(image)
                except Exception as e:
                    logger.warning(f"Failed to load image {image_path}: {e}")
                    images.append(None)
            else:
                # No image available, will use text-only
                images.append(None)
                
            batch_metadata.append({
                'product_id': product['id'],
                'title': product['title'],
                'image_url': f"/images/{product['image']}",
                'category': product.get('category', ''),
                'price': product.get('price', 0.0)
            })
        
        if not texts:
            continue
        
        # Generate embeddings
        try:
            text_embeddings = await clip_model.encode_batch_texts(texts)
            
            # Check if we have any valid images
            valid_images = [img for img in images if img is not None]
            
            if valid_images and len(valid_images) == len(texts):
                # All images available - use combined embeddings
                image_embeddings = await clip_model.encode_batch_images(valid_images)
                combined_embeddings = 0.7 * image_embeddings + 0.3 * text_embeddings
                logger.info(f"Batch {i}: Using combined image+text embeddings")
            else:
                # Use text-only embeddings
                combined_embeddings = text_embeddings
                logger.info(f"Batch {i}: Using text-only embeddings (images not available)")
            
            # Normalize
            combined_embeddings = combined_embeddings / np.linalg.norm(
                combined_embeddings, axis=1, keepdims=True
            )
            
            embeddings_list.append(combined_embeddings)
            metadata_list.extend(batch_metadata)
            
        except Exception as e:
            logger.error(f"Failed to process batch {i}: {e}")
            continue
    
    if embeddings_list:
        # Combine all embeddings
        all_embeddings = np.vstack(embeddings_list)
        
        # Add to FAISS index
        faiss_index.add_batch_products(all_embeddings, metadata_list)
        
        # Save index
        faiss_index.save_index()
        
        logger.info(f"Generated embeddings for {len(metadata_list)} products")
        logger.info(f"Saved FAISS index successfully")
    else:
        logger.error("No embeddings generated")

if __name__ == "__main__":
    asyncio.run(generate_embeddings())