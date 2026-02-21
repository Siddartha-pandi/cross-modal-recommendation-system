"""
Embedding Fusion Engine
Implements the Ef = α*Ei + (1-α)*Et fusion algorithm with match score computation
"""

import numpy as np
from typing import Optional, Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)


class FusionEngine:
    """
    Advanced embedding fusion with multiple strategies and explainability
    """
    
    def __init__(self, default_alpha: float = 0.7):
        """
        Initialize fusion engine
        
        Args:
            default_alpha: Default weight for image embedding (0-1)
        """
        self.default_alpha = default_alpha
        logger.info(f"FusionEngine initialized with α={default_alpha}")
    
    def fuse(
        self,
        image_embedding: Optional[np.ndarray] = None,
        text_embedding: Optional[np.ndarray] = None,
        alpha: float = None,
        method: str = "weighted_avg"
    ) -> Tuple[np.ndarray, Dict[str, float]]:
        """
        Fuse image and text embeddings with explainability
        
        Args:
            image_embedding: Normalized image embedding (512-dim)
            text_embedding: Normalized text embedding (512-dim)
            alpha: Weight for image (0-1), uses default if None
            method: Fusion strategy ('weighted_avg', 'concatenation', 'element_wise')
        
        Returns:
            (fused_embedding, match_scores_dict)
        """
        alpha = alpha if alpha is not None else self.default_alpha
        
        # Validate inputs
        if image_embedding is None and text_embedding is None:
            raise ValueError("At least one embedding must be provided")
        
        # Single modality cases
        if image_embedding is None:
            logger.debug("Text-only search")
            return text_embedding, {"text_contribution": 1.0, "image_contribution": 0.0}
        
        if text_embedding is None:
            logger.debug("Image-only search")
            return image_embedding, {"image_contribution": 1.0, "text_contribution": 0.0}
        
        # Ensure normalized
        image_embedding = self._normalize(image_embedding)
        text_embedding = self._normalize(text_embedding)
        
        # Execute fusion strategy
        if method == "weighted_avg":
            fused = self._weighted_avg_fusion(image_embedding, text_embedding, alpha)
        elif method == "concatenation":
            fused = self._concatenation_fusion(image_embedding, text_embedding)
        elif method == "element_wise":
            fused = self._element_wise_fusion(image_embedding, text_embedding)
        else:
            raise ValueError(f"Unknown fusion method: {method}")
        
        # Compute match scores for explainability
        match_scores = self._compute_match_scores(
            image_embedding, text_embedding, fused, alpha
        )
        
        logger.debug(f"Fusion complete: method={method}, α={alpha:.2f}")
        return fused, match_scores
    
    def _weighted_avg_fusion(
        self, 
        img_emb: np.ndarray, 
        txt_emb: np.ndarray, 
        alpha: float
    ) -> np.ndarray:
        """
        Core fusion algorithm: Ef = α*Ei + (1-α)*Et
        """
        beta = 1.0 - alpha
        fused = (alpha * img_emb) + (beta * txt_emb)
        return self._normalize(fused)
    
    def _concatenation_fusion(
        self, 
        img_emb: np.ndarray, 
        txt_emb: np.ndarray
    ) -> np.ndarray:
        """
        Concatenate embeddings [Ei || Et]
        """
        fused = np.concatenate([img_emb, txt_emb])
        return self._normalize(fused)
    
    def _element_wise_fusion(
        self, 
        img_emb: np.ndarray, 
        txt_emb: np.ndarray
    ) -> np.ndarray:
        """
        Element-wise multiplication: Ei ⊙ Et
        """
        fused = img_emb * txt_emb
        return self._normalize(fused)
    
    def _normalize(self, embedding: np.ndarray) -> np.ndarray:
        """L2 normalization"""
        norm = np.linalg.norm(embedding)
        if norm == 0:
            logger.warning("Zero norm embedding detected")
            return embedding
        return embedding / norm
    
    def _compute_match_scores(
        self,
        image_embedding: np.ndarray,
        text_embedding: np.ndarray,
        fused_embedding: np.ndarray,
        alpha: float
    ) -> Dict[str, float]:
        """
        Compute match contribution scores for explainability
        
        Returns:
            {
                'image_contribution': float (0-1),
                'text_contribution': float (0-1),
                'image_text_alignment': float (0-1),
                'fusion_quality': float (0-1)
            }
        """
        # Cosine similarity between modalities
        img_txt_sim = float(np.dot(image_embedding, text_embedding))
        
        # Contribution scores (based on alpha)
        img_contrib = alpha
        txt_contrib = 1.0 - alpha
        
        # Alignment score (how well image and text agree)
        alignment = (img_txt_sim + 1.0) / 2.0  # Map from [-1,1] to [0,1]
        
        # Fusion quality (weighted similarity to components)
        img_sim = float(np.dot(fused_embedding, image_embedding))
        txt_sim = float(np.dot(fused_embedding, text_embedding))
        fusion_quality = (alpha * img_sim + (1-alpha) * txt_sim + 1.0) / 2.0
        
        return {
            'image_contribution': float(img_contrib),
            'text_contribution': float(txt_contrib),
            'image_text_alignment': float(alignment),
            'fusion_quality': float(fusion_quality)
        }
    
    def compute_similarity_scores(
        self,
        query_embedding: np.ndarray,
        product_embeddings: np.ndarray
    ) -> np.ndarray:
        """
        Compute cosine similarity between query and products
        
        Args:
            query_embedding: Query embedding (512,)
            product_embeddings: Product embeddings (N, 512)
        
        Returns:
            Similarity scores (N,) normalized to [0, 1]
        """
        # Ensure normalized
        query_embedding = self._normalize(query_embedding)
        
        # Compute cosine similarities
        similarities = np.dot(product_embeddings, query_embedding)
        
        # Map from [-1, 1] to [0, 1]
        similarities = (similarities + 1.0) / 2.0
        
        return similarities
    
    def rerank_with_diversity(
        self,
        scores: np.ndarray,
        product_features: List[Dict],
        diversity_weight: float = 0.1
    ) -> np.ndarray:
        """
        Rerank results with diversity penalty (MMR-like)
        
        Args:
            scores: Initial similarity scores
            product_features: List of product metadata dicts
            diversity_weight: Weight for diversity (0-1)
        
        Returns:
            Reranked scores
        """
        if diversity_weight == 0:
            return scores
        
        # Extract categories for diversity
        categories = [p.get('category', 'unknown') for p in product_features]
        
        # Compute diversity penalty
        reranked_scores = scores.copy()
        selected_categories = []
        
        for i, category in enumerate(categories):
            if category in selected_categories:
                # Apply penalty for duplicate category
                penalty = diversity_weight * selected_categories.count(category)
                reranked_scores[i] *= (1.0 - penalty)
            selected_categories.append(category)
        
        return reranked_scores


