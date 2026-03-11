"""
Multi-Stage Ranking Engine
Advanced ranking system with multiple stages for accurate product retrieval.

Implements:
Stage 1: Vector Similarity (CLIP cosine similarity)
Stage 2: Attribute Matching (color, category, gender, style)
Stage 3: Text Matching (title and description similarity)
Stage 4: Business Ranking (popularity, ratings, price)

Final Score = 0.60*visual + 0.25*text + 0.15*attribute
"""
import asyncio
import logging
import re
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass

import numpy as np
from PIL import Image

from app.config.settings import settings
from app.services.query_understanding import QueryAttributes
from app.services.product_catalog import Product

logger = logging.getLogger(__name__)


@dataclass
class RankingScores:
    """Detailed ranking scores for explainability."""
    visual_score: float = 0.0
    text_score: float = 0.0
    attribute_score: float = 0.0
    business_score: float = 0.0
    final_score: float = 0.0
    
    def to_dict(self) -> Dict:
        return {
            "visual_score": round(self.visual_score, 4),
            "text_score": round(self.text_score, 4),
            "attribute_score": round(self.attribute_score, 4),
            "business_score": round(self.business_score, 4),
            "final_score": round(self.final_score, 4),
        }


@dataclass
class RankedProduct:
    """Product with complete ranking information."""
    product: Any  # Product or dict
    scores: RankingScores
    rank: int = 0
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for API response."""
        if hasattr(self.product, 'to_dict'):
            product_data = self.product.to_dict()
        elif isinstance(self.product, dict):
            product_data = self.product
        else:
            product_data = {
                "title": getattr(self.product, 'title', 'Unknown'),
                "url": getattr(self.product, 'url', ''),
                "image_url": getattr(self.product, 'image_url', ''),
            }
        
        return {
            **product_data,
            **self.scores.to_dict(),
            "rank": self.rank,
        }


class MultiStageRankingEngine:
    """
    Advanced multi-stage ranking engine for fashion product retrieval.
    
    Combines multiple signals:
    - Visual similarity (CLIP embeddings)
    - Text similarity (title/description matching)
    - Attribute matching (fashion attributes)
    - Business signals (popularity, ratings, price)
    """
    
    def __init__(
        self,
        visual_weight: float = 0.60,
        text_weight: float = 0.25,
        attribute_weight: float = 0.15,
        business_weight: float = 0.0,
    ):
        """
        Initialize ranking engine with configurable weights.
        
        Args:
            visual_weight: Weight for visual similarity
            text_weight: Weight for text similarity
            attribute_weight: Weight for attribute matching
            business_weight: Weight for business signals
        """
        # Normalize weights
        total = visual_weight + text_weight + attribute_weight + business_weight
        self.visual_weight = visual_weight / total
        self.text_weight = text_weight / total
        self.attribute_weight = attribute_weight / total
        self.business_weight = business_weight / total
        
        logger.info(
            f"MultiStageRankingEngine initialized: "
            f"visual={self.visual_weight:.2f}, text={self.text_weight:.2f}, "
            f"attr={self.attribute_weight:.2f}, business={self.business_weight:.2f}"
        )
    
    async def rank(
        self,
        clip_model,
        candidates: List[Tuple[Any, Any]],  # [(product, image), ...]
        query_embedding: np.ndarray,
        query_text: Optional[str] = None,
        query_attributes: Optional[QueryAttributes] = None,
        image_embedding: Optional[np.ndarray] = None,
        text_embedding: Optional[np.ndarray] = None,
        top_k: int = 10,
    ) -> List[RankedProduct]:
        """
        Multi-stage ranking of candidate products.
        
        Args:
            clip_model: CLIP model instance
            candidates: List of (product, PIL.Image) tuples
            query_embedding: Fused query embedding
            query_text: Original query text
            query_attributes: Extracted query attributes
            image_embedding: Optional query image embedding
            text_embedding: Optional query text embedding
            top_k: Number of top results to return
        
        Returns:
            List of RankedProduct objects sorted by final score
        """
        if not candidates:
            logger.warning("No candidates to rank")
            return []
        
        logger.info(f"Ranking {len(candidates)} candidates...")
        
        ranked_products = []
        
        # Process each candidate
        for product_obj, product_image in candidates:
            try:
                scores = await self._compute_all_scores(
                    clip_model=clip_model,
                    product=product_obj,
                    product_image=product_image,
                    query_embedding=query_embedding,
                    query_text=query_text,
                    query_attributes=query_attributes,
                    image_embedding=image_embedding,
                    text_embedding=text_embedding,
                )
                
                ranked_products.append(RankedProduct(
                    product=product_obj,
                    scores=scores,
                ))
            
            except Exception as e:
                logger.warning(f"Failed to rank product: {e}")
                continue
        
        # Sort by final score
        ranked_products.sort(key=lambda x: x.scores.final_score, reverse=True)
        
        # Assign ranks
        for idx, rp in enumerate(ranked_products[:top_k]):
            rp.rank = idx + 1
        
        logger.info(f"Ranked {len(ranked_products)} products, returning top {top_k}")
        return ranked_products[:top_k]
    
    async def _compute_all_scores(
        self,
        clip_model,
        product: Any,
        product_image: Image.Image,
        query_embedding: np.ndarray,
        query_text: Optional[str],
        query_attributes: Optional[QueryAttributes],
        image_embedding: Optional[np.ndarray],
        text_embedding: Optional[np.ndarray],
    ) -> RankingScores:
        """Compute all ranking scores for a product."""
        scores = RankingScores()
        
        # Stage 1: Visual Similarity
        scores.visual_score = await self._compute_visual_score(
            clip_model=clip_model,
            product_image=product_image,
            query_embedding=query_embedding,
            image_embedding=image_embedding,
        )
        
        # Stage 2: Text Similarity
        scores.text_score = self._compute_text_score(
            product=product,
            query_text=query_text,
            text_embedding=text_embedding,
        )
        
        # Stage 3: Attribute Matching
        scores.attribute_score = self._compute_attribute_score(
            product=product,
            query_attributes=query_attributes,
        )
        
        # Stage 4: Business Signals
        scores.business_score = self._compute_business_score(product)
        
        # Final weighted score
        scores.final_score = (
            self.visual_weight * scores.visual_score +
            self.text_weight * scores.text_score +
            self.attribute_weight * scores.attribute_score +
            self.business_weight * scores.business_score
        )
        
        return scores
    
    # ─── Stage 1: Visual Similarity ─────────────────────────────────────────
    
    async def _compute_visual_score(
        self,
        clip_model,
        product_image: Image.Image,
        query_embedding: np.ndarray,
        image_embedding: Optional[np.ndarray] = None,
    ) -> float:
        """
        Compute visual similarity using CLIP.
        
        Returns cosine similarity between query and product image.
        """
        try:
            # Encode product image
            product_embedding = await clip_model.encode_image(product_image)
            
            # Compute cosine similarity
            similarity = np.dot(query_embedding, product_embedding)
            
            # Normalize to [0, 1]
            similarity = (similarity + 1) / 2
            
            return float(similarity)
        
        except Exception as e:
            logger.warning(f"Visual score computation failed: {e}")
            return 0.0
    
    # ─── Stage 2: Text Similarity ───────────────────────────────────────────
    
    def _compute_text_score(
        self,
        product: Any,
        query_text: Optional[str],
        text_embedding: Optional[np.ndarray] = None,
    ) -> float:
        """
        Compute text similarity between query and product.
        
        Uses simple keyword matching and overlap.
        """
        if not query_text:
            return 0.5  # Neutral score
        
        try:
            # Get product text
            product_text = self._get_product_text(product)
            
            if not product_text:
                return 0.3
            
            # Simple token-based similarity
            query_tokens = set(self._tokenize(query_text.lower()))
            product_tokens = set(self._tokenize(product_text.lower()))
            
            if not query_tokens or not product_tokens:
                return 0.3
            
            # Jaccard similarity
            intersection = query_tokens & product_tokens
            union = query_tokens | product_tokens
            
            jaccard = len(intersection) / len(union) if union else 0.0
            
            # Boost for exact phrase matches
            exact_match_boost = 0.0
            query_lower = query_text.lower()
            product_lower = product_text.lower()
            
            if query_lower in product_lower:
                exact_match_boost = 0.3
            elif any(word in product_lower for word in query_tokens if len(word) > 3):
                exact_match_boost = 0.15
            
            score = min(jaccard + exact_match_boost, 1.0)
            return score
        
        except Exception as e:
            logger.warning(f"Text score computation failed: {e}")
            return 0.3
    
    def _get_product_text(self, product: Any) -> str:
        """Extract searchable text from product."""
        texts = []
        
        if hasattr(product, 'title'):
            texts.append(str(product.title))
        elif isinstance(product, dict) and 'title' in product:
            texts.append(str(product['title']))
        
        if hasattr(product, 'description'):
            texts.append(str(product.description))
        elif isinstance(product, dict) and 'description' in product:
            texts.append(str(product.get('description', '')))
        
        if hasattr(product, 'snippet'):
            texts.append(str(product.snippet or ''))
        elif isinstance(product, dict) and 'snippet' in product:
            texts.append(str(product.get('snippet', '')))
        
        return ' '.join(texts)
    
    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization."""
        # Remove special characters, keep alphanumeric and spaces
        text = re.sub(r'[^\w\s]', ' ', text)
        tokens = text.split()
        return [t for t in tokens if len(t) > 1]
    
    # ─── Stage 3: Attribute Matching ────────────────────────────────────────
    
    def _compute_attribute_score(
        self,
        product: Any,
        query_attributes: Optional[QueryAttributes],
    ) -> float:
        """
        Compute attribute matching score.
        
        Checks how many query attributes match the product.
        """
        if not query_attributes:
            return 0.5  # Neutral score
        
        try:
            matches = 0
            total_checks = 0
            
            # Check color match
            if query_attributes.colors:
                total_checks += 1
                if self._check_attribute_match(product, 'color', query_attributes.colors):
                    matches += 1
            
            # Check category match
            if query_attributes.categories:
                total_checks += 1
                if self._check_attribute_match(product, 'category', query_attributes.categories):
                    matches += 1.5  # Category is more important
            
            # Check pattern match
            if query_attributes.patterns:
                total_checks += 1
                if self._check_attribute_match(product, 'pattern', query_attributes.patterns):
                    matches += 0.8
            
            # Check material match
            if query_attributes.materials:
                total_checks += 1
                if self._check_attribute_match(product, 'material', query_attributes.materials):
                    matches += 0.7
            
            # Check gender match
            if query_attributes.genders:
                total_checks += 1
                if self._check_attribute_match(product, 'gender', query_attributes.genders):
                    matches += 1
            
            # Check occasion match
            if query_attributes.occasions:
                total_checks += 1
                if self._check_attribute_match(product, 'occasion', query_attributes.occasions):
                    matches += 0.6

            # Check season/weather match
            if query_attributes.seasons:
                total_checks += 1
                if self._check_attribute_match(product, 'weather', query_attributes.seasons):
                    matches += 0.9

            # Taxonomy-specific checks
            if query_attributes.sleeve_types:
                total_checks += 1
                if self._check_attribute_match(product, 'sleeve_type', query_attributes.sleeve_types):
                    matches += 0.6

            if query_attributes.collar_types:
                total_checks += 1
                if self._check_attribute_match(product, 'collar_type', query_attributes.collar_types):
                    matches += 0.5

            if query_attributes.length_types:
                total_checks += 1
                if self._check_attribute_match(product, 'length', query_attributes.length_types):
                    matches += 0.5

            if query_attributes.neckline_types:
                total_checks += 1
                if self._check_attribute_match(product, 'neckline', query_attributes.neckline_types):
                    matches += 0.5

            if query_attributes.sole_types:
                total_checks += 1
                if self._check_attribute_match(product, 'sole_type', query_attributes.sole_types):
                    matches += 0.5

            if query_attributes.closure_types:
                total_checks += 1
                if self._check_attribute_match(product, 'closure', query_attributes.closure_types):
                    matches += 0.5

            if query_attributes.use_types:
                total_checks += 1
                if self._check_attribute_match(product, 'use', query_attributes.use_types):
                    matches += 0.5
            
            if total_checks == 0:
                return 0.5
            
            # Normalize score
            score = matches / (total_checks * 1.5)  # 1.5 is max weight
            return min(score, 1.0)
        
        except Exception as e:
            logger.warning(f"Attribute score computation failed: {e}")
            return 0.5
    
    def _check_attribute_match(
        self,
        product: Any,
        attr_name: str,
        attr_values: List[str]
    ) -> bool:
        """Check if product matches any of the attribute values."""
        # Get product attribute value
        product_value = None
        
        if hasattr(product, attr_name):
            product_value = getattr(product, attr_name)
        elif isinstance(product, dict):
            product_value = product.get(attr_name)
        
        # For gender, check in title/text
        if attr_name == 'gender':
            product_text = self._get_product_text(product).lower()
            return any(val.lower() in product_text for val in attr_values)
        
        # For occasion, check in description/tags
        if attr_name == 'occasion':
            product_text = self._get_product_text(product).lower()
            tags = getattr(product, 'tags', []) if hasattr(product, 'tags') else []
            tag_text = ' '.join(tags).lower()
            return any(val.lower() in product_text or val.lower() in tag_text for val in attr_values)

        if attr_name == 'weather':
            weather = None
            if hasattr(product, 'weather'):
                weather = getattr(product, 'weather')
            elif isinstance(product, dict):
                weather = product.get('weather')
            if weather:
                return any(val.lower() in str(weather).lower() for val in attr_values)
            return any(val.lower() in self._get_product_text(product).lower() for val in attr_values)
        
        if not product_value:
            return False
        
        product_value_lower = str(product_value).lower()
        return any(val.lower() in product_value_lower for val in attr_values)
    
    # ─── Stage 4: Business Signals ──────────────────────────────────────────
    
    def _compute_business_score(self, product: Any) -> float:
        """
        Compute business ranking score.
        
        Combines:
        - Popularity (rating)
        - Price (prefer mid-range)
        - Brand recognition
        """
        score = 0.0
        
        try:
            # Rating/popularity (40% of business score)
            rating = 0.0
            if hasattr(product, 'rating'):
                rating = product.rating
            elif isinstance(product, dict):
                rating = product.get('rating', 0.0)
            
            if rating > 0:
                rating_score = rating / 5.0
                score += 0.4 * rating_score
            else:
                score += 0.2  # Default for unknown
            
            # Price (30% of business score)
            # Prefer mid-range products (₹1000-5000 gets highest score)
            price = 0.0
            if hasattr(product, 'price'):
                price = product.price
            elif isinstance(product, dict):
                price = product.get('price', 0.0)
            
            if price > 0:
                if 1000 <= price <= 5000:
                    price_score = 1.0
                elif price < 1000:
                    price_score = 0.8
                elif price < 10000:
                    price_score = 0.7
                else:
                    price_score = 0.5
                score += 0.3 * price_score
            else:
                score += 0.15
            
            # Brand (20% of business score)
            brand = None
            if hasattr(product, 'brand'):
                brand = product.brand
            elif isinstance(product, dict):
                brand = product.get('brand')
            
            if brand:
                score += 0.2
            else:
                score += 0.1
            
            # Source boost (10% of business score)
            # Prefer known e-commerce sites
            source = self._get_source(product)
            if source.lower() in ['myntra', 'amazon', 'flipkart', 'ajio']:
                score += 0.1
            else:
                score += 0.05
            
            return min(score, 1.0)
        
        except Exception as e:
            logger.warning(f"Business score computation failed: {e}")
            return 0.5
    
    def _get_source(self, product: Any) -> str:
        """Extract source/website from product."""
        if hasattr(product, 'source'):
            return str(product.source)
        elif isinstance(product, dict):
            return str(product.get('source', ''))
        return 'Unknown'


# ─── Singleton Instance ──────────────────────────────────────────────────────

multi_stage_ranking_engine = MultiStageRankingEngine()
