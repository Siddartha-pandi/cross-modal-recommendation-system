"""
Ranking Service
Re-ranks candidate products using CLIP ViT-L/14 cosine similarity
between the fused query embedding and each candidate's image embedding.
"""
import asyncio
import logging
from typing import List, Tuple, Optional

import numpy as np
from PIL import Image

from app.config.settings import settings

logger = logging.getLogger(__name__)


class RecommendationResult:
    """Final ranked recommendation with metadata."""

    def __init__(
        self,
        title: str,
        url: str,
        image_url: str,
        source: str,
        similarity_score: float,
        visual_score: float = 0.0,
        text_score: float = 0.0,
        price: Optional[str] = None,
        snippet: Optional[str] = None,
        position: int = 0,
    ):
        self.title = title
        self.url = url
        self.image_url = image_url
        self.source = source
        self.similarity_score = round(float(similarity_score), 4)
        self.visual_score = round(float(visual_score), 4)
        self.text_score = round(float(text_score), 4)
        self.price = price
        self.snippet = snippet
        self.position = position

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "source": self.source,
            "url": self.url,
            "image_url": self.image_url,
            "similarity_score": self.similarity_score,
            "visual_score": self.visual_score,
            "text_score": self.text_score,
            "price": self.price,
            "snippet": self.snippet,
        }


class RankingService:
    """
    Encodes candidate product images with CLIP and ranks them by
    cosine similarity to the fused query embedding.
    """

    def __init__(self, top_k: int = None):
        self.top_k = top_k or settings.TOP_K

    async def rank(
        self,
        clip_model,                         # CLIPModel instance (ViT-L/14)
        fused_embedding: np.ndarray,         # (1024,) normalised fused query
        candidates: List[Tuple[any, Image.Image]],  # [(CandidateProduct, PIL.Image)]
        image_embedding: Optional[np.ndarray] = None,
        text_embedding: Optional[np.ndarray] = None,
        alpha: float = None,
        top_k: int = None,
    ) -> List[RecommendationResult]:
        """
        Rank candidates by CLIP similarity.

        Args:
            clip_model: CLIPModel instance (ViT-L/14).
            fused_embedding: L2-normalised fused query embedding (1024-dim).
            candidates: List of (CandidateProduct, PIL.Image) tuples.
            image_embedding: Optional query image embedding for per-modality scores.
            text_embedding: Optional query text embedding for per-modality scores.
            alpha: Image weight used in fusion (for explainability).
            top_k: Override default top-k.

        Returns:
            List of RecommendationResult sorted by similarity descending.
        """
        k = top_k or self.top_k
        alpha = alpha if alpha is not None else settings.IMAGE_ALPHA
        beta = 1.0 - alpha

        if not candidates:
            logger.warning("RankingService received 0 candidates")
            return []

        # Encode all product images in a batch
        pil_images = [pil for _, pil in candidates]
        product_metas = [meta for meta, _ in candidates]

        logger.info(f"Encoding {len(pil_images)} candidate images with CLIP...")
        product_embeddings = await clip_model.encode_batch_images(pil_images)
        # product_embeddings: (N, dim) — already L2-normalised by CLIPModel

        # Ensure fused query is normalised
        fused_norm = fused_embedding / (np.linalg.norm(fused_embedding) + 1e-9)

        # Cosine similarity: fused_norm · product_embeddings.T
        scores = product_embeddings @ fused_norm  # (N,)

        # Per-modality scores for explainability
        if image_embedding is not None:
            img_norm = image_embedding / (np.linalg.norm(image_embedding) + 1e-9)
            visual_scores = product_embeddings @ img_norm
        else:
            visual_scores = scores

        if text_embedding is not None:
            txt_norm = text_embedding / (np.linalg.norm(text_embedding) + 1e-9)
            text_scores = product_embeddings @ txt_norm
        else:
            text_scores = scores

        # Sort descending by fused score
        ranked_indices = np.argsort(scores)[::-1]

        results: List[RecommendationResult] = []
        for rank_pos, idx in enumerate(ranked_indices[:k]):
            meta = product_metas[idx]
            sim = float(scores[idx])
            vis = float(visual_scores[idx])
            txt = float(text_scores[idx])

            # Map raw cosine [-1, 1] → [0, 1] for display
            sim_display = (sim + 1.0) / 2.0
            vis_display = (vis + 1.0) / 2.0
            txt_display = (txt + 1.0) / 2.0

            results.append(RecommendationResult(
                title=meta.title,
                url=meta.url,
                image_url=meta.image_url,
                source=meta.source,
                similarity_score=sim_display,
                visual_score=vis_display,
                text_score=txt_display,
                price=meta.price,
                snippet=meta.snippet,
                position=rank_pos + 1,
            ))

        logger.info(
            f"Ranked {len(results)} results. "
            f"Top score: {results[0].similarity_score:.4f}" if results else "No results."
        )
        return results


# Module-level singleton
ranking_service = RankingService()
