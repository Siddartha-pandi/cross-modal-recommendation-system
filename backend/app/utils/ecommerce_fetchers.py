"""
E-commerce Product Fetchers - FREE APIs Version
Uses 100% FREE public APIs - NO authentication required:
- DummyJSON API: Free product data (https://dummyjson.com)
- FakeStoreAPI: Alternative free products (https://fakestoreapi.com)
- Platzi Fake Store API: Free product data (https://api.escuelajs.co/api/v1)
- No signup, no API keys, completely free!
"""

import asyncio
import aiohttp
import httpx
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
import logging
import json
import re
from urllib.parse import quote_plus, urljoin
import random

logger = logging.getLogger(__name__)

class Product:
    """Product data model"""
    def __init__(
        self,
        product_id: str,
        title: str,
        description: str,
        image_url: str,
        price: float,
        source: str,
        buy_url: str,
        category: Optional[str] = None,
        brand: Optional[str] = None,
        rating: Optional[float] = None
    ):
        self.product_id = product_id
        self.title = title
        self.description = description
        self.image_url = image_url
        self.price = price
        self.source = source
        self.buy_url = buy_url
        self.category = category
        self.brand = brand
        self.rating = rating

    def to_dict(self) -> Dict[str, Any]:
        return {
            "product_id": self.product_id,
            "title": self.title,
            "description": self.description,
            "image_url": self.image_url,
            "price": self.price,
            "source": self.source,
            "buy_url": self.buy_url,
            "category": self.category,
            "brand": self.brand,
            "rating": self.rating
        }


class AmazonFetcher:
    """Fetch products using DummyJSON API - 100% FREE, no signup!"""
    
    def __init__(self, access_key: Optional[str] = None, secret_key: Optional[str] = None, partner_tag: Optional[str] = None):
        self.base_url = "https://dummyjson.com"
        self.enabled = True
    
    async def search(self, query: str, max_results: int = 20) -> List[Product]:
        """Search products using DummyJSON free API"""
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                # Get all products (DummyJSON has 194 products total)
                response = await client.get(f"{self.base_url}/products", params={"limit": 0, "skip": 0})
                response.raise_for_status()
                data = response.json()
                
                # Filter by query with smart matching
                query_lower = query.lower().strip()
                query_keywords = set(query_lower.split())
                
                scored_products = []
                
                for item in data.get("products", []):
                    title = item.get("title", "")
                    desc = item.get("description", "")
                    category = item.get("category", "")
                    
                    title_lower = title.lower()
                    desc_lower = desc.lower()
                    category_lower = category.lower()
                    
                    # Score based on keyword matches
                    score = 0
                    
                    # Exact phrase match (highest priority)
                    if query_lower in title_lower:
                        score += 100
                    elif query_lower in desc_lower:
                        score += 50
                    
                    # Individual keyword matches
                    for keyword in query_keywords:
                        if len(keyword) > 2:  # Ignore very short words
                            if keyword in title_lower:
                                score += 30
                            if keyword in category_lower:
                                score += 20
                            if keyword in desc_lower:
                                score += 10
                    
                    # Only include if there's some relevance
                    if score > 0:
                        scored_products.append((score, item))
                
                # Sort by score descending
                scored_products.sort(key=lambda x: x[0], reverse=True)
                
                products = []
                for score, item in scored_products[:max_results]:
                    products.append(Product(
                        product_id=f"amazon_{item.get('id')}",
                        title=item.get("title", ""),
                        description=item.get("description", ""),
                        image_url=item.get("thumbnail", item.get("images", [""])[0] if item.get("images") else ""),
                        price=float(item.get("price", 0)),
                        source="Amazon",
                        buy_url=f"https://www.amazon.com/s?k={quote_plus(item.get('title', ''))}",
                        category=item.get("category", "General"),
                        brand=item.get("brand", "Generic"),
                        rating=float(item.get("rating", 4.0))
                    ))
                
                # If no matches, return top rated products as fallback
                if not products:
                    all_products = sorted(
                        data.get("products", []),
                        key=lambda x: x.get("rating", 0),
                        reverse=True
                    )
                    for item in all_products[:max_results]:
                        products.append(Product(
                            product_id=f"amazon_{item.get('id')}",
                            title=item.get("title", ""),
                            description=item.get("description", ""),
                            image_url=item.get("thumbnail", item.get("images", [""])[0] if item.get("images") else ""),
                            price=float(item.get("price", 0)),
                            source="Amazon",
                            buy_url=f"https://www.amazon.com/s?k={quote_plus(item.get('title', ''))}",
                            category=item.get("category", "General"),
                            brand=item.get("brand", "Generic"),
                            rating=float(item.get("rating", 4.0))
                        ))
                
                logger.info(f"DummyJSON API returned {len(products)} products for query '{query}'")
                return products
                
        except Exception as e:
            logger.error(f"DummyJSON API error: {e}")
            return []


