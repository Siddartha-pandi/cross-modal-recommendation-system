"""
Comprehensive Search Service
Integrates CLIP, Fusion, FAISS, and Redis Cache
"""

import hashlib
import time
import logging
from typing import Optional, List, Dict, Any, Tuple
from PIL import Image
import numpy as np

from app.models.clip_model import CLIPModel
from app.models.fusion import FusionEngine, ExplainableRecommender
from app.utils.faiss_index import FAISSIndex
from app.utils.redis_cache import RedisCacheManager

logger = logging.getLogger(__name__)


class SearchService:
    """
    Production-ready search service with caching and fusion
    """
    
    def __init__(
        self,
        clip_model: CLIPModel,
        faiss_index: FAISSIndex,
        cache: RedisCacheManager,
        fusion_engine: FusionEngine = None
    ):
        self.clip_model = clip_model
        self.faiss_index = faiss_index
        self.cache = cache
        self.fusion_engine = fusion_engine or FusionEngine(default_alpha=0.7)
        
        logger.info("SearchService initialized")
    
    async def search(
        self,
        text_query: Optional[str] = None,
        image_query: Optional[Image.Image] = None,
        top_k: int = 10,
        alpha: float = 0.7,
        fusion_method: str = "weighted_avg",
        filters: Optional[Dict] = None,
        diversity_weight: float = 0.0
    ) -> Tuple[List[Dict], Dict[str, Any]]:
        """
        Unified search with caching and explainability
        
        Args:
            text_query: Text search query
            image_query: PIL Image for visual search
            top_k: Number of results
            alpha: Image weight for fusion (0-1)
            fusion_method: Fusion strategy
            filters: Optional filters (category, price_min, price_max)
            diversity_weight: MMR diversity weight
        
        Returns:
            (results_list, metadata_dict)
        """
        start_time = time.time()
        metadata = {
            'cache_hit': False,
            'embeddings_cached': [],
            'fusion_method': fusion_method,
            'alpha': alpha
        }
        
        # Generate cache key
        cache_key = self._generate_search_cache_key(
            text_query, image_query, alpha, fusion_method, filters
        )
        
        # Check cache for full search results
        cached_results = self.cache.get_cached_search_results(cache_key)
        if cached_results:
            metadata['cache_hit'] = True
            metadata['search_time_ms'] = (time.time() - start_time) * 1000
            logger.info(f"Cache hit for search: {cache_key[:16]}...")
            return cached_results[:top_k], metadata
        
        # Compute embeddings (with caching)
        image_embedding = None
        text_embedding = None
        
        if image_query:
            image_embedding = await self._get_or_compute_image_embedding(image_query)
            if image_embedding is not None:
                metadata['embeddings_cached'].append('image')
        
        if text_query:
            text_embedding = await self._get_or_compute_text_embedding(text_query)
            if text_embedding is not None:
                metadata['embeddings_cached'].append('text')
        
        # Fuse embeddings
        fused_embedding, match_scores = self.fusion_engine.fuse(
            image_embedding=image_embedding,
            text_embedding=text_embedding,
            alpha=alpha,
            method=fusion_method
        )
        
        metadata['match_scores'] = match_scores
        
        # Search FAISS index
        product_ids, similarities = self.faiss_index.search(
            fused_embedding,
            k=top_k * 2  # Get extra for filtering
        )
        
        # Retrieve product metadata
        results = []
        for pid, sim in zip(product_ids, similarities):
            product = self.faiss_index.get_product_metadata(pid)
            if product is None:
                continue
            
            # Apply filters
            if filters and not self._match_filters(product, filters):
                continue
            
            # Generate explanation
            explanation = ExplainableRecommender.generate_explanation(
                product=product,
                query_text=text_query,
                query_image=(image_query is not None),
                similarity_score=float(sim),
                match_scores=match_scores
            )
            
            results.append({
                'product_id': product['product_id'],
                'title': product.get('title', ''),
                'price': product.get('price'),
                'category': product.get('category'),
                'image_url': product.get('image_url', ''),
                'brand': product.get('brand'),
                'rating': product.get('rating'),
                'similarity_score': float(sim),
                'match_explanation': explanation
            })
            
            if len(results) >= top_k:
                break
        
        # Apply diversity reranking if requested
        if diversity_weight > 0 and len(results) > 1:
            results = self._apply_diversity_reranking(results, diversity_weight)
        
        # Cache results
        self.cache.cache_search_results(cache_key, results, ttl=3600)  # 1 hour
        
        metadata['search_time_ms'] = (time.time() - start_time) * 1000
        metadata['results_count'] = len(results)
        
        logger.info(f"Search completed: {len(results)} results in {metadata['search_time_ms']:.2f}ms")
        return results, metadata
    
    async def _get_or_compute_image_embedding(
        self, 
        image: Image.Image
    ) -> Optional[np.ndarray]:
        """Get image embedding from cache or compute"""
        # Generate image hash
        image_hash = hashlib.md5(image.tobytes()).hexdigest()
        
        # Check cache
        cached = self.cache.get_cached_embedding(image_hash, 'image')
        if cached is not None:
            logger.debug(f"Image embedding cache hit: {image_hash[:8]}")
            return cached
        
        # Compute embedding
        embedding = await self.clip_model.encode_image(image)
        
        # Cache it
        self.cache.cache_embedding(image_hash, 'image', embedding, ttl=86400)
        
        return embedding
    
    async def _get_or_compute_text_embedding(
        self, 
        text: str
    ) -> Optional[np.ndarray]:
        """Get text embedding from cache or compute"""
        # Check cache
        cached = self.cache.get_cached_embedding(text, 'text')
        if cached is not None:
            logger.debug(f"Text embedding cache hit: {text[:20]}")
            return cached
        
        # Compute embedding
        embedding = await self.clip_model.encode_text(text)
        
        # Cache it
        self.cache.cache_embedding(text, 'text', embedding, ttl=86400)
        
        return embedding
    
    def _generate_search_cache_key(
        self,
        text: Optional[str],
        image: Optional[Image.Image],
        alpha: float,
        method: str,
        filters: Optional[Dict]
    ) -> str:
        """Generate unique cache key for search"""
        key_components = [
            text or '',
            hashlib.md5(image.tobytes()).hexdigest() if image else '',
            str(alpha),
            method,
            json.dumps(filters, sort_keys=True) if filters else ''
        ]
        key_str = '|'.join(key_components)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def _match_filters(self, product: Dict, filters: Dict) -> bool:
        """Check if product matches filters"""
        if 'category' in filters:
            if product.get('category') != filters['category']:
                return False
        
        if 'price_min' in filters:
            if product.get('price', 0) < filters['price_min']:
                return False
        
        if 'price_max' in filters:
            if product.get('price', float('inf')) > filters['price_max']:
                return False
        
        return True
    
    def _apply_diversity_reranking(
        self, 
        results: List[Dict], 
        diversity_weight: float
    ) -> List[Dict]:
        """Apply MMR-style diversity reranking"""
        if not results:
            return results
        
        # Extract scores and categories
        scores = np.array([r['similarity_score'] for r in results])
        
        # Apply diversity penalty (simple greedy MMR)
        reranked_indices = []
        selected_categories = []
        remaining = list(range(len(results)))
        
        while remaining:
            best_idx = None
            best_score = -1
            
            for idx in remaining:
                base_score = scores[idx]
                category = results[idx].get('category', 'unknown')
                
                # Diversity penalty
                penalty = diversity_weight * selected_categories.count(category)
                final_score = base_score * (1.0 - penalty)
                
                if final_score > best_score:
                    best_score = final_score
                    best_idx = idx
            
            reranked_indices.append(best_idx)
            selected_categories.append(results[best_idx].get('category', 'unknown'))
            remaining.remove(best_idx)
        
        return [results[i] for i in reranked_indices]
    
    def get_product_by_id(self, product_id: str) -> Optional[Dict]:
        """Retrieve product by ID with caching"""
        # Check cache
        cached = self.cache.get_cached_product(product_id)
        if cached:
            return cached
        
        # Get from FAISS metadata
        product = self.faiss_index.get_product_metadata(product_id)
        
        # Cache it
        if product:
            self.cache.cache_product(product_id, product, ttl=86400)
        
        return product
    
    async def get_similar_products(
        self, 
        product_id: str, 
        top_k: int = 10
    ) -> List[Dict]:
        """Find similar products to a given product"""
        # Get product embedding
        product = self.get_product_by_id(product_id)
        if not product:
            return []
        
        # Get its embedding (reconstruct from FAISS)
        embedding = self.faiss_index.get_embedding_by_id(product_id)
        if embedding is None:
            return []
        
        # Search for similar
        product_ids, similarities = self.faiss_index.search(embedding, k=top_k+1)
        
        # Filter out the query product itself
        results = []
        for pid, sim in zip(product_ids, similarities):
            if pid == product_id:
                continue
            
            prod = self.faiss_index.get_product_metadata(pid)
            if prod:
                results.append({
                    **prod,
                    'similarity_score': float(sim)
                })
        
        return results[:top_k]


# Global service instance
_search_service: Optional[SearchService] = None


def initialize_search_service(
    clip_model: CLIPModel,
    faiss_index: FAISSIndex,
    cache: RedisCacheManager
) -> SearchService:
    """Initialize global search service"""
    global _search_service
    _search_service = SearchService(clip_model, faiss_index, cache)
    return _search_service


def get_search_service() -> Optional[SearchService]:
    """Get global search service instance"""
    return _search_service
