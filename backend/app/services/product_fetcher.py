"""
E-commerce Product Fetcher System
Supports multiple platforms with unified interface
"""

import asyncio
import aiohttp
import logging
from typing import List, Dict, Optional, Any
from abc import ABC, abstractmethod
from datetime import datetime
import os

logger = logging.getLogger(__name__)


class ProductFetcher(ABC):
    """Base class for e-commerce product fetchers"""
    
    @abstractmethod
    async def fetch_products(
        self,
        category: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Fetch products from platform"""
        pass
    
    @abstractmethod
    async def fetch_product_detail(self, product_id: str) -> Optional[Dict[str, Any]]:
        """Fetch single product details"""
        pass
    
    def normalize_product(self, raw_data: Dict) -> Dict[str, Any]:
        """Normalize product data to common format"""
        return {
            'product_id': str(raw_data.get('id', '')),
            'title': raw_data.get('title', ''),
            'description': raw_data.get('description', ''),
            'price': float(raw_data.get('price', 0)),
            'category': raw_data.get('category', ''),
            'brand': raw_data.get('brand', ''),
            'image_url': raw_data.get('image', raw_data.get('image_url', '')),
            'images': raw_data.get('images', []),
            'rating': float(raw_data.get('rating', 0)),
            'review_count': int(raw_data.get('review_count', 0)),
            'availability': raw_data.get('in_stock', True),
            'specifications': raw_data.get('specs', {}),
            'source': self.__class__.__name__
        }


class DummyFetcher(ProductFetcher):
    """
    Dummy fetcher for testing - generates synthetic products
    """
    
async def fetch_products(
        self,
        category: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Generate synthetic products"""
        logger.info(f"Generating {limit} dummy products")
        
        categories = ['Dresses', 'Tops', 'Bottoms', 'Shoes', 'Accessories']
        brands = ['Nike', 'Adidas', 'Zara', 'H&M', 'Uniqlo']
        
        products = []
        for i in range(limit):
            product = {
                'id': f'PROD{i:05d}',
                'title': f'Product {i} - Fashion Item',
                'description': f'High-quality fashion item {i} with premium materials',
                'price': round(29.99 + (i % 50) * 10, 2),
                'category': categories[i % len(categories)],
                'brand': brands[i % len(brands)],
                'image': f'https://source.unsplash.com/400x400/?fashion,{i}',
                'images': [f'https://source.unsplash.com/400x400/?fashion,{i}'],
                'rating': round(3.5 + (i % 15) / 10, 1),
                'review_count': 10 + (i % 100),
                'in_stock': True,
                'specs': {'material': 'Cotton', 'origin': 'USA'}
            }
            products.append(self.normalize_product(product))
        
        return products
    
    async def fetch_product_detail(self, product_id: str) -> Optional[Dict[str, Any]]:
        """Generate single product detail"""
        product = {
            'id': product_id,
            'title': f'Product {product_id} - Fashion Item',
            'description': 'Detailed description of the product',
            'price': 99.99,
            'category': 'Dresses',
            'brand': 'Premium Brand',
            'image': f'https://source.unsplash.com/600x600/?fashion',
            'images': [f'https://source.unsplash.com/600x600/?fashion,{i}' for i in range(4)],
            'rating': 4.5,
            'review_count': 128,
            'in_stock': True,
            'specs': {'material': 'Cotton', 'size': 'M', 'color': 'Blue'}
        }
        return self.normalize_product(product)


class AmazonFetcher(ProductFetcher):
    """
    Amazon product fetcher (requires API credentials)
    Uses Amazon Product Advertising API
    """
    
    def __init__(self, api_key: str = None, api_secret: str = None):
        self.api_key = api_key or os.getenv('AMAZON_API_KEY')
        self.api_secret = api_secret or os.getenv('AMAZON_API_SECRET')
        self.base_url = 'https://webservices.amazon.com/paapi5'
    
    async def fetch_products(
        self,
        category: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Fetch from Amazon API"""
        if not self.api_key:
            logger.warning("Amazon API key not configured, using dummy data")
            return await DummyFetcher().fetch_products(category, limit)
        
        # Implement Amazon API calls here
        logger.info("Amazon API integration coming soon")
        return []
    
    async def fetch_product_detail(self, product_id: str) -> Optional[Dict[str, Any]]:
        """Fetch Amazon product detail"""
        logger.info(f"Fetching Amazon product: {product_id}")
        return None


class ShopifyFetcher(ProductFetcher):
    """
    Shopify product fetcher
    Uses Shopify Admin API or Storefront API
    """
    
    def __init__(self, shop_url: str = None, access_token: str = None):
        self.shop_url = shop_url or os.getenv('SHOPIFY_SHOP_URL')
        self.access_token = access_token or os.getenv('SHOPIFY_ACCESS_TOKEN')
    
    async def fetch_products(
        self,
        category: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Fetch from Shopify API"""
        if not self.shop_url or not self.access_token:
            logger.warning("Shopify credentials not configured")
            return []
        
        url = f"{self.shop_url}/admin/api/2024-01/products.json"
        headers = {'X-Shopify-Access-Token': self.access_token}
        params = {'limit': min(limit, 250)}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        products = data.get('products', [])
                        return [self._convert_shopify_product(p) for p in products]
                    else:
                        logger.error(f"Shopify API error: {response.status}")
                        return []
        except Exception as e:
            logger.error(f"Shopify fetch error: {e}")
            return []
    
    def _convert_shopify_product(self, raw: Dict) -> Dict[str, Any]:
        """Convert Shopify format to normalized format"""
        image = raw.get('images', [{}])[0].get('src', '') if raw.get('images') else ''
        
        return self.normalize_product({
            'id': str(raw.get('id')),
            'title': raw.get('title', ''),
            'description': raw.get('body_html', ''),
            'price': float(raw.get('variants', [{}])[0].get('price', 0)),
            'category': raw.get('product_type', ''),
            'brand': raw.get('vendor', ''),
            'image': image,
            'images': [img.get('src', '') for img in raw.get('images', [])],
            'in_stock': raw.get('variants', [{}])[0].get('inventory_quantity', 0) > 0
        })
    
    async def fetch_product_detail(self, product_id: str) -> Optional[Dict[str, Any]]:
        """Fetch Shopify product detail"""
        if not self.shop_url or not self.access_token:
            return None
        
        url = f"{self.shop_url}/admin/api/2024-01/products/{product_id}.json"
        headers = {'X-Shopify-Access-Token': self.access_token}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._convert_shopify_product(data.get('product', {}))
        except Exception as e:
            logger.error(f"Shopify detail fetch error: {e}")
        
        return None


class WooCommerceFetcher(ProductFetcher):
    """
    WooCommerce product fetcher
    Uses WooCommerce REST API
    """
    
    def __init__(self, store_url: str = None, consumer_key: str = None, consumer_secret: str = None):
        self.store_url = store_url or os.getenv('WOOCOMMERCE_URL')
        self.consumer_key = consumer_key or os.getenv('WOOCOMMERCE_KEY')
        self.consumer_secret = consumer_secret or os.getenv('WOOCOMMERCE_SECRET')
    
    async def fetch_products(
        self,
        category: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Fetch from WooCommerce API"""
        if not self.store_url:
            logger.warning("WooCommerce URL not configured")
            return []
        
        url = f"{self.store_url}/wp-json/wc/v3/products"
        auth = aiohttp.BasicAuth(self.consumer_key, self.consumer_secret)
        params = {'per_page': min(limit, 100)}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, auth=auth, params=params) as response:
                    if response.status == 200:
                        products = await response.json()
                        return [self._convert_woo_product(p) for p in products]
                    else:
                        logger.error(f"WooCommerce API error: {response.status}")
                        return []
        except Exception as e:
            logger.error(f"WooCommerce fetch error: {e}")
            return []
    
    def _convert_woo_product(self, raw: Dict) -> Dict[str, Any]:
        """Convert WooCommerce format"""
        return self.normalize_product({
            'id': str(raw.get('id')),
            'title': raw.get('name', ''),
            'description': raw.get('description', ''),
            'price': float(raw.get('price', 0)),
            'category': ', '.join([c.get('name', '') for c in raw.get('categories', [])]),
            'brand': '',
            'image': raw.get('images', [{}])[0].get('src', ''),
            'images': [img.get('src', '') for img in raw.get('images', [])],
            'rating': float(raw.get('average_rating', 0)),
            'review_count': int(raw.get('rating_count', 0)),
            'in_stock': raw.get('stock_status') == 'instock'
        })
    
    async def fetch_product_detail(self, product_id: str) -> Optional[Dict[str, Any]]:
        """Fetch WooCommerce product detail"""
        if not self.store_url:
            return None
        
        url = f"{self.store_url}/wp-json/wc/v3/products/{product_id}"
        auth = aiohttp.BasicAuth(self.consumer_key, self.consumer_secret)
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, auth=auth) as response:
                    if response.status == 200:
                        product = await response.json()
                        return self._convert_woo_product(product)
        except Exception as e:
            logger.error(f"WooCommerce detail fetch error: {e}")
        
        return None


class ProductFetcherFactory:
    """
    Factory for creating appropriate product fetcher
    """
    
    @staticmethod
    def create(platform: str = 'dummy') -> ProductFetcher:
        """
        Create fetcher for specified platform
        
        Args:
            platform: 'dummy', 'amazon', 'shopify', 'woocommerce'
        
        Returns:
            ProductFetcher instance
        """
        platform = platform.lower()
        
        if platform == 'amazon':
            return AmazonFetcher()
        elif platform == 'shopify':
            return ShopifyFetcher()
        elif platform == 'woocommerce':
            return WooCommerceFetcher()
        else:
            logger.info("Using dummy product fetcher for development")
            return DummyFetcher()


async def fetch_and_index_products(
    platform: str,
    clip_model,
    faiss_index,
    limit: int = 100
):
    """
    Fetch products and add them to FAISS index with embeddings
    
    Args:
        platform: E-commerce platform name
        clip_model: CLIP model instance
        faiss_index: FAISS index instance
        limit: Number of products to fetch
    """
    logger.info(f"Fetching products from {platform}...")
    
    fetcher = ProductFetcherFactory.create(platform)
    products = await fetcher.fetch_products(limit=limit)
    
    logger.info(f"Fetched {len(products)} products, generating embeddings...")
    
    for i, product in enumerate(products):
        try:
            # Generate text embedding from title + category
            text = f"{product['title']} {product['category']}"
            embedding = await clip_model.encode_text(text)
            
            # Add to FAISS index
            faiss_index.add_product(embedding, product)
            
            if (i + 1) % 10 == 0:
                logger.info(f"Indexed {i + 1}/{len(products)} products")
        
        except Exception as e:
            logger.error(f"Error indexing product {product.get('product_id')}: {e}")
    
    logger.info(f"Successfully indexed {len(products)} products")


# Singleton instance
_fetcher_instance: Optional[ProductFetcher] = None


def get_product_fetcher(platform: str = 'dummy') -> ProductFetcher:
    """Get global product fetcher instance"""
    global _fetcher_instance
    if _fetcher_instance is None:
        _fetcher_instance = ProductFetcherFactory.create(platform)
    return _fetcher_instance
