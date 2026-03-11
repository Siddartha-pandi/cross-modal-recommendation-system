"""
Product Catalog Service
Manages product database and FAISS index for fast candidate retrieval.

Implements:
- Product database loading
- FAISS index building and querying
- Fast k-NN search for candidate generation
- Product metadata management
"""
import json
import logging
import asyncio
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
import numpy as np

from app.utils.faiss_index import FAISSIndex
from app.services.query_understanding import QueryAttributes

logger = logging.getLogger(__name__)


@dataclass
class Product:
    """Product entity with all metadata."""
    id: int
    title: str
    description: str
    category: str
    subcategory: Optional[str] = None
    color: Optional[str] = None
    pattern: Optional[str] = None
    material: Optional[str] = None
    weather: Optional[str] = None
    sleeve_type: Optional[str] = None
    collar_type: Optional[str] = None
    sole_type: Optional[str] = None
    closure: Optional[str] = None
    use: Optional[str] = None
    neckline: Optional[str] = None
    length: Optional[str] = None
    size: Optional[str] = None
    price: float = 0.0
    currency: str = "INR"
    rating: float = 0.0
    brand: Optional[str] = None
    image: Optional[str] = None
    tags: List[str] = None
    embedding: Optional[np.ndarray] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
    
    def to_dict(self) -> Dict:
        """Convert to dictionary (excluding embedding)."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "subcategory": self.subcategory,
            "color": self.color,
            "pattern": self.pattern,
            "material": self.material,
            "weather": self.weather,
            "sleeve_type": self.sleeve_type,
            "collar_type": self.collar_type,
            "sole_type": self.sole_type,
            "closure": self.closure,
            "use": self.use,
            "neckline": self.neckline,
            "length": self.length,
            "size": self.size,
            "price": self.price,
            "currency": self.currency,
            "rating": self.rating,
            "brand": self.brand,
            "image": self.image,
            "tags": self.tags,
        }
    
    def matches_attribute(self, attr_name: str, attr_value: str) -> bool:
        """Check if product matches a specific attribute value."""
        if attr_name == "color":
            return self.color and attr_value.lower() in self.color.lower()
        elif attr_name == "category":
            return (
                (self.category and attr_value.lower() in self.category.lower()) or
                (self.subcategory and attr_value.lower() in self.subcategory.lower())
            )
        elif attr_name == "pattern":
            return self.pattern and attr_value.lower() in self.pattern.lower()
        elif attr_name == "material":
            return self.material and attr_value.lower() in self.material.lower()
        elif attr_name == "weather":
            return self.weather and attr_value.lower() in self.weather.lower()
        elif attr_name == "sleeve_type":
            return self.sleeve_type and attr_value.lower() in self.sleeve_type.lower()
        elif attr_name == "collar_type":
            return self.collar_type and attr_value.lower() in self.collar_type.lower()
        elif attr_name == "sole_type":
            return self.sole_type and attr_value.lower() in self.sole_type.lower()
        elif attr_name == "closure":
            return self.closure and attr_value.lower() in self.closure.lower()
        elif attr_name == "use":
            return self.use and attr_value.lower() in self.use.lower()
        elif attr_name == "neckline":
            return self.neckline and attr_value.lower() in self.neckline.lower()
        elif attr_name == "length":
            return self.length and attr_value.lower() in self.length.lower()
        elif attr_name == "brand":
            return self.brand and attr_value.lower() in self.brand.lower()
        elif attr_name == "gender":
            # Infer from tags or title
            title_lower = self.title.lower()
            return attr_value.lower() in title_lower or any(attr_value.lower() in tag for tag in self.tags)
        return False
    
    def get_popularity_score(self) -> float:
        """Compute popularity score based on rating."""
        # Simple popularity: normalize rating to 0-1
        return self.rating / 5.0 if self.rating > 0 else 0.5


class ProductCatalogService:
    """
    Service for managing product catalog and FAISS index.
    
    Responsibilities:
    - Load product database from JSON
    - Build/maintain FAISS index of product embeddings
    - Fast candidate retrieval via k-NN search
    - Attribute-based filtering
    """
    
    def __init__(
        self,
        products_file: Optional[Path] = None,
        embedding_dim: int = 512,
    ):
        """
        Initialize product catalog.
        
        Args:
            products_file: Path to products JSON file
            embedding_dim: Dimension of embeddings (512 for ViT-B/32, 1024 for ViT-L/14)
        """
        # Find repository root
        repo_root = self._find_repo_root()
        self.repo_root = repo_root
        
        # Set paths
        if products_file is None:
            products_file = repo_root / "data" / "products.json"
        self.products_file = products_file
        
        self.embedding_dim = embedding_dim
        self.products: List[Product] = []
        self.product_index: Dict[int, Product] = {}
        self.faiss_index: Optional[FAISSIndex] = None
        
        # Load products
        self._load_products()
        
        # Initialize FAISS index
        self._init_faiss_index()
        
        logger.info(
            f"ProductCatalogService initialized with {len(self.products)} products"
        )
    
    def _find_repo_root(self) -> Path:
        """Find repository root directory."""
        current = Path(__file__).resolve()
        for parent in [current] + list(current.parents):
            if (parent / "data").exists() and (parent / "backend").exists():
                return parent
        # Fallback
        return Path(__file__).resolve().parents[3]
    
    def _load_products(self):
        """Load products from JSON file."""
        if not self.products_file.exists():
            logger.warning(f"Products file not found: {self.products_file}")
            return
        
        try:
            with open(self.products_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for item in data:
                product = Product(
                    id=item.get("id"),
                    title=item.get("title", ""),
                    description=item.get("description", ""),
                    category=item.get("category", ""),
                    subcategory=item.get("subcategory"),
                    color=item.get("color"),
                    pattern=item.get("pattern"),
                    material=item.get("material"),
                    weather=item.get("weather"),
                    sleeve_type=item.get("sleeve_type"),
                    collar_type=item.get("collar_type"),
                    sole_type=item.get("sole_type"),
                    closure=item.get("closure"),
                    use=item.get("use"),
                    neckline=item.get("neckline"),
                    length=item.get("length"),
                    size=item.get("size"),
                    price=item.get("price", 0.0),
                    currency=item.get("currency", "INR"),
                    rating=item.get("rating", 0.0),
                    brand=item.get("brand"),
                    image=item.get("image"),
                    tags=item.get("tags", []),
                )
                self.products.append(product)
                self.product_index[product.id] = product
            
            logger.info(f"Loaded {len(self.products)} products from {self.products_file}")
        
        except Exception as e:
            logger.error(f"Failed to load products: {e}")
    
    def _init_faiss_index(self):
        """Initialize FAISS index for fast retrieval."""
        self.faiss_index = FAISSIndex(
            embedding_dim=self.embedding_dim,
            index_type="HNSW",
            load_existing=True,
        )
        logger.info("FAISS index initialized")
    
    async def build_product_embeddings(self, clip_model) -> int:
        """
        Build embeddings for all products using CLIP model.
        
        Args:
            clip_model: CLIPModel instance
        
        Returns:
            Number of products embedded
        """
        from PIL import Image
        
        count = 0
        image_dir = self.repo_root / "data" / "images"
        
        logger.info(f"Building embeddings for {len(self.products)} products...")
        
        for product in self.products:
            if product.image:
                image_path = image_dir / product.image
                
                if image_path.exists():
                    try:
                        # Load image
                        img = Image.open(image_path).convert("RGB")
                        
                        # Generate embedding
                        embedding = await clip_model.encode_image(img)
                        product.embedding = embedding
                        
                        # Add to FAISS index
                        self.faiss_index.add_product(
                            embedding=embedding,
                            metadata=product.to_dict()
                        )
                        
                        count += 1
                        
                        if count % 100 == 0:
                            logger.info(f"Processed {count} products...")
                    
                    except Exception as e:
                        logger.warning(f"Failed to process {product.image}: {e}")
                else:
                    logger.debug(f"Image not found: {image_path}")
            else:
                # Use text-only embedding for products without images
                try:
                    text = f"{product.title} {product.description}"
                    embedding = await clip_model.encode_text(text)
                    product.embedding = embedding
                    
                    self.faiss_index.add_product(
                        embedding=embedding,
                        metadata=product.to_dict()
                    )
                    count += 1
                except Exception as e:
                    logger.warning(f"Failed to create text embedding for product {product.id}: {e}")
        
        # Save index
        self.faiss_index.save()
        logger.info(f"Built embeddings for {count} products and saved index")
        
        return count
    
    async def search_similar_products(
        self,
        query_embedding: np.ndarray,
        top_k: int = 200,
        attributes: Optional[QueryAttributes] = None,
    ) -> List[Tuple[Product, float]]:
        """
        Search for similar products using FAISS index.
        
        Args:
            query_embedding: Query embedding vector
            top_k: Number of results to return
            attributes: Optional query attributes for filtering
        
        Returns:
            List of (Product, similarity_score) tuples
        """
        if self.faiss_index is None or self.faiss_index.index.ntotal == 0:
            logger.warning("FAISS index is empty")
            return []
        
        # Search FAISS index
        try:
            distances, indices, metadata_list = self.faiss_index.search(
                query_embedding=query_embedding,
                k=top_k * 2  # Get more candidates for filtering
            )
            
            results = []
            
            for idx, (distance, product_data) in enumerate(zip(distances, metadata_list)):
                product_id = product_data.get("id")
                
                if product_id in self.product_index:
                    product = self.product_index[product_id]
                    similarity = float(distance)  # Already cosine similarity from FAISS
                    
                    # Apply attribute filtering if provided
                    if attributes:
                        if not self._matches_attributes(product, attributes):
                            continue
                    
                    results.append((product, similarity))
                    
                    if len(results) >= top_k:
                        break
            
            logger.debug(f"Found {len(results)} similar products from index")
            return results
        
        except Exception as e:
            logger.error(f"FAISS search failed: {e}")
            return []
    
    def _matches_attributes(
        self,
        product: Product,
        attributes: QueryAttributes
    ) -> bool:
        """Check if product matches query attributes."""
        # Color match
        if attributes.colors:
            if not any(product.matches_attribute("color", c) for c in attributes.colors):
                return False
        
        # Category match
        if attributes.categories:
            if not any(product.matches_attribute("category", c) for c in attributes.categories):
                return False
        
        # Pattern match
        if attributes.patterns:
            if not any(product.matches_attribute("pattern", p) for p in attributes.patterns):
                return False
        
        # Material match
        if attributes.materials:
            if not any(product.matches_attribute("material", m) for m in attributes.materials):
                return False

        # Weather / season match
        if attributes.seasons:
            if not any(product.matches_attribute("weather", s) for s in attributes.seasons):
                return False
        
        # Gender match
        if attributes.genders:
            if not any(product.matches_attribute("gender", g) for g in attributes.genders):
                return False
        
        # Price range match
        if attributes.price_range:
            min_price, max_price = attributes.price_range
            if not (min_price <= product.price <= max_price):
                return False
        
        return True
    
    def get_product_by_id(self, product_id: int) -> Optional[Product]:
        """Get product by ID."""
        return self.product_index.get(product_id)
    
    def get_products_by_category(self, category: str) -> List[Product]:
        """Get all products in a category."""
        return [
            p for p in self.products
            if p.category.lower() == category.lower()
        ]
    
    def get_all_categories(self) -> List[str]:
        """Get all unique categories."""
        return list(set(p.category for p in self.products if p.category))
    
    def get_all_brands(self) -> List[str]:
        """Get all unique brands."""
        return list(set(p.brand for p in self.products if p.brand))
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get catalog statistics."""
        return {
            "total_products": len(self.products),
            "categories": len(self.get_all_categories()),
            "brands": len(self.get_all_brands()),
            "indexed_products": self.faiss_index.index.ntotal if self.faiss_index else 0,
            "avg_price": np.mean([p.price for p in self.products if p.price > 0]),
            "avg_rating": np.mean([p.rating for p in self.products if p.rating > 0]),
        }


# ─── Singleton Instance ──────────────────────────────────────────────────────
# Will be initialized in main.py startup
product_catalog_service: Optional[ProductCatalogService] = None


def get_product_catalog() -> ProductCatalogService:
    """Get singleton instance of product catalog."""
    global product_catalog_service
    if product_catalog_service is None:
        raise RuntimeError("ProductCatalogService not initialized. Call initialize_product_catalog() first.")
    return product_catalog_service


def initialize_product_catalog(embedding_dim: int = 512) -> ProductCatalogService:
    """Initialize the product catalog singleton."""
    global product_catalog_service
    product_catalog_service = ProductCatalogService(embedding_dim=embedding_dim)
    return product_catalog_service
