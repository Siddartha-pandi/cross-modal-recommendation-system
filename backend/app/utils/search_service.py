"""
Enhanced Search Service
Integrates CLIP encoding, e-commerce fetching, and ranking.
No database - all operations are in-memory/ephemeral.
"""

import asyncio
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from PIL import Image
import logging
import hashlib
import time
import re

from app.models.clip_model import CLIPModel
from app.models.visual_sentiment import VisualSentimentAnalyzer
from app.models.occasion_mood import OccasionMoodAnalyzer, ContextProfile
from app.utils.ecommerce_fetchers import EcommerceFetcher
from app.utils.image_downloader import get_image_downloader
from app.utils.deduplicator import get_deduplicator
from app.utils.cache import get_cache

logger = logging.getLogger(__name__)

class SearchService:
    """
    Main search service that orchestrates:
    1. E-commerce data fetching
    2. Image downloading
    3. CLIP encoding
    4. Late fusion scoring
    5. Deduplication
    6. Ranking
    """
    
    def __init__(self, clip_model: CLIPModel, ecommerce_config: Optional[Dict] = None):
        self.clip_model = clip_model
        self.ecommerce_fetcher = EcommerceFetcher(ecommerce_config or {})
        self.image_downloader = get_image_downloader()
        self.deduplicator = get_deduplicator()
        self.cache = get_cache()
        self.sentiment_analyzer = VisualSentimentAnalyzer()
        self.occasion_analyzer = OccasionMoodAnalyzer()
        
        logger.info("Search service initialized with sentiment and occasion analysis")
    
    def _preprocess_query(self, text: str) -> str:
        """Clean and normalize text query for better CLIP encoding"""
        if not text:
            return text
        
        # Convert to lowercase
        text = text.lower().strip()
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Expand common abbreviations for fashion
        abbreviations = {
            'tshirt': 't-shirt',
            't shirt': 't-shirt',
            'jkt': 'jacket',
            'pant': 'pants',
            'sunglass': 'sunglasses',
            'watches': 'watch',
            'shoes': 'shoe',
            'bags': 'bag',
            'jewellery': 'jewelry',
            'jewlery': 'jewelry'
        }
        
        for abbr, full in abbreviations.items():
            text = text.replace(abbr, full)
        
        # Add descriptive context for better CLIP understanding
        # CLIP works better with full phrases
        if len(text.split()) == 1:
            # Single word queries - add context
            category_context = {
                'watch': 'a wrist watch',
                'bag': 'a handbag or backpack',
                'shoe': 'a pair of shoes',
                'dress': 'a women\'s dress',
                'shirt': 'a shirt or top',
                'jacket': 'a jacket or coat',
                'ring': 'a ring or jewelry',
                'bracelet': 'a bracelet or jewelry',
                'necklace': 'a necklace or jewelry',
                'sunglasses': 'sunglasses or eyewear'
            }
            
            for key, context in category_context.items():
                if key in text:
                    text = context
                    break
        
        return text
    
    def _generate_query_hash(self, text: Optional[str], image_data: Optional[bytes]) -> str:
        """Generate hash for caching search results"""
        hash_input = ""
        if text:
            hash_input += text
        if image_data:
            hash_input += hashlib.md5(image_data).hexdigest()
        
        return hashlib.md5(hash_input.encode()).hexdigest()
    
    async def search(
        self,
        text_query: Optional[str] = None,
        image_query: Optional[Image.Image] = None,
        priority: Dict[str, float] = None,
        top_k: int = 20,
        sources: Optional[List[str]] = None,
        use_cache: bool = True,
        enable_sentiment_scoring: bool = True,
        enable_occasion_ranking: bool = True,
        context: Optional[ContextProfile] = None
    ) -> Dict[str, Any]:
        """
        Perform multimodal search with live e-commerce data.
        
        Args:
            text_query: Optional text search query
            image_query: Optional image search query (PIL Image)
            priority: Dict with 'image' and 'text' weights (default: {'image': 0.6, 'text': 0.4})
            top_k: Number of results to return
            sources: List of e-commerce sources to search (default: all)
            use_cache: Whether to use cached results
        
        Returns:
            Dict with results, metadata, and timing info
        """
        start_time = time.time()
        
        # Validate input
        if not text_query and not image_query:
            raise ValueError("At least one of text_query or image_query must be provided")
        
        # Set default priorities
        if priority is None:
            priority = {'image': 0.6, 'text': 0.4}
        
        image_weight = priority.get('image', 0.6)
        text_weight = priority.get('text', 0.4)
        
        # Normalize weights
        total_weight = image_weight + text_weight
        if total_weight > 0:
            image_weight /= total_weight
            text_weight /= total_weight
        
        logger.info(f"Search query - Text: '{text_query}', Image: {image_query is not None}")
        logger.info(f"Weights - Image: {image_weight:.2f}, Text: {text_weight:.2f}")
        
        # Parse context from query if not provided
        if enable_occasion_ranking and context is None and text_query:
            context = self.occasion_analyzer.parse_context_from_query(text_query)
            logger.info(f"Parsed context: {context.to_dict()}")
        
        # Step 1: Encode query
        query_encoding_start = time.time()
        
        image_embedding = None
        text_embedding = None
        
        if image_query:
            image_embedding = await self.clip_model.encode_image(image_query)
            logger.info(f"Encoded image query: shape {image_embedding.shape}")
        
        if text_query:
            # Preprocess query for better CLIP understanding
            processed_query = self._preprocess_query(text_query)
            logger.info(f"Preprocessed query: '{text_query}' -> '{processed_query}'")
            text_embedding = await self.clip_model.encode_text(processed_query)
            logger.info(f"Encoded text query: shape {text_embedding.shape}")
        
        # Fuse embeddings if both exist
        if image_embedding is not None and text_embedding is not None:
            query_embedding = await self.clip_model.fuse_embeddings(
                image_embedding=image_embedding,
                text_embedding=text_embedding,
                image_weight=image_weight,
                text_weight=text_weight,
                fusion_method="weighted_avg"
            )
        elif image_embedding is not None:
            query_embedding = image_embedding
        else:
            query_embedding = text_embedding
        
        query_encoding_time = time.time() - query_encoding_start
        logger.info(f"Query encoding took {query_encoding_time:.3f}s")
        
        # Step 2: Fetch products from e-commerce sources
        fetch_start = time.time()
        
        # Determine search strategy based on input modalities
        search_text = text_query or "products"  # Use generic term if no text
        
        # When both image and text are provided, fetch more products for better matching
        fetch_count_per_source = 30 if (image_query and text_query) else 15
        
        if sources:
            raw_products = await self.ecommerce_fetcher.search_specific(
                search_text, sources, max_results_per_source=fetch_count_per_source
            )
        else:
            raw_products = await self.ecommerce_fetcher.search_all(
                search_text, max_results_per_source=fetch_count_per_source
            )
        
        fetch_time = time.time() - fetch_start
        logger.info(f"Fetched {len(raw_products)} products in {fetch_time:.3f}s")
        
        if not raw_products:
            return {
                "results": [],
                "meta": {
                    "num_candidates": 0,
                    "query_time": time.time() - start_time,
                    "fetch_time": fetch_time,
                    "encoding_time": 0,
                    "ranking_time": 0
                }
            }
        
        # Step 3: Download product images
        download_start = time.time()
        
        product_dicts = [p.to_dict() for p in raw_products]
        urls = [p['image_url'] for p in product_dicts if p.get('image_url')]
        
        image_map = await self.image_downloader.download_images_batch(urls)
        
        download_time = time.time() - download_start
        logger.info(f"Downloaded images in {download_time:.3f}s")
        
        # Step 4: Encode product images in batch
        encoding_start = time.time()
        
        valid_products = []
        valid_images = []
        image_hashes = []
        
        for product in product_dicts:
            url = product.get('image_url')
            image = image_map.get(url) if url else None
            
            if image:
                valid_products.append(product)
                valid_images.append(image)
                
                # Compute image hash for deduplication
                from app.utils.deduplicator import ProductDeduplicator
                dedup = ProductDeduplicator()
                img_hash = dedup.compute_image_hash(image)
                image_hashes.append(img_hash)
        
        logger.info(f"Valid products with images: {len(valid_products)}")
        
        if not valid_products:
            return {
                "results": [],
                "meta": {
                    "num_candidates": len(raw_products),
                    "query_time": time.time() - start_time,
                    "fetch_time": fetch_time,
                    "encoding_time": 0,
                    "ranking_time": 0
                }
            }
        
        # Batch encode product images
        product_embeddings = await self.clip_model.encode_batch_images(valid_images)
        
        # Apply visual sentiment analysis
        sentiment_scores = []
        if enable_sentiment_scoring:
            sentiment_start = time.time()
            for image in valid_images:
                sentiment = await self.sentiment_analyzer.analyze_image(image)
                sentiment_scores.append(sentiment)
            sentiment_time = time.time() - sentiment_start
            logger.info(f"Computed sentiment for {len(valid_images)} products in {sentiment_time:.3f}s")
        
        encoding_time = time.time() - encoding_start
        logger.info(f"Encoded {len(valid_images)} products in {encoding_time:.3f}s")
        
        # Step 5: Compute similarity scores with category relevance and visual boosting
        ranking_start = time.time()
        
        # Extract keywords from query for category boosting
        query_keywords = set()
        if text_query:
            query_keywords = set(text_query.lower().split())
        
        similarities = []
        for i, prod_embedding in enumerate(product_embeddings):
            # Compute cosine similarity
            similarity = np.dot(query_embedding, prod_embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(prod_embedding)
            )
            
            base_similarity = float(similarity)
            
            # Category relevance boosting (only for text queries)
            product = valid_products[i]
            title_lower = product.get('title', '').lower()
            category_lower = product.get('category', '').lower()
            
            boost = 1.0
            
            # Text-based boosting
            if text_query:
                for keyword in query_keywords:
                    if len(keyword) > 2:  # Ignore very short words
                        if keyword in title_lower:
                            boost += 0.15  # Boost for title match
                        if keyword in category_lower:
                            boost += 0.10  # Boost for category match
            
            # Image-based boosting - enhance high similarity matches
            if image_query:
                # Progressive boost for strong visual matches
                if base_similarity > 0.85:
                    boost += 0.25  # Very strong match
                elif base_similarity > 0.75:
                    boost += 0.20  # Strong match
                elif base_similarity > 0.65:
                    boost += 0.15  # Good match
                elif base_similarity > 0.55:
                    boost += 0.10  # Moderate match
                
                # Additional boost if both image and text query present (multimodal)
                if text_query and base_similarity > 0.60:
                    boost += 0.10  # Multimodal bonus
            
            # Cap boost at reasonable level
            boost = min(boost, 2.0)
            
            similarity = base_similarity * boost
            similarities.append(similarity)
        
        # Add scores to products with enhanced multimodal filtering
        for i, (product, score) in enumerate(zip(valid_products, similarities)):
            product['base_score'] = score
            product['score'] = score
            product['relevance_flags'] = []
            
            title_lower = product.get('title', '').lower()
            desc_lower = product.get('description', '').lower()
            category_lower = product.get('category', '').lower()
            
            # For multimodal queries, apply strict dual-mode filtering
            if image_query and text_query:
                # Extract all query keywords
                query_keywords = set(text_query.lower().split())
                text_match_score = 0
                matched_keywords = []
                
                # Check each keyword for matches
                for keyword in query_keywords:
                    if len(keyword) > 2:  # Ignore very short words like "a", "is", etc.
                        keyword_found = False
                        
                        # Title match (highest weight)
                        if keyword in title_lower:
                            text_match_score += 3
                            keyword_found = True
                            matched_keywords.append(keyword)
                        # Category match (medium weight)
                        elif keyword in category_lower:
                            text_match_score += 2
                            keyword_found = True
                            matched_keywords.append(keyword)
                        # Description match (lower weight)
                        elif keyword in desc_lower:
                            text_match_score += 1
                            keyword_found = True
                            matched_keywords.append(keyword)
                
                # Calculate text relevance ratio
                total_keywords = len([k for k in query_keywords if len(k) > 2])
                text_relevance_ratio = text_match_score / max(total_keywords * 3, 1)  # Normalize to 0-1
                
                # Strict filtering: Both image similarity AND text match required
                # If visual similarity is good (>0.60) but NO text match → heavy penalty
                if text_match_score == 0:
                    # No keywords matched at all - strong penalty
                    if score < 0.80:  # Only keep if extremely high visual match
                        product['score'] *= 0.3  # Reduce to 30% of original
                        product['relevance_flags'].append('low_text_match')
                        logger.debug(f"Heavy penalty for '{product.get('title')}' - zero text match (score: {score:.3f} -> {product['score']:.3f})")
                elif text_match_score < 2:
                    # Weak text match - moderate penalty
                    product['score'] *= 0.6  # Reduce to 60%
                    product['relevance_flags'].append('weak_text_match')
                    logger.debug(f"Moderate penalty for '{product.get('title')}' - weak text match")
                else:
                    # Good text match - apply bonus
                    text_bonus = min(text_relevance_ratio * 0.3, 0.3)  # Up to 30% bonus
                    product['score'] *= (1.0 + text_bonus)
                    product['relevance_flags'].append('strong_multimodal_match')
                
                # Additional visual similarity check
                # If visual match is poor (<0.50) even with text match → penalty
                if score < 0.50:
                    product['score'] *= 0.7
                    product['relevance_flags'].append('low_visual_match')
                    logger.debug(f"Visual penalty for '{product.get('title')}' - low image similarity")
                
                product['text_match_score'] = text_match_score
                product['matched_keywords'] = matched_keywords
                product['text_relevance_ratio'] = text_relevance_ratio
            
            # For text-only queries, ensure strong keyword matching
            elif text_query and not image_query:
                query_keywords = set(text_query.lower().split())
                text_match_score = 0
                
                for keyword in query_keywords:
                    if len(keyword) > 2:
                        if keyword in title_lower:
                            text_match_score += 3
                        elif keyword in category_lower:
                            text_match_score += 2
                        elif keyword in desc_lower:
                            text_match_score += 1
                
                # Boost products with strong text matches
                if text_match_score >= 3:
                    product['score'] *= 1.2
                    product['relevance_flags'].append('strong_text_match')
                elif text_match_score == 0:
                    product['score'] *= 0.5
                    product['relevance_flags'].append('weak_text_match')
            
            # For image-only queries, rely on visual similarity
            elif image_query and not text_query:
                if score > 0.70:
                    product['relevance_flags'].append('strong_visual_match')
                elif score < 0.40:
                    product['score'] *= 0.8
                    product['relevance_flags'].append('weak_visual_match')
            
            # Apply sentiment scoring boost
            if enable_sentiment_scoring and i < len(sentiment_scores):
                sentiment = sentiment_scores[i]
                sentiment_boost = self.sentiment_analyzer.compute_sentiment_boost(sentiment)
                product['score'] *= sentiment_boost
                product['sentiment'] = sentiment.to_dict()
                product['sentiment_boost'] = sentiment_boost
        
        # Step 6: Apply occasion-aware ranking
        if enable_occasion_ranking and context and (context.occasion or context.mood):
            occasion_start = time.time()
            
            # Get base scores
            base_scores = [p['score'] for p in valid_products]
            
            # Rank by context
            ranked_products = self.occasion_analyzer.rank_products_by_context(
                valid_products, context, base_scores
            )
            
            # Update products with occasion scores
            valid_products = []
            for product, occasion_score in ranked_products:
                product['score'] = occasion_score.final_score
                product['occasion_score'] = {
                    'base_relevance': occasion_score.base_relevance,
                    'occasion_boost': occasion_score.occasion_boost,
                    'mood_boost': occasion_score.mood_boost,
                    'context_boost': occasion_score.context_boost,
                    'matched_attributes': occasion_score.matched_attributes,
                    'explanation': occasion_score.explanation
                }
                valid_products.append(product)
            
            occasion_time = time.time() - occasion_start
            logger.info(f"Occasion-aware ranking took {occasion_time:.3f}s")
        
        # Step 7: Deduplicate
        valid_products = self.deduplicator.deduplicate_by_image_hash(
            valid_products, image_hashes
        )
        
        # Step 8: Generate match tags
        for product in valid_products:
            product['match_tags'] = self._generate_match_tags(
                product, text_query, product['score']
            )
        
        # Step 9: Sort by score and get top K
        valid_products.sort(key=lambda x: x['score'], reverse=True)
        top_results = valid_products[:top_k]
        
        ranking_time = time.time() - ranking_start
        total_time = time.time() - start_time
        
        logger.info(f"Ranking took {ranking_time:.3f}s")
        logger.info(f"Total search time: {total_time:.3f}s")
        
        return {
            "results": top_results,
            "meta": {
                "num_candidates": len(raw_products),
                "num_valid": len(valid_products),
                "num_returned": len(top_results),
                "query_time": total_time,
                "fetch_time": fetch_time,
                "download_time": download_time,
                "encoding_time": encoding_time,
                "ranking_time": ranking_time,
                "sentiment_enabled": enable_sentiment_scoring,
                "occasion_enabled": enable_occasion_ranking,
                "context": context.to_dict() if context else None,
                "weights": {
                    "image": image_weight,
                    "text": text_weight
                }
            }
        }
    
    def _generate_match_tags(
        self, 
        product: Dict, 
        text_query: Optional[str], 
        score: float
    ) -> List[str]:
        """Generate match explanation tags"""
        tags = []
        
        # Score-based tags
        if score > 0.9:
            tags.append("excellent-match")
        elif score > 0.8:
            tags.append("great-match")
        elif score > 0.7:
            tags.append("good-match")
        
        # Text-based tags
        if text_query:
            title_lower = product.get('title', '').lower()
            desc_lower = product.get('description', '').lower()
            query_lower = text_query.lower()
            
            if query_lower in title_lower:
                tags.append("title-match")
            
            if query_lower in desc_lower:
                tags.append("description-match")
            
            # Check for color words
            colors = ['red', 'blue', 'green', 'black', 'white', 'yellow', 'pink', 'purple']
            for color in colors:
                if color in query_lower and color in title_lower:
                    tags.append("color-match")
                    break
            
            # Check for style words
            styles = ['elegant', 'casual', 'formal', 'modern', 'vintage', 'classic']
            for style in styles:
                if style in query_lower and (style in title_lower or style in desc_lower):
                    tags.append("style-match")
                    break
        
        # Visual similarity tag
        if score > 0.75:
            tags.append("visual-match")
        
        return tags


# Global service instance
_global_search_service = None

def get_search_service(clip_model: CLIPModel) -> SearchService:
    """Get or create global search service instance"""
    global _global_search_service
    if _global_search_service is None:
        _global_search_service = SearchService(clip_model)
    return _global_search_service
