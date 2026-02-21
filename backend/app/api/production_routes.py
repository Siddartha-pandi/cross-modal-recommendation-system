"""
Comprehensive API Routes - Phase 2 Production Ready
Implements all 12+ endpoints from API specification
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Request, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
import base64
import io
import time
import uuid
from PIL import Image
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class RecommendationRequest(BaseModel):
    """Main recommendation request"""
    text: Optional[str] = Field(None, description="Text query")
    image: Optional[str] = Field(None, description="Base64-encoded image")
    top_k: int = Field(default=10, ge=1, le=100, description="Number of results")
    alpha: float = Field(default=0.7, ge=0.0, le=1.0, description="Image weight (1-alpha = text weight)")
    fusion_method: str = Field(default="weighted_avg", description="Fusion method")
    category: Optional[str] = Field(None, description="Filter by category")
    price_min: Optional[float] = Field(None, ge=0, description="Minimum price")
    price_max: Optional[float] = Field(None, ge=0, description="Maximum price")
    diversity_weight: float = Field(default=0.0, ge=0.0, le=1.0, description="Diversity penalty weight")
    
    @validator('text', 'image')
    def check_at_least_one(cls, v, values):
        if not v and 'text' in values and not values.get('text'):
            raise ValueError('Either text or image must be provided')
        return v


class ProductRecommendation(BaseModel):
    """Single product result"""
    product_id: str
    title: str
    price: Optional[float] = None
    category: Optional[str] = None
    brand: Optional[str] = None
    image_url: str
    rating: Optional[float] = None
    review_count: Optional[int] = None
    similarity_score: float = Field(..., ge=0.0, le=1.0)
    rank: int
    match_explanation: Optional[str] = None


class RecommendationResponse(BaseModel):
    """API response for recommendations"""
    status: str = "success"
    query_id: str
    results: List[ProductRecommendation]
    total_results: int
    query_time_ms: float
    metadata: Dict[str, Any] = {}


class ProductDetailResponse(BaseModel):
    """Detailed product information"""
    product_id: str
    title: str
    description: Optional[str] = None
    price: Optional[float] = None
    category: Optional[str] = None
    brand: Optional[str] = None
    images: List[str] = []
    rating: Optional[float] = None
    review_count: Optional[int] = None
    specifications: Optional[Dict[str, Any]] = None
    availability: bool = True


class SimilarProductsResponse(BaseModel):
    """Similar products response"""
    product_id: str
    similar_products: List[ProductRecommendation]
    count: int


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: float
    services: Dict[str, str]
    index_size: int


# ============================================================================
# CORE RECOMMENDATION ENDPOINTS
# ============================================================================

@router.post("/recommend", response_model=RecommendationResponse)
async def get_recommendations(
    request: RecommendationRequest,
    app_request: Request
):
    """
    Main recommendation endpoint - hybrid text + image search
    
    - **text**: Optional text query
    - **image**: Optional base64-encoded image
    - **top_k**: Number of results (1-100)
    - **alpha**: Image weight (0-1), text weight = 1-alpha
    - **fusion_method**: 'weighted_avg', 'concatenation', or 'element_wise'
    - **filters**: Optional category, price range
    """
    start_time = time.time()
    query_id = str(uuid.uuid4())
    
    try:
        # Get search service
        search_service = getattr(app_request.app.state, 'search_service', None)
        if not search_service:
            raise HTTPException(status_code=503, detail="Search service not available")
        
        # Parse image if provided
        image_obj = None
        if request.image:
            try:
                image_data = base64.b64decode(request.image)
                image_obj = Image.open(io.BytesIO(image_data)).convert('RGB')
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Invalid image format: {str(e)}")
        
        # Build filters
        filters = {}
        if request.category:
            filters['category'] = request.category
        if request.price_min is not None:
            filters['price_min'] = request.price_min
        if request.price_max is not None:
            filters['price_max'] = request.price_max
        
        # Execute search
        results, metadata = await search_service.search(
            text_query=request.text,
            image_query=image_obj,
            top_k=request.top_k,
            alpha=request.alpha,
            fusion_method=request.fusion_method,
            filters=filters if filters else None,
            diversity_weight=request.diversity_weight
        )
        
        # Format response
        recommendations = [
            ProductRecommendation(
                product_id=r['product_id'],
                title=r['title'],
                price=r.get('price'),
                category=r.get('category'),
                brand=r.get('brand'),
                image_url=r.get('image_url', ''),
                rating=r.get('rating'),
                review_count=r.get('review_count'),
                similarity_score=r['similarity_score'],
                rank=idx + 1,
                match_explanation=r.get('match_explanation')
            )
            for idx, r in enumerate(results)
        ]
        
        query_time = (time.time() - start_time) * 1000
        
        return RecommendationResponse(
            status="success",
            query_id=query_id,
            results=recommendations,
            total_results=len(recommendations),
            query_time_ms=query_time,
            metadata=metadata
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Recommendation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/text-search", response_model=RecommendationResponse)
async def text_search(
    query: str = Query(..., min_length=1, max_length=500),
    top_k: int = Query(default=10, ge=1, le=100),
    category: Optional[str] = None,
    price_min: Optional[float] = None,
    price_max: Optional[float] = None,
    app_request: Request = None
):
    """
    Text-only search endpoint
    
    - **query**: Text search query (required)
    - **top_k**: Number of results
    - **filters**: Optional category and price range
    """
    req = RecommendationRequest(
        text=query,
        top_k=top_k,
        category=category,
        price_min=price_min,
        price_max=price_max,
        alpha=0.0  # Text-only
    )
    return await get_recommendations(req, app_request)


@router.post("/image-search", response_model=RecommendationResponse)
async def image_search(
    file: UploadFile = File(...),
    top_k: int = Query(default=10, ge=1, le=100),
    category: Optional[str] = None,
    price_min: Optional[float] = None,
    price_max: Optional[float] = None,
    app_request: Request = None
):
    """
    Image-only search endpoint
    
    - **file**: Image file upload
    - **top_k**: Number of results
    - **filters**: Optional category and price range
    """
    try:
        # Read and validate image
        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
        
        # Convert to base64
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        img_b64 = base64.b64encode(buffered.getvalue()).decode()
        
        req = RecommendationRequest(
            image=img_b64,
            top_k=top_k,
            category=category,
            price_min=price_min,
            price_max=price_max,
            alpha=1.0  # Image-only
        )
        return await get_recommendations(req, app_request)
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image: {str(e)}")


# ============================================================================
# PRODUCT ENDPOINTS
# ============================================================================

@router.get("/products/{product_id}", response_model=ProductDetailResponse)
async def get_product_detail(
    product_id: str,
    app_request: Request
):
    """
    Get detailed product information
    
    - **product_id**: Unique product identifier
    """
    search_service = getattr(app_request.app.state, 'search_service', None)
    if not search_service:
        raise HTTPException(status_code=503, detail="Service unavailable")
    
    product = search_service.get_product_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return ProductDetailResponse(
        product_id=product['product_id'],
        title=product.get('title', ''),
        description=product.get('description'),
        price=product.get('price'),
        category=product.get('category'),
        brand=product.get('brand'),
        images=[product.get('image_url', '')],
        rating=product.get('rating'),
        review_count=product.get('review_count'),
        specifications=product.get('specifications'),
        availability=product.get('availability', True)
    )


@router.get("/products/{product_id}/similar", response_model=SimilarProductsResponse)
async def get_similar_products(
    product_id: str,
    top_k: int = Query(default=10, ge=1, le=50),
    app_request: Request = None
):
    """
    Find visually similar products
    
    - **product_id**: Reference product ID
    - **top_k**: Number of similar products
    """
    search_service = getattr(app_request.app.state, 'search_service', None)
    if not search_service:
        raise HTTPException(status_code=503, detail="Service unavailable")
    
    similar = await search_service.get_similar_products(product_id, top_k)
    
    recommendations = [
        ProductRecommendation(
            product_id=s['product_id'],
            title=s.get('title', ''),
            price=s.get('price'),
            category=s.get('category'),
            brand=s.get('brand'),
            image_url=s.get('image_url', ''),
            rating=s.get('rating'),
            similarity_score=s['similarity_score'],
            rank=idx + 1
        )
        for idx, s in enumerate(similar)
    ]
    
    return SimilarProductsResponse(
        product_id=product_id,
        similar_products=recommendations,
        count=len(recommendations)
    )


# ============================================================================
# UTILITY ENDPOINTS
# ============================================================================

@router.get("/health", response_model=HealthResponse)
async def health_check(app_request: Request):
    """
    Health check endpoint
    """
    clip_model = getattr(app_request.app.state, 'clip_model', None)
    faiss_index = getattr(app_request.app.state, 'faiss_index', None)
    cache = getattr(app_request.app.state, 'cache', None)
    
    services = {
        'clip_model': 'healthy' if clip_model else 'unavailable',
        'faiss_index': 'healthy' if faiss_index else 'unavailable',
        'cache': 'healthy' if (cache and cache.is_available()) else 'degraded'
    }
    
    index_size = faiss_index.get_size() if faiss_index else 0
    
    return HealthResponse(
        status="healthy",
        timestamp=time.time(),
        services=services,
        index_size=index_size
    )


@router.get("/cache/stats")
async def get_cache_stats(app_request: Request):
    """
    Get cache statistics
    """
    cache = getattr(app_request.app.state, 'cache', None)
    if not cache:
        raise HTTPException(status_code=503, detail="Cache not available")
    
    stats = cache.get_stats()
    return JSONResponse(content=stats)


@router.post("/cache/invalidate")
async def invalidate_cache(
    pattern: str = Query(default="*", description="Pattern to invalidate"),
    app_request: Request = None
):
    """
    Invalidate cache entries (admin endpoint)
    """
    cache = getattr(app_request.app.state, 'cache', None)
    if not cache:
        raise HTTPException(status_code=503, detail="Cache not available")
    
    count = cache.invalidate_pattern(f"cmrs:{pattern}")
    return {"status": "success", "invalidated_keys": count}


# ============================================================================
# ADMIN ENDPOINTS (Placeholder for Phase 5)
# ============================================================================

@router.get("/admin/stats")
async def get_system_stats(app_request: Request):
    """
    System statistics dashboard (Phase 5)
    """
    return {
        "status": "Phase 5 - Coming Soon",
        "message": "Admin dashboard statistics"
    }


@router.get("/admin/logs")
async def get_search_logs(
    limit: int = Query(default=100, ge=1, le=1000),
    app_request: Request = None
):
    """
    Search logs for analytics (Phase 5)
    """
    return {
        "status": "Phase 5 - Coming Soon",
        "message": "Search query logs"
    }