class FlipkartFetcher:
    """Fetch products using FakeStoreAPI - 100% FREE, no signup!"""
    
    def __init__(self, api_key: Optional[str] = None, affiliate_id: Optional[str] = None):
        self.base_url = "https://fakestoreapi.com"
        self.enabled = True
    
    async def search(self, query: str, max_results: int = 20) -> List[Product]:
        """Search products using FakeStoreAPI free API"""
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(f"{self.base_url}/products")
                response.raise_for_status()
                data = response.json()
                
                # Duplicate products with variations for more data
                expanded_data = []
                for item in data:
                    expanded_data.append(item)  # Original
                    # Add 4 variations with slight price changes
                    for i in range(1, 5):
                        variant = item.copy()
                        variant['id'] = f"{item['id']}_v{i}"
                        variant['price'] = round(item.get('price', 0) * (0.9 + i * 0.05), 2)
                        variant['title'] = f"{item.get('title', '')} - Variant {i}"
                        expanded_data.append(variant)
                
                data = expanded_data
                
                query_lower = query.lower()
                products = []
                
                for item in data:
                    title = item.get("title", "")
                    desc = item.get("description", "")
                    
                    if query_lower in title.lower() or query_lower in desc.lower():
                        products.append(Product(
                            product_id=f"flipkart_{item.get('id')}",
                            title=title,
                            description=desc,
                            image_url=item.get("image", ""),
                            price=float(item.get("price", 0)),
                            source="Flipkart",
                            buy_url=f"https://www.flipkart.com/search?q={quote_plus(title)}",
                            category=item.get("category", "General"),
                            brand="FakeStore",
                            rating=float(item.get("rating", {}).get("rate", 4.0))
                        ))
                
                if not products:
                    for item in data[:max_results]:
                        products.append(Product(
                            product_id=f"flipkart_{item.get('id')}",
                            title=item.get("title", ""),
                            description=item.get("description", ""),
                            image_url=item.get("image", ""),
                            price=float(item.get("price", 0)),
                            source="Flipkart",
                            buy_url=f"https://www.flipkart.com/search?q={quote_plus(item.get('title', ''))}",
                            category=item.get("category", "General"),
                            brand="FakeStore",
                            rating=float(item.get("rating", {}).get("rate", 4.0))
                        ))
                
                logger.info(f"FakeStoreAPI returned {len(products[:max_results])} products")
                return products[:max_results]
                
        except Exception as e:
            logger.error(f"FakeStoreAPI error: {e}")
            return []


