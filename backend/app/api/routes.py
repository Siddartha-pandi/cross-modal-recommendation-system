"""
Simple, production-ready hybrid search endpoint
Implements: V_fusion = alpha * V_image + (1-alpha) * V_text
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import base64
import io
import time
import re
from PIL import Image
import numpy as np
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# ─────────────────────────────────────────────────────────────
# Category keyword mapping for query-aware filtering
# ─────────────────────────────────────────────────────────────
CATEGORY_KEYWORDS: Dict[str, List[str]] = {
    "tops":      ["t-shirt", "tshirt", "t shirt", "shirt", "tee", "top", "blouse",
                  "tunic", "kurti", "hoodie", "sweatshirt", "polo"],
    "dresses":   ["dress", "gown", "frock", "midi", "maxi"],
    "jackets":   ["jacket", "blazer", "coat", "windbreaker", "hoodie"],
    "bottoms":   ["jeans", "denim", "trousers", "pants", "shorts", "skirt",
                  "leggings", "palazzos"],
    "sarees":    ["saree", "sari"],
    "ethnic wear":["kurti", "kurta", "anarkali", "lehenga", "salwar",
                   "ethnic", "churidar"],
    "footwear":  ["shoes", "boots", "sneakers", "heels", "sandals",
                  "loafers", "flats", "chappal"],
    "accessories":["bag", "handbag", "purse", "watch", "scarf",
                   "belt", "cap", "hat", "sunglasses"],
}

# Colour & pattern vocab for query understanding
COLOR_KEYWORDS = [
    "red", "blue", "green", "black", "white", "yellow", "pink", "purple",
    "orange", "brown", "grey", "gray", "navy", "beige", "maroon", "olive",
    "teal", "cyan", "coral", "lavender", "cream", "gold", "silver",
]
PATTERN_KEYWORDS = [
    "floral", "striped", "stripes", "printed", "solid", "plain", "graphic",
    "checkered", "plaid", "dots", "polka", "embroidered", "abstract",
    "animal print", "camouflage", "geometric",
]


def analyse_query(text: str) -> Dict[str, Any]:
    """Extract category, colours and patterns from a text query."""
    lower = text.lower()
    detected_category: Optional[str] = None
    detected_colors: List[str] = []
    detected_patterns: List[str] = []

    # Detect category
    for cat, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw in lower:
                detected_category = cat
                break
        if detected_category:
            break

    # Detect colours
    for color in COLOR_KEYWORDS:
        if color in lower:
            detected_colors.append(color)

    # Detect patterns
    for pattern in PATTERN_KEYWORDS:
        if pattern in lower:
            detected_patterns.append(pattern)

    # Build human-readable intent
    parts = []
    if detected_colors:
        parts.append(detected_colors[0].title())
    if detected_patterns:
        parts.append(detected_patterns[0].title())
    if detected_category:
        parts.append(detected_category.title())
    intent = " ".join(parts) if parts else text.title()

    return {
        "detected_category": detected_category,
        "detected_colors":   detected_colors,
        "detected_patterns": detected_patterns,
        "intent":            intent,
    }


def filter_by_category(
    results: List[Dict[str, Any]],
    detected_category: Optional[str],
    fallback: List[Dict[str, Any]],
    top_k: int,
) -> List[Dict[str, Any]]:
    """
    Keep only results matching the detected category.
    Falls back to the original ranked list if fewer than `top_k` match.
    """
    if not detected_category:
        return results

    filtered = [
        r for r in results
        if detected_category.lower() in (r.get("category") or "").lower()
    ]

    # If too few filtered results, fall back to unfiltered to avoid empty pages
    if len(filtered) < max(1, top_k // 2):
        logger.info(
            f"Category filter '{detected_category}' yielded {len(filtered)} results "
            "– falling back to unfiltered"
        )
        return fallback[:top_k]

    return filtered[:top_k]

class SearchRequest(BaseModel):
    """Hybrid search request with adjustable alpha"""
    text: Optional[str] = Field(None, description="Text query")
    image: Optional[str] = Field(None, description="Base64 encoded image")
    alpha: float = Field(0.6, ge=0.0, le=1.0, description="Weight for image (0=text-only, 1=image-only)")
    top_k: int = Field(3, ge=1, le=50, description="Number of results to return")

class ProductResult(BaseModel):
    """Product search result – now includes per-result match scores for explainability"""
    product_id: str
    title: str
    description: Optional[str] = None
    image_url: str
    price: float
    category: Optional[str] = None
    color: Optional[str] = None
    pattern: Optional[str] = None
    similarity_score: float
    # Explainability scores (0-1)
    visual_score: Optional[float] = None
    text_score: Optional[float] = None
    final_score: Optional[float] = None
    matched_attributes: Optional[List[str]] = None

class SearchResponse(BaseModel):
    """Search response with results, metadata, and query analysis"""
    results: List[ProductResult]
    query_time: float
    total_results: int
    alpha_used: float
    search_type: str            # "text", "image", or "hybrid"
    fusion_info: Optional[dict] = None
    query_analysis: Optional[dict] = None  # Detected category / colour / pattern

@router.post("/search", response_model=SearchResponse)
async def hybrid_search(request: SearchRequest, app_request: Request):
    """
    Hybrid cross-modal search endpoint
    
    Implements fusion formula:
    V_fusion = alpha * V_image + (1-alpha) * V_text
    
    Where:
    - alpha ∈ [0, 1]: Weight for image embedding
    - (1-alpha): Weight for text embedding
    
    Search types:
    - Text-only: alpha = 0
    - Image-only: alpha = 1
    - Hybrid: 0 < alpha < 1
    """
    start_time = time.time()
    
    # Validate input
    if not request.text and not request.image:
        raise HTTPException(
            status_code=400, 
            detail="Either text or image must be provided"
        )
    
    # Get models from app state
    clip_model = getattr(app_request.app.state, 'clip_model', None)
    faiss_index = getattr(app_request.app.state, 'faiss_index', None)
    fusion_engine = getattr(app_request.app.state, 'fusion_engine', None)
    
    if not clip_model or not faiss_index:
        raise HTTPException(
            status_code=503, 
            detail="Models not yet loaded. Please wait."
        )
    
    try:
        # ── Step 1: Analyse text query ──────────────────────────────────────
        query_analysis: Dict[str, Any] = {}
        if request.text:
            query_analysis = analyse_query(request.text)

        # ── Step 2: Generate embeddings ──────────────────────────────────────
        text_embedding = None
        image_embedding = None
        search_type = "hybrid"

        if request.text:
            text_embedding = await clip_model.encode_text(request.text)
            search_type = "text"

        if request.image:
            try:
                base64_str = re.sub(r'^data:image/.+;base64,', '', request.image)
                missing_padding = len(base64_str) % 4
                if missing_padding:
                    base64_str += '=' * (4 - missing_padding)
                image_data = base64.b64decode(base64_str)
                image = Image.open(io.BytesIO(image_data)).convert('RGB')
                image_embedding = await clip_model.encode_image(image)
                search_type = "image" if not request.text else "hybrid"
            except Exception as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid image format: {str(e)}"
                )

        # ── Step 3: Fusion ───────────────────────────────────────────────────
        fusion_info: Dict[str, Any] = {}
        match_scores: Dict[str, float] = {}

        if fusion_engine and text_embedding is not None and image_embedding is not None:
            query_embedding, match_scores = fusion_engine.fuse(
                image_embedding=image_embedding,
                text_embedding=text_embedding,
                alpha=request.alpha,
                method="weighted_avg"
            )
            fusion_info = {
                "method": "FusionEngine",
                "match_scores": match_scores,
                "embedding_space": "CLIP joint space",
                "formula": f"V_fusion = {request.alpha:.2f}·V_image + {1-request.alpha:.2f}·V_text",
            }
        elif text_embedding is not None and image_embedding is not None:
            query_embedding = (
                request.alpha * image_embedding +
                (1 - request.alpha) * text_embedding
            )
            query_embedding = query_embedding / np.linalg.norm(query_embedding)
            fusion_info = {
                "method": "Manual weighted average",
                "formula": f"V_fusion = {request.alpha:.2f}·V_image + {1-request.alpha:.2f}·V_text",
            }
        elif image_embedding is not None:
            query_embedding = image_embedding
            fusion_info = {"method": "Image-only", "alpha": 1.0}
        else:
            query_embedding = text_embedding
            fusion_info = {"method": "Text-only", "alpha": 0.0}

        # ── Step 4: FAISS similarity search ─────────────────────────────────
        top_k = min(request.top_k, 3)
        # Fetch more candidates so the category filter has room to work
        candidate_k = min(top_k * 10, 50)
        raw_results, _ = faiss_index.search(
            query_embedding=query_embedding,
            top_k=candidate_k
        )

        # ── Step 5: Category filter ──────────────────────────────────────────
        detected_category = query_analysis.get("detected_category")
        filtered_results = filter_by_category(
            results=raw_results,
            detected_category=detected_category,
            fallback=raw_results,
            top_k=top_k,
        )

        # ── Step 5.1: Similarity Threshold Filter (>= 0.65) ──────────────────
        SIMILARITY_THRESHOLD = 0.65
        final_filtered_results = [
            r for r in filtered_results 
            if r.get("similarity_score", 0) >= SIMILARITY_THRESHOLD
        ]

        # Compute individual text/image similarity scores for explainability
        # We approximate:
        #   visual_score = cos-sim(image_emb, product_emb)  [0-1]
        #   text_score   = cos-sim(text_emb,  product_emb)  [0-1]
        #   final_score  = similarity_score as returned by FAISS
        def _cos_sim_0_1(a: np.ndarray, b: np.ndarray) -> float:
            """Cosine similarity mapped to [0, 1]."""
            norm_a = np.linalg.norm(a)
            norm_b = np.linalg.norm(b)
            if norm_a == 0 or norm_b == 0:
                return 0.5
            raw = float(np.dot(a, b) / (norm_a * norm_b))
            return float((raw + 1.0) / 2.0)

        # ── Step 6: Build response ────────────────────────────────────────────
        product_results = []
        detected_colors   = query_analysis.get("detected_colors", [])
        detected_patterns = query_analysis.get("detected_patterns", [])

        for result in final_filtered_results[:top_k]:
            sim = float(result['similarity_score'])

            # Per-product explainability scores
            if image_embedding is not None and text_embedding is not None:
                # Approximate individual-modality scores
                visual = match_scores.get('image_contribution', request.alpha) * sim * 1.2
                text   = match_scores.get('text_contribution', 1 - request.alpha) * sim * 1.2
                visual = min(visual, 1.0)
                text   = min(text, 1.0)
            elif image_embedding is not None:
                visual, text = sim, 0.0
            else:
                visual, text = 0.0, sim
            final = sim

            # Matched attributes
            attrs: List[str] = []
            prod_color   = (result.get('color') or '').lower()
            prod_pattern = (result.get('pattern') or '').lower()
            prod_title   = (result.get('title') or '').lower()
            prod_cat     = (result.get('category') or '').lower()

            for c in detected_colors:
                if c in prod_color or c in prod_title:
                    attrs.append(f"Color: {c.title()}")
                    break
            for p in detected_patterns:
                if p in prod_pattern or p in prod_title:
                    attrs.append(f"Pattern: {p.title()}")
                    break
            if detected_category and detected_category in prod_cat:
                attrs.append(f"Category: {prod_cat.title()}")
            if visual > 0.6:
                attrs.append("Visual Similarity")
            if text > 0.5:
                attrs.append("Text Match")
            if sim > 0.75:
                attrs.append("High Relevance")

            product_results.append(ProductResult(
                product_id=str(result['product_id']),
                title=result['title'],
                description=result.get('description', ''),
                image_url=result['image_url'],
                price=result.get('price', 0.0),
                category=result.get('category', ''),
                color=result.get('color', ''),
                pattern=result.get('pattern', ''),
                similarity_score=sim,
                visual_score=round(visual, 3),
                text_score=round(text, 3),
                final_score=round(final, 3),
                matched_attributes=attrs if attrs else None,
            ))

        query_time = time.time() - start_time

        return SearchResponse(
            results=product_results,
            query_time=query_time,
            total_results=len(product_results),
            alpha_used=request.alpha,
            search_type=search_type,
            fusion_info=fusion_info,
            query_analysis=query_analysis if query_analysis else None,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Search error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Search failed: {str(e)}"
        )

@router.get("/health")
async def health_check(request: Request):
    """Health check endpoint with search provider status"""
    from app.config.settings import settings
    
    clip_model = getattr(request.app.state, 'clip_model', None)
    faiss_index = getattr(request.app.state, 'faiss_index', None)
    
    # Check search provider configuration
    search_provider = settings.SEARCH_PROVIDER.lower()
    search_status = {"provider": search_provider}
    
    if search_provider in ["serpapi", "serapi"]:
        search_status["serpapi_configured"] = bool(settings.SERP_API_KEY and settings.SERP_API_KEY.strip())
        search_status["google_fallback_configured"] = bool(
            settings.GOOGLE_API_KEY and settings.GOOGLE_API_KEY.strip() and 
            settings.GOOGLE_CX and settings.GOOGLE_CX.strip()
        )
    elif search_provider == "google":
        search_status["google_configured"] = bool(
            settings.GOOGLE_API_KEY and settings.GOOGLE_API_KEY.strip() and 
            settings.GOOGLE_CX and settings.GOOGLE_CX.strip()
        )
    elif search_provider == "duckduckgo":
        search_status["requires_api_key"] = False
    
    return JSONResponse({
        "status": "healthy",
        "clip_model_loaded": clip_model is not None,
        "faiss_index_loaded": faiss_index is not None,
        "total_products": faiss_index.get_total_products() if faiss_index else 0,
        "search": search_status
    })

@router.get("/stats")
async def get_stats(request: Request):
    """Get index statistics"""
    faiss_index = getattr(request.app.state, 'faiss_index', None)
    
    if not faiss_index:
        raise HTTPException(status_code=503, detail="Index not loaded")
    
    stats = faiss_index.get_statistics()
    return JSONResponse(stats)

@router.get("/products/{product_id}")
async def get_product(product_id: str, request: Request):
    """Get product details by ID"""
    faiss_index = getattr(request.app.state, 'faiss_index', None)
    
    if not faiss_index:
        raise HTTPException(status_code=503, detail="Index not loaded")
    
    try:
        # Get product from index metadata
        product = faiss_index.get_product_by_id(product_id)
        
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {product_id} not found")
        
        return JSONResponse(product)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching product {product_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch product: {str(e)}")
