"""
/recommend API Endpoint
Full hybrid cross-modal fashion product retrieval pipeline:
  Image + Text → CLIP ViT-L/14 → Embedding Fusion → Web Search →
  Async Image Download → CLIP Re-ranking → Top-K Results

/recommend/advanced API Endpoint - Advanced Architecture:
  Input Processing → CLIP Feature Extraction → Query Understanding →
  Candidate Generation (Web Search + Product Index) → FAISS Search →
  Multi-Stage Ranking → Recommendation Filtering → Top-K Results
"""
import asyncio
import base64
import io
import re
import time
import logging
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from PIL import Image

import numpy as np

from app.config.settings import settings
from app.services.query_generator import query_generator
from app.services.web_search_service import web_search_service
from app.services.ranking_service import ranking_service
from app.services.query_understanding import query_understanding_service
from app.services.multi_stage_ranking import multi_stage_ranking_engine
from app.services.recommendation_filter import recommendation_filter
from app.services.fashion_knowledge_graph import fashion_knowledge_graph
from app.utils.image_downloader import download_images
from app.utils.preprocessing import validate_image, resize_image

logger = logging.getLogger(__name__)

recommend_router = APIRouter()

# ── Response schemas ─────────────────────────────────────────────────────────


class RecommendedProduct(BaseModel):
    title: str
    source: str
    url: str
    image_url: str
    similarity_score: float
    visual_score: Optional[float] = None
    text_score: Optional[float] = None
    price: str  # Now compulsory
    currency: Optional[str] = "INR"
    snippet: Optional[str] = None
    rank: int


class RecommendResponse(BaseModel):
    results: List[RecommendedProduct]
    total_results: int
    query_time: float
    search_phrase: str
    image_caption: Optional[str] = None
    alpha_used: float
    search_type: str             # "image", "text", or "hybrid"
    total_candidates: int        # how many were fetched from web search
    model_used: str = "ViT-L/14"


# ── Endpoint ─────────────────────────────────────────────────────────────────