class ExplainableRecommender:
    """
    Generate human-readable explanations for recommendations
    """
    
    @staticmethod
    def generate_explanation(
        product: Dict,
        query_text: Optional[str],
        query_image: bool,
        similarity_score: float,
        match_scores: Dict[str, float]
    ) -> str:
        """
        Generate match explanation for a product
        
        Args:
            product: Product metadata
            query_text: Text query (if any)
            query_image: Whether image was provided
            similarity_score: Overall similarity (0-1)
            match_scores: Contribution scores from fusion
        
        Returns:
            Human-readable explanation string
        """
        explanations = []
        
        # Overall match
        if similarity_score > 0.9:
            match_quality = "Excellent match"
        elif similarity_score > 0.75:
            match_quality = "Very good match"
        elif similarity_score > 0.6:
            match_quality = "Good match"
        else:
            match_quality = "Moderate match"
        
        explanations.append(match_quality)
        
        # Modality contributions
        if query_image and query_text:
            img_contrib = match_scores.get('image_contribution', 0)
            txt_contrib = match_scores.get('text_contribution', 0)
            alignment = match_scores.get('image_text_alignment', 0)
            
            if img_contrib > 0.6:
                explanations.append(f"Strong visual similarity ({img_contrib*100:.0f}%)")
            if txt_contrib > 0.4:
                explanations.append(f"Matches text query ({txt_contrib*100:.0f}%)")
            if alignment > 0.7:
                explanations.append("Image and text are well-aligned")
        
        elif query_image:
            explanations.append("Visually similar to your image")
        
        elif query_text:
            # Text-only: extract keywords
            if query_text:
                keywords = query_text.lower().split()[:3]
                if any(kw in product.get('title', '').lower() for kw in keywords):
                    explanations.append("Matches query keywords")
        
        # Category relevance
        category = product.get('category', '')
        if category and query_text and category.lower() in query_text.lower():
            explanations.append(f"In {category} category")
        
        return " • ".join(explanations)