class PlatziFetcher:
    """Fetch products using Platzi Fake Store API - 100% FREE, no signup!"""

    def __init__(self):
        self.base_url = "https://api.escuelajs.co/api/v1"
        self.enabled = True

    def _extract_image(self, images: Any) -> str:
        if isinstance(images, list) and images:
            for image in images:
                if isinstance(image, str) and image.strip():
                    return image
        if isinstance(images, str):
            return images
        return ""

    async def search(self, query: str, max_results: int = 20) -> List[Product]:
        """Search products using Platzi Fake Store API"""
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                params = {"limit": max(max_results, 50), "offset": 0}
                response = await client.get(f"{self.base_url}/products", params=params)
                response.raise_for_status()
                data = response.json()

                query_lower = query.lower().strip()
                products = []

                for item in data:
                    title = item.get("title", "")
                    desc = item.get("description", "")
                    category_name = (item.get("category") or {}).get("name", "")

                    title_lower = title.lower()
                    desc_lower = desc.lower()
                    category_lower = category_name.lower()

                    if query_lower in title_lower or query_lower in desc_lower or query_lower in category_lower:
                        products.append(Product(
                            product_id=f"platzi_{item.get('id')}",
                            title=title,
                            description=desc,
                            image_url=self._extract_image(item.get("images", [])),
                            price=float(item.get("price", 0)),
                            source="Platzi",
                            buy_url=f"{self.base_url}/products/{item.get('id')}",
                            category=category_name or "General",
                            brand="Platzi",
                            rating=4.1
                        ))

                if not products:
                    for item in data[:max_results]:
                        products.append(Product(
                            product_id=f"platzi_{item.get('id')}",
                            title=item.get("title", ""),
                            description=item.get("description", ""),
                            image_url=self._extract_image(item.get("images", [])),
                            price=float(item.get("price", 0)),
                            source="Platzi",
                            buy_url=f"{self.base_url}/products/{item.get('id')}",
                            category=(item.get("category") or {}).get("name", "General"),
                            brand="Platzi",
                            rating=4.1
                        ))

                logger.info(f"Platzi API returned {len(products[:max_results])} products")
                return products[:max_results]

        except Exception as e:
            logger.error(f"Platzi API error: {e}")
            return []


class MyntraFetcher:
    """Fetch products using DummyJSON Fashion APIs - 100% FREE"""
    
    async def search(self, query: str, max_results: int = 20) -> List[Product]:
        """Search for fashion/clothing products from multiple categories"""
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                # Map common queries to specific categories
                query_lower = query.lower()
                
                category_map = {
                    'shirt': ['mens-shirts', 'tops'],
                    'dress': ['womens-dresses'],
                    'shoe': ['mens-shoes', 'womens-shoes'],
                    'bag': ['womens-bags'],
                    'watch': ['mens-watches', 'womens-watches'],
                    'jewelry': ['womens-jewellery'],
                    'jewellery': ['womens-jewellery'],
                    'ring': ['womens-jewellery'],
                    'necklace': ['womens-jewellery'],
                    'bracelet': ['womens-jewellery'],
                    'sunglasses': ['sunglasses'],
                    'glasses': ['sunglasses']
                }
                
                # Determine which categories to fetch
                target_categories = []
                for keyword, categories in category_map.items():
                    if keyword in query_lower:
                        target_categories.extend(categories)
                
                # If no specific match, use all fashion categories
                if not target_categories:
                    target_categories = [
                        "womens-dresses",
                        "womens-shoes",
                        "mens-shirts",
                        "mens-shoes",
                        "womens-bags",
                        "womens-jewellery",
                        "mens-watches",
                        "womens-watches",
                        "sunglasses",
                        "tops"
                    ]
                else:
                    # Remove duplicates
                    target_categories = list(set(target_categories))
                
                all_products = []
                
                # Fetch from targeted categories
                for category in target_categories[:8]:  # Limit to 8 categories
                    try:
                        response = await client.get(f"https://dummyjson.com/products/category/{category}")
                        if response.status_code == 200:
                            data = response.json()
                            
                            for item in data.get("products", []):
                                all_products.append(Product(
                                    product_id=f"myntra_{category}_{item.get('id')}",
                                    title=item.get("title", ""),
                                    description=item.get("description", ""),
                                    image_url=item.get("thumbnail", item.get("images", [""])[0] if item.get("images") else ""),
                                    price=float(item.get("price", 0)),
                                    source="Myntra",
                                    buy_url=f"https://www.myntra.com/{quote_plus(item.get('title', ''))}",
                                    category=category.replace('-', ' ').title(),
                                    brand=item.get("brand", "Myntra"),
                                    rating=float(item.get("rating", 4.2))
                                ))
                    except Exception as cat_error:
                        logger.warning(f"Error fetching category {category}: {cat_error}")
                        continue
                
                logger.info(f"Myntra (DummyJSON) returned {len(all_products[:max_results])} fashion products")
                return all_products[:max_results]
        except Exception as e:
            logger.error(f"Myntra fetcher error: {e}")
        return []