@recommend_router.post("/recommend", response_model=RecommendResponse)
async def recommend(
    request: Request,
    text_query: Optional[str] = Form(None, description="Text description of the fashion item"),
    image: Optional[UploadFile] = File(None, description="Fashion image to search from"),
    top_k: int = Form(2, ge=1, le=20, description="Number of recommendations to return"),
    alpha: float = Form(0.6, ge=0.0, le=1.0, description="Image weight (0=text-only, 1=image-only)"),
):
    """
    Hybrid Cross-Modal Fashion Product Retrieval

    Accepts an optional fashion image and/or text description,
    fuses their CLIP ViT-L/14 embeddings, searches Indian e-commerce
    websites via SerpAPI, downloads candidate product images,
    and returns them re-ranked by cosine similarity.

    **Pipeline:**
    1. Encode image & text with CLIP ViT-L/14
    2. Fuse: V_fused = α·V_image + β·V_text  (normalised)
    3. Generate site-restricted search query
    4. Call SerpAPI → candidate products
    5. Download candidate images async (parallel)
    6. Encode with CLIP ViT-L/14
    7. Rank by cosine similarity → Top-K
    """
    start_time = time.time()

    if not text_query and not image:
        raise HTTPException(
            status_code=400,
            detail="At least one of 'image' or 'text_query' must be provided.",
        )

    # ── Get ViT-L/14 model from app state ─────────────────────────────────
    clip_model = getattr(request.app.state, "clip_model_large", None)
    if clip_model is None:
        raise HTTPException(
            status_code=503,
            detail="CLIP ViT-L/14 model is not loaded. Server may still be starting up.",
        )

    # ── Step 1: Encode inputs ──────────────────────────────────────────────
    image_embedding: Optional[np.ndarray] = None
    text_embedding: Optional[np.ndarray] = None
    pil_query_image: Optional[Image.Image] = None
    image_caption: Optional[str] = None

    if image:
        try:
            raw = await image.read()
            pil_query_image = Image.open(io.BytesIO(raw)).convert("RGB")
            image_embedding = await clip_model.encode_image(pil_query_image)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid image: {e}")

    if text_query and text_query.strip():
        try:
            text_embedding = await clip_model.encode_text(text_query.strip())
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Text encoding failed: {e}")

    blip_captioner = getattr(request.app.state, "blip_captioner", None)
    if pil_query_image is not None and blip_captioner is not None:
        image_caption = await blip_captioner.generate_caption(pil_query_image)

    # Determine search type
    if image_embedding is not None and text_embedding is not None:
        search_type = "hybrid"
    elif image_embedding is not None:
        search_type = "image"
    else:
        search_type = "text"

    # ── Step 2: Embedding fusion ───────────────────────────────────────────
    beta = 1.0 - alpha
    if image_embedding is not None and text_embedding is not None:
        fused = alpha * image_embedding + beta * text_embedding
    elif image_embedding is not None:
        fused = image_embedding
    else:
        fused = text_embedding  # type: ignore[assignment]

    fused = fused / (np.linalg.norm(fused) + 1e-9)

    # ── Step 3: Generate web search query ──────────────────────────────────
    # Use image-derived attributes when text is absent to avoid generic fallback.
    search_text = text_query
    if image_caption:
        search_text = f"{search_text} {image_caption}".strip() if search_text else image_caption
    if (not search_text or not search_text.strip()) and pil_query_image is not None and hasattr(clip_model, "infer_fashion_attributes"):
        try:
            inferred_attrs = await clip_model.infer_fashion_attributes(pil_query_image)
            inferred_text = _attributes_to_search_text(inferred_attrs)
            if inferred_text:
                search_text = inferred_text
        except Exception as e:
            logger.warning(f"Image attribute inference skipped in /recommend: {e}")

    search_phrase, full_query = query_generator.generate(text=search_text)
    logger.info(f"[Recommend] search_phrase='{search_phrase}' type={search_type}")

    # ── Step 4: Web search via SerpAPI ─────────────────────────────────────
    try:
        candidates = await web_search_service.search(
            query=full_query,
            num_results=settings.SEARCH_NUM_RESULTS,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Web search error: {e}", exc_info=True)
        raise HTTPException(status_code=502, detail=f"Web search failed: {e}")

    total_candidates = len(candidates)
    if not candidates:
        logger.warning("No candidates returned by web search")
        query_time = time.time() - start_time
        return RecommendResponse(
            results=[],
            total_results=0,
            query_time=round(query_time, 3),
            search_phrase=search_phrase,
            image_caption=image_caption,
            alpha_used=alpha,
            search_type=search_type,
            total_candidates=0,
        )

    # ── Step 5: Download candidate images async (parallel) ─────────────────
    image_urls = [c.image_url for c in candidates]
    downloaded = await download_images(
        urls=image_urls,
        timeout=settings.DOWNLOAD_TIMEOUT,
        max_concurrent=settings.MAX_CONCURRENT_DOWNLOADS,
    )

    # Map url → CandidateProduct for fast lookup
    url_to_meta = {c.image_url: c for c in candidates}

    # Pair each downloaded PIL image with its candidate metadata;
    # filter out too-small or malformed images
    pairs = []
    for url, pil_img in downloaded:
        meta = url_to_meta.get(url)
        if meta is None:
            continue
        pil_img = resize_image(pil_img, max_dim=800)
        if not validate_image(pil_img, min_dim=50):
            continue
        pairs.append((meta, pil_img))

    if not pairs:
        logger.warning("All candidate images failed to download or validate")
        query_time = time.time() - start_time
        return RecommendResponse(
            results=[],
            total_results=0,
            query_time=round(query_time, 3),
            search_phrase=search_phrase,
            image_caption=image_caption,
            alpha_used=alpha,
            search_type=search_type,
            total_candidates=total_candidates,
        )

    # ── Step 6 & 7: CLIP encode + rank candidates ──────────────────────────
    ranked = await ranking_service.rank(
        clip_model=clip_model,
        fused_embedding=fused,
        candidates=pairs,
        image_embedding=image_embedding,
        text_embedding=text_embedding,
        alpha=alpha,
        top_k=top_k,
    )

    # ── Build response ─────────────────────────────────────────────────────
    results = [
        RecommendedProduct(
            title=r.title,
            source=r.source,
            url=r.url,
            image_url=r.image_url,
            similarity_score=r.similarity_score,
            visual_score=r.visual_score,
            text_score=r.text_score,
            price=str(r.price) if r.price not in [None, '', 0, 0.0] else '0',
            snippet=r.snippet,
            rank=r.position,
        )
        for r in ranked
    ]

    query_time = time.time() - start_time
    logger.info(
        f"[Recommend] done in {query_time:.2f}s | "
        f"candidates={total_candidates} downloaded={len(pairs)} ranked={len(results)}"
    )

    return RecommendResponse(
        results=results,
        total_results=len(results),
        query_time=round(query_time, 3),
        search_phrase=search_phrase,
        image_caption=image_caption,
        alpha_used=alpha,
        search_type=search_type,
        total_candidates=total_candidates,
    )


# ══════════════════════════════════════════════════════════════════════════════
# Advanced Architecture Endpoint
# ══════════════════════════════════════════════════════════════════════════════


class AdvancedRecommendResponse(BaseModel):
    """Extended response model with advanced features."""
    results: List[Dict[str, Any]]
    total_results: int
    query_time: float
    search_phrase: str
    image_caption: Optional[str] = None
    expanded_query: str
    alpha_used: float
    search_type: str
    total_candidates: int
    indexed_candidates: int
    query_attributes: Dict[str, Any]
    knowledge_graph_attributes: Dict[str, str]
    model_used: str = "ViT-L/14"
    pipeline_stages: Dict[str, float]


def _merge_list_dict(base: Dict[str, Any], incoming: Dict[str, Any]) -> Dict[str, Any]:
    """Merge dict values by set-union for list fields used by the pipeline."""
    merged: Dict[str, Any] = dict(base)
    for key, value in incoming.items():
        if isinstance(value, list):
            existing = merged.get(key, [])
            if not isinstance(existing, list):
                existing = [existing] if existing else []
            merged[key] = sorted(set(existing + value))
        elif key not in merged or not merged[key]:
            merged[key] = value
    return merged


def _attributes_to_search_text(attrs: Dict[str, Any]) -> str:
    """Build a compact query phrase from inferred attributes."""
    parts: List[str] = []
    for key in ["colors", "use_types", "occasions", "categories"]:
        values = attrs.get(key, [])
        if isinstance(values, list) and values:
            token = str(values[0]).strip()
            if token and token not in parts:
                parts.append(token)
    return " ".join(parts)


@recommend_router.post("/recommend/advanced", response_model=AdvancedRecommendResponse)
async def recommend_advanced(
    request: Request,
    text_query: Optional[str] = Form(None, description="Text description of the fashion item"),
    image: Optional[UploadFile] = File(None, description="Fashion image to search from"),
    top_k: int = Form(2, ge=1, le=20, description="Number of recommendations to return"),
    alpha: float = Form(0.6, ge=0.0, le=1.0, description="Image weight (0=text-only, 1=image-only)"),
    use_product_index: bool = Form(True, description="Use FAISS product index for candidates"),
    apply_filters: bool = Form(True, description="Apply recommendation filters"),
):
    """
    Advanced Hybrid Cross-Modal Fashion Product Retrieval
    
    Implements the complete advanced architecture:
    
    Pipeline:
    1. Input Processing Layer
    2. CLIP Feature Extraction (ViT-L/14)
    3. Query Understanding (attribute extraction)
    4. Candidate Generation (Web Search + Product Index)
    5. FAISS Similarity Search
    6. Multi-Stage Ranking (visual + text + attribute + business)
    7. Recommendation Filtering (quality + diversity)
    8. Top-K Results
    
    This endpoint provides:
    - Semantic query understanding with attribute extraction
    - Dual candidate sources (web + product index)
    - Multi-stage ranking with explainability
    - Advanced filtering for quality and diversity
    """
    start_time = time.time()
    pipeline_times = {}
    
    if not text_query and not image:
        raise HTTPException(
            status_code=400,
            detail="At least one of 'image' or 'text_query' must be provided.",
        )
    
    # ── Get models from app state ──────────────────────────────────────────────
    clip_model = getattr(request.app.state, "clip_model_large", None)
    if clip_model is None:
        raise HTTPException(
            status_code=503,
            detail="CLIP ViT-L/14 model is not loaded. Server may still be starting up.",
        )
    
    # ══════════════════════════════════════════════════════════════════════════
    # STAGE 1: Input Processing Layer
    # ══════════════════════════════════════════════════════════════════════════
    stage_start = time.time()
    
    image_embedding: Optional[np.ndarray] = None
    text_embedding: Optional[np.ndarray] = None
    pil_query_image: Optional[Image.Image] = None
    image_caption: Optional[str] = None
    
    if image:
        try:
            raw = await image.read()
            pil_query_image = Image.open(io.BytesIO(raw)).convert("RGB")
            pil_query_image = resize_image(pil_query_image, max_dim=800)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid image: {e}")
    
    pipeline_times["input_processing"] = time.time() - stage_start
    
    # ══════════════════════════════════════════════════════════════════════════
    # STAGE 2: Multimodal Feature Extraction (CLIP)
    # ══════════════════════════════════════════════════════════════════════════
    stage_start = time.time()
    
    if pil_query_image:
        try:
            image_embedding = await clip_model.encode_image(pil_query_image)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Image encoding failed: {e}")
    
    if text_query and text_query.strip():
        try:
            text_embedding = await clip_model.encode_text(text_query.strip())
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Text encoding failed: {e}")
    
    # Determine search type
    if image_embedding is not None and text_embedding is not None:
        search_type = "hybrid"
    elif image_embedding is not None:
        search_type = "image"
    else:
        search_type = "text"
    
    pipeline_times["feature_extraction"] = time.time() - stage_start

    blip_captioner_adv = getattr(request.app.state, "blip_captioner", None)
    if pil_query_image is not None and blip_captioner_adv is not None:
        image_caption = await blip_captioner_adv.generate_caption(pil_query_image)
    
    # ══════════════════════════════════════════════════════════════════════════
    # STAGE 3: Multimodal Fusion Layer
    # ══════════════════════════════════════════════════════════════════════════
    stage_start = time.time()
    
    beta = 1.0 - alpha
    if image_embedding is not None and text_embedding is not None:
        fused = alpha * image_embedding + beta * text_embedding
    elif image_embedding is not None:
        fused = image_embedding
    else:
        fused = text_embedding  # type: ignore[assignment]
    
    fused = fused / (np.linalg.norm(fused) + 1e-9)
    
    pipeline_times["fusion"] = time.time() - stage_start
    
    # ══════════════════════════════════════════════════════════════════════════
    # STAGE 4: Query Understanding Module
    # ══════════════════════════════════════════════════════════════════════════
    stage_start = time.time()
    
    semantic_query_text = text_query or ""
    if image_caption:
        semantic_query_text = f"{semantic_query_text} {image_caption}".strip()

    structured_query = query_understanding_service.get_structured_query(
        semantic_query_text
    )
    query_attributes = structured_query["attributes"]
    kg_attributes = fashion_knowledge_graph.extract_attributes(semantic_query_text)
    query_attributes = _merge_list_dict(
        query_attributes,
        fashion_knowledge_graph.extract_attributes_for_pipeline(semantic_query_text),
    )

    image_inferred_attributes: Dict[str, Any] = {}
    if pil_query_image is not None and hasattr(clip_model, "infer_fashion_attributes"):
        try:
            image_inferred_attributes = await clip_model.infer_fashion_attributes(pil_query_image)
            query_attributes = _merge_list_dict(query_attributes, image_inferred_attributes)
        except Exception as e:
            logger.warning(f"Image attribute inference skipped in /recommend/advanced: {e}")

    expanded_query = structured_query["expanded"]
    
    logger.info(
        f"[Advanced] Query understanding: {query_attributes}, "
        f"intent={structured_query['intent']}, confidence={structured_query['confidence']:.2f}"
    )
    
    pipeline_times["query_understanding"] = time.time() - stage_start
    
    # ══════════════════════════════════════════════════════════════════════════
    # STAGE 5: Candidate Generation (Web Search + Product Index)
    # ══════════════════════════════════════════════════════════════════════════
    stage_start = time.time()
    
    # 5a. Web Search
    search_text = text_query
    if image_caption:
        search_text = f"{search_text} {image_caption}".strip() if search_text else image_caption
    if (not search_text or not search_text.strip()) and image_inferred_attributes:
        inferred_text = _attributes_to_search_text(image_inferred_attributes)
        if inferred_text:
            search_text = inferred_text

    search_phrase, full_query = query_generator.generate(text=search_text)
    logger.info(f"[Advanced] search_phrase='{search_phrase}' type={search_type}")
    
    try:
        web_candidates = await web_search_service.search(
            query=full_query,
            num_results=settings.SEARCH_NUM_RESULTS,
        )
        web_candidates = fashion_knowledge_graph.filter_candidates(web_candidates, query_attributes)
    except Exception as e:
        logger.error(f"Web search error: {e}")
        web_candidates = []
    
    # 5b. Product Index (FAISS)
    indexed_candidates = 0
    index_candidates = []
    
    if use_product_index:
        try:
            from app.services.product_catalog import get_product_catalog
            
            catalog = get_product_catalog()
            from app.services.query_understanding import QueryAttributes
            
            # Convert dict to QueryAttributes
            attrs = QueryAttributes(
                colors=query_attributes.get("colors", []),
                categories=query_attributes.get("categories", []),
                patterns=query_attributes.get("patterns", []),
                materials=query_attributes.get("materials", []),
                genders=query_attributes.get("genders", []),
                occasions=query_attributes.get("occasions", []),
                sleeve_types=query_attributes.get("sleeve_types", []),
                collar_types=query_attributes.get("collar_types", []),
                neckline_types=query_attributes.get("neckline_types", []),
                length_types=query_attributes.get("length_types", []),
                sole_types=query_attributes.get("sole_types", []),
                closure_types=query_attributes.get("closure_types", []),
                use_types=query_attributes.get("use_types", []),
                seasons=query_attributes.get("seasons", []),
            )
            
            similar_products = await catalog.search_similar_products(
                query_embedding=fused,
                top_k=100,
                attributes=attrs if any([
                    attrs.colors, attrs.categories, attrs.patterns,
                    attrs.materials, attrs.genders, attrs.occasions,
                    attrs.sleeve_types, attrs.collar_types, attrs.neckline_types,
                    attrs.length_types, attrs.sole_types, attrs.closure_types,
                    attrs.use_types, attrs.seasons
                ]) else None,
            )
            
            indexed_candidates = len(similar_products)
            
            # Convert to candidate format
            for product, similarity in similar_products:
                # Create mock candidate from product
                from app.services.web_search_service import CandidateProduct
                
                # Get image path
                image_path = catalog.repo_root / "data" / "images" / (product.image or "")
                
                if image_path.exists():
                    candidate = CandidateProduct(
                        title=product.title,
                        url=f"product://{product.id}",
                        image_url=str(image_path),
                        source=product.brand or "Catalog",
                        snippet=product.description[:200] if product.description else None,
                    )
                    index_candidates.append(candidate)
            
            logger.info(f"[Advanced] Found {indexed_candidates} products from index")
        
        except Exception as e:
            logger.warning(f"Product index search failed: {e}")
    
    total_candidates = len(web_candidates) + len(index_candidates)
    
    if total_candidates == 0:
        logger.warning("No candidates from web or index")
        query_time = time.time() - start_time
        return AdvancedRecommendResponse(
            results=[],
            total_results=0,
            query_time=round(query_time, 3),
            search_phrase=search_phrase,
            image_caption=image_caption,
            expanded_query=expanded_query,
            alpha_used=alpha,
            search_type=search_type,
            total_candidates=0,
            indexed_candidates=0,
            query_attributes=query_attributes,
            knowledge_graph_attributes=kg_attributes,
            pipeline_stages=pipeline_times,
        )
    
    pipeline_times["candidate_generation"] = time.time() - stage_start
    
    # ══════════════════════════════════════════════════════════════════════════
    # STAGE 6: Image Download & Validation
    # ══════════════════════════════════════════════════════════════════════════
    stage_start = time.time()
    
    # Combine candidates
    all_candidates = web_candidates + index_candidates
    
    # Download images
    image_urls = [c.image_url for c in all_candidates]
    downloaded = await download_images(
        urls=image_urls,
        timeout=settings.DOWNLOAD_TIMEOUT,
        max_concurrent=settings.MAX_CONCURRENT_DOWNLOADS,
    )
    
    url_to_meta = {c.image_url: c for c in all_candidates}
    
    pairs = []
    for url, pil_img in downloaded:
        meta = url_to_meta.get(url)
        if meta is None:
            continue
        pil_img = resize_image(pil_img, max_dim=800)
        if not validate_image(pil_img, min_dim=50):
            continue
        pairs.append((meta, pil_img))
    
    if not pairs:
        logger.warning("All candidate images failed to download or validate")
        query_time = time.time() - start_time
        return AdvancedRecommendResponse(
            results=[],
            total_results=0,
            query_time=round(query_time, 3),
            search_phrase=search_phrase,
            image_caption=image_caption,
            expanded_query=expanded_query,
            alpha_used=alpha,
            search_type=search_type,
            total_candidates=total_candidates,
            indexed_candidates=indexed_candidates,
            query_attributes=query_attributes,
            knowledge_graph_attributes=kg_attributes,
            pipeline_stages=pipeline_times,
        )
    
    pipeline_times["image_download"] = time.time() - stage_start
    
    # ══════════════════════════════════════════════════════════════════════════
    # STAGE 7: Multi-Stage Ranking
    # ══════════════════════════════════════════════════════════════════════════
    stage_start = time.time()
    
    from app.services.query_understanding import QueryAttributes as QA
    
    # Convert dict back to QueryAttributes object
    query_attrs_obj = QA(
        colors=query_attributes.get("colors", []),
        categories=query_attributes.get("categories", []),
        patterns=query_attributes.get("patterns", []),
        materials=query_attributes.get("materials", []),
        genders=query_attributes.get("genders", []),
        occasions=query_attributes.get("occasions", []),
        sleeve_types=query_attributes.get("sleeve_types", []),
        collar_types=query_attributes.get("collar_types", []),
        neckline_types=query_attributes.get("neckline_types", []),
        length_types=query_attributes.get("length_types", []),
        sole_types=query_attributes.get("sole_types", []),
        closure_types=query_attributes.get("closure_types", []),
        use_types=query_attributes.get("use_types", []),
        seasons=query_attributes.get("seasons", []),
    )
    
    ranked = await multi_stage_ranking_engine.rank(
        clip_model=clip_model,
        candidates=pairs,
        query_embedding=fused,
        query_text=semantic_query_text,
        query_attributes=query_attrs_obj,
        image_embedding=image_embedding,
        text_embedding=text_embedding,
        top_k=top_k * 2,  # Get more for filtering
    )
    
    pipeline_times["multi_stage_ranking"] = time.time() - stage_start
    
    # ══════════════════════════════════════════════════════════════════════════
    # STAGE 8: Recommendation Filtering
    # ══════════════════════════════════════════════════════════════════════════
    stage_start = time.time()
    
    if apply_filters:
        filtered = recommendation_filter.filter(
            ranked_products=ranked,
            remove_duplicates=True,
            check_quality=True,
            ensure_diversity=True,
            category_filter=query_attributes.get("categories", [None])[0] if query_attributes.get("categories") else None,
        )
    else:
        filtered = ranked
    
    # Limit to top_k
    final_results = filtered[:top_k]
    
    pipeline_times["filtering"] = time.time() - stage_start
    
    # ══════════════════════════════════════════════════════════════════════════
    # Build Response
    # ══════════════════════════════════════════════════════════════════════════
    
    results = [r.to_dict() for r in final_results]
    
    query_time = time.time() - start_time
    logger.info(
        f"[Advanced] done in {query_time:.2f}s | "
        f"candidates={total_candidates} (web={len(web_candidates)}, index={indexed_candidates}) "
        f"downloaded={len(pairs)} ranked={len(ranked)} filtered={len(final_results)}"
    )
    
    return AdvancedRecommendResponse(
        results=results,
        total_results=len(final_results),
        query_time=round(query_time, 3),
        search_phrase=search_phrase,
        image_caption=image_caption,
        expanded_query=expanded_query,
        alpha_used=alpha,
        search_type=search_type,
        total_candidates=total_candidates,
        indexed_candidates=indexed_candidates,
        query_attributes=query_attributes,
        knowledge_graph_attributes=kg_attributes,
        pipeline_stages=pipeline_times,
    )


# ── Health check for this pipeline ──────────────────────────────────────────

@recommend_router.get("/recommend/health")
async def recommend_health(request: Request):
    """Health check for the /recommend pipeline components."""
    clip_large = getattr(request.app.state, "clip_model_large", None)
    serp_key_set = bool(settings.SERP_API_KEY)

    status = "ready" if (clip_large and serp_key_set) else "degraded"
    return JSONResponse({
        "status": status,
        "clip_vit_l14_loaded": clip_large is not None,
        "serp_api_key_configured": serp_key_set,
        "model_used": "ViT-L/14",
        "search_domains": settings.SEARCH_DOMAINS,
        "top_k": settings.TOP_K,
        "alpha": settings.IMAGE_ALPHA,
    })
