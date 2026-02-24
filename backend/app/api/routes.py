"""
Simple, production-ready hybrid search endpoint
Implements: V_fusion = alpha * V_image + (1-alpha) * V_text
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List
import base64
import io
import time
from PIL import Image
import numpy as np
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

class SearchRequest(BaseModel):
    """Hybrid search request with adjustable alpha"""
    text: Optional[str] = Field(None, description="Text query")
    image: Optional[str] = Field(None, description="Base64 encoded image")
    alpha: float = Field(0.5, ge=0.0, le=1.0, description="Weight for image (0=text-only, 1=image-only)")
    top_k: int = Field(3, ge=1, le=3, description="Number of results to return")

class ProductResult(BaseModel):
    """Product search result"""
    product_id: str
    title: str
    description: Optional[str] = None
    image_url: str
    price: float
    category: Optional[str] = None
    similarity_score: float

class SearchResponse(BaseModel):
    """Search response with results and metadata"""
    results: List[ProductResult]
    query_time: float
    total_results: int
    alpha_used: float
    search_type: str  # "text", "image", or "hybrid"
    fusion_info: Optional[dict] = None  # Match scores and explainability

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
        # Step 1: Generate embeddings based on input
        text_embedding = None
        image_embedding = None
        search_type = "hybrid"
        
        if request.text:
            text_embedding = await clip_model.encode_text(request.text)
            search_type = "text"
        
        if request.image:
            # Decode base64 image
            try:
                image_data = base64.b64decode(request.image)
                image = Image.open(io.BytesIO(image_data)).convert('RGB')
                image_embedding = await clip_model.encode_image(image)
                search_type = "image" if not request.text else "hybrid"
            except Exception as e:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Invalid image format: {str(e)}"
                )
        
        # Step 2: Apply fusion formula using FusionEngine
        # V_fusion = alpha * V_image + (1-alpha) * V_text
        fusion_info = {}
        
        if fusion_engine and text_embedding is not None and image_embedding is not None:
            # Use FusionEngine for explainability
            _, match_scores = fusion_engine.fuse(
                image_embedding=image_embedding,
                text_embedding=text_embedding,
                alpha=request.alpha,
                method="weighted_avg"
            )
            fusion_info = {
                "method": "Dynamic Alpha Fusion",
                "match_scores": match_scores,
                "embedding_space": "CLIP joint space",
                "formula": f"V_fusion = {request.alpha:.2f} * V_image + {1-request.alpha:.2f} * V_text",
                "note": "Products re-scored with same alpha for consistency"
            }
        elif text_embedding is not None and image_embedding is not None:
            fusion_info = {
                "method": "Dynamic Alpha Fusion",
                "formula": f"V_fusion = {request.alpha:.2f} * V_image + {1-request.alpha:.2f} * V_text",
                "note": "Products re-scored with same alpha for consistency"
            }
        elif image_embedding is not None:
            fusion_info = {"method": "Image-only", "alpha": 1.0}
        else:
            fusion_info = {"method": "Text-only", "alpha": 0.0}
        
        # Step 3: FAISS hybrid search with dynamic alpha
        top_k = min(request.top_k, 3)
        results, scores = faiss_index.hybrid_search(
            text_embedding=text_embedding,
            image_embedding=image_embedding,
            alpha=request.alpha,
            top_k=top_k
        )
        
        # Step 4: Format response
        product_results = []
        for result in results:
            product_results.append(ProductResult(
                product_id=str(result['product_id']),
                title=result['title'],
                description=result.get('description', ''),
                image_url=result['image_url'],
                price=result.get('price', 0.0),
                category=result.get('category', ''),
                similarity_score=float(result['similarity_score'])
            ))
        
        query_time = time.time() - start_time
        
        return SearchResponse(
            results=product_results,
            query_time=query_time,
            total_results=len(product_results),
            alpha_used=request.alpha,
            search_type=search_type,
            fusion_info=fusion_info
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
    """Health check endpoint"""
    clip_model = getattr(request.app.state, 'clip_model', None)
    faiss_index = getattr(request.app.state, 'faiss_index', None)
    
    return JSONResponse({
        "status": "healthy",
        "clip_model_loaded": clip_model is not None,
        "faiss_index_loaded": faiss_index is not None,
        "total_products": faiss_index.get_total_products() if faiss_index else 0
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