class IKEAFetcher:
    """Fetch products using DummyJSON Home & Lifestyle APIs - 100% FREE"""
    
    async def search(self, query: str, max_results: int = 20) -> List[Product]:
        """Search for home/furniture/lifestyle products"""
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                home_categories = [
                    "furniture",
                    "home-decoration",
                    "kitchen-accessories",
                    "groceries"
                ]
                
                all_products = []
                
                for category in home_categories:
                    try:
                        response = await client.get(f"https://dummyjson.com/products/category/{category}")
                        if response.status_code == 200:
                            data = response.json()
                            
                            for item in data.get("products", []):
                                all_products.append(Product(
                                    product_id=f"ikea_{category}_{item.get('id')}",
                                    title=item.get("title", ""),
                                    description=item.get("description", ""),
                                    image_url=item.get("thumbnail", item.get("images", [""])[0] if item.get("images") else ""),
                                    price=float(item.get("price", 0)),
                                    source="IKEA",
                                    buy_url=f"https://www.ikea.com/search/?q={quote_plus(item.get('title', ''))}",
                                    category=category.replace('-', ' ').title(),
                                    brand="IKEA",
                                    rating=float(item.get("rating", 4.5))
                                ))
                    except Exception as cat_error:
                        logger.warning(f"Error fetching category {category}: {cat_error}")
                        continue
                
                logger.info(f"IKEA (DummyJSON) returned {len(all_products[:max_results])} home products")
                return all_products[:max_results]
        except Exception as e:
            logger.error(f"IKEA fetcher error: {e}")
        return []


class MeeshoFetcher:
    """Fetch products using DummyJSON Multiple Categories - 100% FREE"""
    
    async def search(self, query: str, max_results: int = 20) -> List[Product]:
        """Search for budget-friendly fashion and lifestyle products"""
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                # Fetch from ALL budget-friendly categories
                budget_categories = [
                    "smartphones",
                    "laptops",
                    "fragrances",
                    "skin-care",
                    "groceries",
                    "home-decoration",
                    "kitchen-accessories",
                    "tablets",
                    "mobile-accessories"
                ]
                
                all_products = []
                
                for category in budget_categories:  # Use ALL categories
                    try:
                        response = await client.get(f"https://dummyjson.com/products/category/{category}")
                        if response.status_code == 200:
                            data = response.json()
                            
                            for item in data.get("products", []):  # Take ALL products
                                # Reduce prices for "budget" feel
                                price = float(item.get("price", 0)) * 0.6
                                
                                all_products.append(Product(
                                    product_id=f"meesho_{category}_{item.get('id')}",
                                    title=item.get("title", ""),
                                    description=item.get("description", ""),
                                    image_url=item.get("thumbnail", item.get("images", [""])[0] if item.get("images") else ""),
                                    price=round(price, 2),
                                    source="Meesho",
                                    buy_url=f"https://www.meesho.com/search?q={quote_plus(item.get('title', ''))}",
                                    category=category.replace('-', ' ').title(),
                                    brand=item.get("brand", "Meesho"),
                                    rating=float(item.get("rating", 4.0))
                                ))
                    except Exception as cat_error:
                        logger.warning(f"Error fetching category {category}: {cat_error}")
                        continue
                
                logger.info(f"Meesho (DummyJSON) returned {len(all_products[:max_results])} budget products")
                return all_products[:max_results]
        except Exception as e:
            logger.error(f"Meesho fetcher error: {e}")
        return []


