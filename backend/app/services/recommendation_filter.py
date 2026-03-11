"""
Recommendation Filter Service
Post-processing filters for recommendation results.

Implements:
- Deduplication (remove similar/duplicate products)
- Quality filtering (image quality, completeness)
- Category filtering (ensure relevance)
- Diversity filtering (ensure variety in results)
"""
import logging
from typing import List, Set, Tuple, Optional, Any
from collections import defaultdict
import re

import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


class RecommendationFilter:
    """
    Advanced filtering system for recommendation results.
    
    Ensures high-quality, diverse, and relevant recommendations.
    """
    
    def __init__(
        self,
        min_image_size: Tuple[int, int] = (100, 100),
        similarity_threshold: float = 0.95,
        max_per_source: int = 5,
    ):
        """
        Initialize filter with configuration.
        
        Args:
            min_image_size: Minimum acceptable image dimensions (width, height)
            similarity_threshold: Threshold for detecting duplicates (0-1)
            max_per_source: Maximum results from single source
        """
        self.min_image_size = min_image_size
        self.similarity_threshold = similarity_threshold
        self.max_per_source = max_per_source
        
        logger.info("RecommendationFilter initialized")
    
    def filter(
        self,
        ranked_products: List[Any],
        remove_duplicates: bool = True,
        check_quality: bool = True,
        ensure_diversity: bool = True,
        category_filter: Optional[str] = None,
    ) -> List[Any]:
        """
        Apply all filters to ranked products.
        
        Args:
            ranked_products: List of ranked products (RankedProduct objects or dicts)
            remove_duplicates: Remove duplicate products
            check_quality: Filter out low-quality results
            ensure_diversity: Ensure diversity across sources/categories
            category_filter: Optional category to filter by
        
        Returns:
            Filtered list of products
        """
        logger.info(f"Filtering {len(ranked_products)} products...")
        
        filtered = ranked_products.copy()
        
        # Filter 1: Category filtering (if specified)
        if category_filter:
            filtered = self._filter_by_category(filtered, category_filter)
            logger.debug(f"After category filter: {len(filtered)} products")
        
        # Filter 2: Quality check
        if check_quality:
            filtered = self._filter_by_quality(filtered)
            logger.debug(f"After quality filter: {len(filtered)} products")
        
        # Filter 3: Deduplication
        if remove_duplicates:
            filtered = self._remove_duplicates(filtered)
            logger.debug(f"After deduplication: {len(filtered)} products")
        
        # Filter 4: Diversity
        if ensure_diversity:
            filtered = self._ensure_diversity(filtered)
            logger.debug(f"After diversity filter: {len(filtered)} products")
        
        logger.info(f"Filtering complete: {len(ranked_products)} → {len(filtered)} products")
        return filtered
    
    # ─── Filter 1: Category Filtering ───────────────────────────────────────
    
    def _filter_by_category(
        self,
        products: List[Any],
        category: str
    ) -> List[Any]:
        """Filter products by category."""
        category_lower = category.lower()
        
        filtered = []
        for product in products:
            product_category = self._get_category(product)
            
            if product_category and category_lower in product_category.lower():
                filtered.append(product)
        
        return filtered
    
    def _get_category(self, product: Any) -> str:
        """Extract category from product."""
        if hasattr(product, 'product'):
            product = product.product
        
        if hasattr(product, 'category'):
            return str(product.category)
        elif isinstance(product, dict):
            return str(product.get('category', ''))
        
        return ''
    
    # ─── Filter 2: Quality Check ────────────────────────────────────────────
    
    def _filter_by_quality(self, products: List[Any]) -> List[Any]:
        """
        Filter out low-quality products.
        
        Checks:
        - Has valid title
        - Has valid image URL
        - Title is not too short
        - Not spam/junk
        """
        filtered = []
        
        for product in products:
            if self._is_high_quality(product):
                filtered.append(product)
        
        return filtered
    
    def _is_high_quality(self, product: Any) -> bool:
        """Check if product meets quality standards."""
        # Extract product data
        if hasattr(product, 'product'):
            product_data = product.product
        else:
            product_data = product
        
        # Check title
        title = self._get_title(product_data)
        if not title or len(title) < 10:
            logger.debug(f"Rejected: title too short ({title})")
            return False
        
        # Check for spam patterns
        if self._is_spam(title):
            logger.debug(f"Rejected: spam detected ({title})")
            return False
        
        # Check image URL
        image_url = self._get_image_url(product_data)
        if not image_url or not self._is_valid_image_url(image_url):
            logger.debug(f"Rejected: invalid image URL ({image_url})")
            return False
        
        # Check if result is actually a fashion product
        if not self._is_fashion_product(title):
            logger.debug(f"Rejected: not a fashion product ({title})")
            return False
        
        return True
    
    def _get_title(self, product: Any) -> str:
        """Extract title from product."""
        if hasattr(product, 'title'):
            return str(product.title)
        elif isinstance(product, dict):
            return str(product.get('title', ''))
        return ''
    
    def _get_image_url(self, product: Any) -> str:
        """Extract image URL from product."""
        if hasattr(product, 'image_url'):
            return str(product.image_url)
        elif hasattr(product, 'image'):
            return str(product.image)
        elif isinstance(product, dict):
            return str(product.get('image_url', product.get('image', '')))
        return ''
    
    def _is_valid_image_url(self, url: str) -> bool:
        """Check if URL looks like a valid image URL."""
        if not url:
            return False
        
        url_lower = url.lower()
        
        # Check for image extensions or image hosting patterns
        image_patterns = [
            r'\.(jpg|jpeg|png|webp|gif)',
            r'images\.',
            r'/img/',
            r'cloudinary',
            r'imgix',
        ]
        
        return any(re.search(pattern, url_lower) for pattern in image_patterns)
    
    def _is_spam(self, text: str) -> bool:
        """Detect spam patterns."""
        text_lower = text.lower()
        
        spam_patterns = [
            r'click here',
            r'buy now',
            r'limited offer',
            r'free shipping',
            r'http[s]?://',
        ]
        
        return any(re.search(pattern, text_lower) for pattern in spam_patterns)
    
    def _is_fashion_product(self, title: str) -> bool:
        """Check if title indicates a fashion product."""
        title_lower = title.lower()
        
        # Fashion-related keywords
        fashion_keywords = [
            'dress', 'shirt', 'pant', 'jean', 'jacket', 'coat', 'shoe',
            'boot', 'sneaker', 'sandal', 'bag', 'belt', 'watch', 'scarf',
            'blouse', 'top', 'skirt', 'short', 'hoodie', 'sweater', 'tshirt',
            't-shirt', 'kurta', 'kurti', 'saree', 'lehenga', 'ethnic',
            'formal', 'casual', 'party', 'wedding', 'fashion', 'style',
            'women', 'men', 'girl', 'boy', 'kid', 'apparel', 'clothing',
            'wear', 'outfit', 'attire'
        ]
        
        return any(keyword in title_lower for keyword in fashion_keywords)
    
    # ─── Filter 3: Deduplication ────────────────────────────────────────────
    
    def _remove_duplicates(self, products: List[Any]) -> List[Any]:
        """
        Remove duplicate products.
        
        Uses title similarity to detect duplicates.
        """
        if len(products) <= 1:
            return products
        
        filtered = []
        seen_titles: Set[str] = set()
        
        for product in products:
            title = self._get_title(
                product.product if hasattr(product, 'product') else product
            )
            
            # Normalize title for comparison
            normalized_title = self._normalize_title(title)
            
            # Check if similar title already seen
            if not self._is_duplicate_title(normalized_title, seen_titles):
                filtered.append(product)
                seen_titles.add(normalized_title)
        
        return filtered
    
    def _normalize_title(self, title: str) -> str:
        """Normalize title for duplicate detection."""
        # Convert to lowercase
        normalized = title.lower()
        
        # Remove special characters
        normalized = re.sub(r'[^\w\s]', ' ', normalized)
        
        # Remove extra whitespace
        normalized = ' '.join(normalized.split())
        
        # Remove common filler words
        filler_words = {'for', 'the', 'a', 'an', 'with', 'in', 'on', 'at', 'by'}
        words = [w for w in normalized.split() if w not in filler_words]
        normalized = ' '.join(words)
        
        return normalized
    
    def _is_duplicate_title(self, title: str, seen_titles: Set[str]) -> bool:
        """Check if title is duplicate of any seen title."""
        title_words = set(title.split())
        
        for seen in seen_titles:
            seen_words = set(seen.split())
            
            # Compute Jaccard similarity
            if not title_words or not seen_words:
                continue
            
            intersection = title_words & seen_words
            union = title_words | seen_words
            
            jaccard = len(intersection) / len(union)
            
            if jaccard >= self.similarity_threshold:
                return True
        
        return False
    
    # ─── Filter 4: Diversity ────────────────────────────────────────────────
    
    def _ensure_diversity(self, products: List[Any]) -> List[Any]:
        """
        Ensure diversity in results.
        
        Limits number of results from same source/category.
        """
        source_counts = defaultdict(int)
        category_counts = defaultdict(int)
        
        filtered = []
        
        for product in products:
            product_data = product.product if hasattr(product, 'product') else product
            
            source = self._get_source(product_data)
            category = self._get_category(product)
            
            # Check source limit
            if source and source_counts[source] >= self.max_per_source:
                continue
            
            # Add to filtered
            filtered.append(product)
            
            if source:
                source_counts[source] += 1
            if category:
                category_counts[category] += 1
        
        return filtered
    
    def _get_source(self, product: Any) -> str:
        """Extract source/website from product."""
        if hasattr(product, 'source'):
            return str(product.source)
        elif isinstance(product, dict):
            return str(product.get('source', ''))
        return 'Unknown'


# ─── Singleton Instance ──────────────────────────────────────────────────────

recommendation_filter = RecommendationFilter()