class ShopifyFetcher:
    """Fetch products from Shopify stores using Storefront API"""
    
    def __init__(self, shop_name: Optional[str] = None, api_key: Optional[str] = None):
        """
        Initialize Shopify fetcher.
        
        Args:
            shop_name: Shopify store name (e.g., "your-store" from your-store.myshopify.com)
            api_key: Storefront API access token (optional for public stores)
        """
        self.shop_name = shop_name or "demo-store"  # Demo store for testing
        self.api_key = api_key
        self.base_url = f"https://{self.shop_name}.myshopify.com/api/2024-01/graphql.json"
        self.enabled = True
    
    async def search(self, query: str, max_results: int = 20) -> List[Product]:
        """Search products from Shopify using GraphQL API"""
        try:
            # Fallback to public demo products if no auth
            if not self.api_key:
                logger.info(f"Shopify fetcher: No API key configured, using demo data")
                return await self._fetch_demo_products(query, max_results)
            
            async with httpx.AsyncClient(timeout=15.0) as client:
                # GraphQL query to search products
                query_str = """
                {
                    products(first: %d, query: "%s") {
                        edges {
                            node {
                                id
                                title
                                description
                                priceRange {
                                    minVariantPrice {
                                        amount
                                    }
                                }
                                images(first: 1) {
                                    edges {
                                        node {
                                            url
                                        }
                                    }
                                }
                                vendor
                                productType
                                handle
                            }
                        }
                    }
                }
                """ % (max_results, query.lower())
                
                headers = {
                    "X-Shopify-Storefront-Access-Token": self.api_key,
                    "Content-Type": "application/json"
                }
                
                response = await client.post(
                    self.base_url,
                    json={"query": query_str},
                    headers=headers
                )
                
                if response.status_code == 200:
                    data = response.json()
                    products = []
                    
                    if "data" in data and "products" in data["data"]:
                        for edge in data["data"]["products"].get("edges", []):
                            node = edge.get("node", {})
                            
                            # Extract price
                            price = 0
                            try:
                                price = float(node.get("priceRange", {})
                                            .get("minVariantPrice", {})
                                            .get("amount", 0))
                            except (ValueError, TypeError):
                                price = 29.99  # Default price
                            
                            # Extract image
                            image_url = ""
                            try:
                                image_url = (node.get("images", {})
                                           .get("edges", [{}])[0]
                                           .get("node", {})
                                           .get("url", ""))
                            except (IndexError, KeyError):
                                image_url = ""
                            
                            products.append(Product(
                                product_id=f"shopify_{node.get('id', '').split('/')[-1]}",
                                title=node.get("title", ""),
                                description=node.get("description", ""),
                                image_url=image_url,
                                price=price,
                                source="Shopify",
                                buy_url=f"https://{self.shop_name}.myshopify.com/products/{node.get('handle', '')}",
                                category=node.get("productType", "General"),
                                brand=node.get("vendor", "Shopify"),
                                rating=4.5  # Shopify doesn't provide ratings in basic query
                            ))
                    
                    logger.info(f"Shopify returned {len(products)} products")
                    return products
                else:
                    logger.warning(f"Shopify API error: Status {response.status_code}")
                    return await self._fetch_demo_products(query, max_results)
                    
        except Exception as e:
            logger.error(f"Shopify fetcher error: {e}")
            return await self._fetch_demo_products(query, max_results)
    
    async def _fetch_demo_products(self, query: str, max_results: int) -> List[Product]:
        """Fallback: Fetch demo Shopify products for testing"""
        # Demo products representing typical Shopify store items
        demo_products = [
            {
                "id": "gid://shopify/Product/1",
                "title": "Premium Cotton T-Shirt",
                "description": "High-quality organic cotton t-shirt",
                "price": 29.99,
                "image": "https://via.placeholder.com/300?text=Cotton+TShirt",
                "vendor": "Fashion Brand",
                "handle": "cotton-tshirt"
            },
            {
                "id": "gid://shopify/Product/2",
                "title": "Classic Denim Jeans",
                "description": "Comfortable and stylish denim jeans",
                "price": 59.99,
                "image": "https://via.placeholder.com/300?text=Denim+Jeans",
                "vendor": "Denim Co",
                "handle": "classic-jeans"
            },
            {
                "id": "gid://shopify/Product/3",
                "title": "Summer Linen Dress",
                "description": "Light and breathable linen dress",
                "price": 49.99,
                "image": "https://via.placeholder.com/300?text=Linen+Dress",
                "vendor": "Summer Collection",
                "handle": "summer-dress"
            },
            {
                "id": "gid://shopify/Product/4",
                "title": "Leather Crossbody Bag",
                "description": "Genuine leather crossbody bag",
                "price": 79.99,
                "image": "https://via.placeholder.com/300?text=Leather+Bag",
                "vendor": "Leather Works",
                "handle": "crossbody-bag"
            },
            {
                "id": "gid://shopify/Product/5",
                "title": "Canvas Sneakers",
                "description": "Casual canvas sneakers",
                "price": 44.99,
                "image": "https://via.placeholder.com/300?text=Canvas+Sneakers",
                "vendor": "Shoe Brand",
                "handle": "canvas-sneakers"
            },
        ]
        
        # Filter by query
        query_lower = query.lower()
        filtered = [
            p for p in demo_products
            if query_lower in p["title"].lower() or query_lower in p["description"].lower()
        ]
        
        # If no matches, return all
        if not filtered:
            filtered = demo_products
        
        products = []
        for item in filtered[:max_results]:
            products.append(Product(
                product_id=f"shopify_{item['id'].split('/')[-1]}",
                title=item["title"],
                description=item["description"],
                image_url=item["image"],
                price=item["price"],
                source="Shopify",
                buy_url=f"https://shopify-demo.myshopify.com/products/{item['handle']}",
                category="Fashion",
                brand=item["vendor"],
                rating=4.5
            ))
        
        logger.info(f"Shopify (demo mode) returned {len(products)} demo products")
        return products


class EcommerceFetcher:
    """
    Main coordinator for fetching products from multiple e-commerce sources.
    No database - all data fetched live on each request.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        config = config or {}
        
        # Initialize fetchers
        self.amazon = AmazonFetcher(
            access_key=config.get("amazon_access_key"),
            secret_key=config.get("amazon_secret_key"),
            partner_tag=config.get("amazon_partner_tag")
        )
        
        self.flipkart = FlipkartFetcher(
            api_key=config.get("flipkart_api_key"),
            affiliate_id=config.get("flipkart_affiliate_id")
        )
        
        self.myntra = MyntraFetcher()
        self.ikea = IKEAFetcher()
        self.meesho = MeeshoFetcher()

        # Add Platzi fetcher
        self.platzi = PlatziFetcher()
        
        # Add Shopify fetcher
        self.shopify = ShopifyFetcher(
            shop_name=config.get("shopify_store_name"),
            api_key=config.get("shopify_api_key")
        )
        
        logger.info("E-commerce fetchers initialized (7 sources)")
    
    async def search_all(self, query: str, max_results_per_source: int = 20) -> List[Product]:
        """
        Search all e-commerce sources in parallel and combine results.
        Returns live data - no database storage.
        """
        logger.info(f"Fetching products for query: '{query}' from all sources")
        
        # Execute all searches in parallel
        tasks = [
            self.amazon.search(query, max_results_per_source),
            self.flipkart.search(query, max_results_per_source),
            self.myntra.search(query, max_results_per_source),
            self.ikea.search(query, max_results_per_source),
            self.meesho.search(query, max_results_per_source),
            self.shopify.search(query, max_results_per_source),
            self.platzi.search(query, max_results_per_source)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine all products
        all_products = []
        for result in results:
            if isinstance(result, list):
                all_products.extend(result)
            elif isinstance(result, Exception):
                logger.error(f"Fetcher error: {result}")
        
        logger.info(f"Fetched {len(all_products)} total products from {len(tasks)} sources")
        
        return all_products
    
    async def search_specific(self, query: str, sources: List[str], max_results_per_source: int = 20) -> List[Product]:
        """
        Search specific e-commerce sources.
        """
        logger.info(f"Fetching products from sources: {sources}")
        
        tasks = []
        for source in sources:
            if source.lower() == "amazon":
                tasks.append(self.amazon.search(query, max_results_per_source))
            elif source.lower() == "flipkart":
                tasks.append(self.flipkart.search(query, max_results_per_source))
            elif source.lower() == "myntra":
                tasks.append(self.myntra.search(query, max_results_per_source))
            elif source.lower() == "ikea":
                tasks.append(self.ikea.search(query, max_results_per_source))
            elif source.lower() == "meesho":
                tasks.append(self.meesho.search(query, max_results_per_source))
            elif source.lower() == "shopify":
                tasks.append(self.shopify.search(query, max_results_per_source))
            elif source.lower() == "platzi":
                tasks.append(self.platzi.search(query, max_results_per_source))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        all_products = []
        for result in results:
            if isinstance(result, list):
                all_products.extend(result)
        
        return all_products
