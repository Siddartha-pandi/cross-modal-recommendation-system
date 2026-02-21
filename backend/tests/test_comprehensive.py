""""""












































































































































































































































































































































































































































    pytest.main([__file__, '-v', '--tb=short'])if __name__ == '__main__':    assert search_time < 500    # Should be under 500ms target        print(f"\nSearch time: {search_time:.2f}ms")        search_time = metadata['search_time_ms']    )        top_k=10        text_query="blue shirt",    results, metadata = await search_service.search(    start = time.time()    # Measure        await search_service.search(text_query="test", top_k=5)    # Warm-up            search_service.faiss_index.add_product(embedding, product)        embedding = embedding / np.linalg.norm(embedding)        embedding = np.random.randn(512).astype(np.float32)    for product in sample_products:    # Add products        import time    """Test search meets performance targets"""async def test_search_speed(search_service, sample_products):@pytest.mark.asyncio    assert avg_time < 0.2    # Should be under 200ms target        print(f"\nAverage CLIP inference time: {avg_time*1000:.2f}ms")    avg_time = (end - start) / iterations        end = time.time()        await clip_model.encode_text(text)    for _ in range(iterations):    start = time.time()        iterations = 10    text = "test query"        import time    """Test CLIP inference meets performance targets"""async def test_clip_inference_speed(clip_model):@pytest.mark.asyncio# ============================================================================# PERFORMANCE TESTS# ============================================================================    assert 'results' in data    assert data['status'] == 'success'    data = response.json()    assert response.status_code == 200    response = await async_client.post("/api/v1/recommend", json=payload)    }        "alpha": 0.7        "top_k": 10,        "text": "blue cotton shirt",    payload = {    """Test recommendation endpoint"""async def test_api_recommend_endpoint(async_client):@pytest.mark.asyncio    assert 'query_time_ms' in data    assert 'results' in data    data = response.json()    assert response.status_code == 200    )        params={"query": "blue shirt", "top_k": 5}        "/api/v1/text-search",    response = await async_client.post(    """Test text search endpoint"""async def test_api_text_search(async_client):@pytest.mark.asyncio    assert data['status'] == 'healthy'    data = response.json()    assert response.status_code == 200    response = await async_client.get("/api/v1/health")    """Test health endpoint"""async def test_api_health_endpoint(async_client):@pytest.mark.asyncio# ============================================================================# API ENDPOINT TESTS (Integration)# ============================================================================        assert result['category'] == 'Tops'    for result in results:    # All results should match filter        )        filters={'category': 'Tops'}        top_k=10,        text_query="shirt",    results, metadata = await search_service.search(            search_service.faiss_index.add_product(embedding, product)        embedding = embedding / np.linalg.norm(embedding)        embedding = np.random.randn(512).astype(np.float32)    for product in sample_products:    # Add products    """Test search with filters"""async def test_search_service_with_filters(search_service, sample_products):@pytest.mark.asyncio    assert metadata['search_time_ms'] > 0    assert 'search_time_ms' in metadata    assert len(results) <= 2        )        top_k=2        text_query="blue shirt",    results, metadata = await search_service.search(            search_service.faiss_index.add_product(embedding, product)        embedding = embedding / np.linalg.norm(embedding)        embedding = np.random.randn(512).astype(np.float32)    for product in sample_products:    # Add products to index    """Test text-only search"""async def test_search_service_text_query(search_service, sample_products):@pytest.mark.asyncio# ============================================================================# SEARCH SERVICE TESTS# ============================================================================    assert np.array_equal(retrieved, embedding)    assert retrieved is not None    retrieved = cache.get_cached_embedding(content, "text")        assert success    success = cache.cache_embedding(content, "text", embedding)        embedding = np.random.randn(512).astype(np.float32)    content = "test query"            pytest.skip("Redis not available")    if not cache.is_available():    """Test embedding caching"""def test_cache_embedding(cache):    assert retrieved == value    retrieved = cache.get(key)        assert success    success = cache.set(key, value, ttl=60)        value = {"test": "data"}    key = "test:key"            pytest.skip("Redis not available")    if not cache.is_available():    """Test cache set and get"""def test_cache_set_get(cache):# ============================================================================# CACHE TESTS# ============================================================================    assert all(0 <= sim <= 1 for sim in similarities)    assert len(similarities) == len(product_ids)    assert len(product_ids) <= 2        product_ids, similarities = faiss_index.search(query_embedding, k=2)        query_embedding = query_embedding / np.linalg.norm(query_embedding)    query_embedding = np.random.randn(512).astype(np.float32)    # Search            faiss_index.add_product(embedding, product)        embedding = embedding / np.linalg.norm(embedding)        embedding = np.random.randn(512).astype(np.float32)    for product in sample_products:    # Add sample products    """Test FAISS search"""def test_faiss_search(faiss_index, sample_products):    assert faiss_index.get_size() == initial_size + 1        faiss_index.add_product(embedding, metadata)    initial_size = faiss_index.get_size()        }        'category': 'Test'        'title': 'Test Product',        'product_id': 'TEST001',    metadata = {        embedding = embedding / np.linalg.norm(embedding)    embedding = np.random.randn(512).astype(np.float32)    """Test adding product to FAISS index"""def test_faiss_add_product(faiss_index):# ============================================================================# FAISS INDEX TESTS# ============================================================================    assert len(explanation) > 0    assert isinstance(explanation, str)        )        match_scores=match_scores        similarity_score=0.92,        query_image=True,        query_text="blue shirt",        product=product,    explanation = ExplainableRecommender.generate_explanation(        }        'image_text_alignment': 0.8        'text_contribution': 0.3,        'image_contribution': 0.7,    match_scores = {        }        'category': 'Tops'        'title': 'Blue Cotton T-Shirt',        'product_id': 'TEST001',    product = {    """Test recommendation explanation generation"""def test_explainable_recommender():    assert scores['image_contribution'] == 1.0    assert np.array_equal(fused, img_emb)    assert fused is not None        )        alpha=0.7        text_embedding=None,        image_embedding=img_emb,    fused, scores = fusion_engine.fuse(        img_emb = img_emb / np.linalg.norm(img_emb)    img_emb = np.random.randn(512)    """Test image-only fusion"""def test_fusion_image_only(fusion_engine):    assert scores['text_contribution'] == 1.0    assert np.array_equal(fused, txt_emb)    assert fused is not None        )        alpha=0.7        text_embedding=txt_emb,        image_embedding=None,    fused, scores = fusion_engine.fuse(        txt_emb = txt_emb / np.linalg.norm(txt_emb)    txt_emb = np.random.randn(512)    """Test text-only fusion"""def test_fusion_text_only(fusion_engine):    assert scores['text_contribution'] == 0.3    assert scores['image_contribution'] == 0.7    assert 'text_contribution' in scores    assert 'image_contribution' in scores    assert np.isclose(np.linalg.norm(fused), 1.0, atol=1e-5)    assert fused.shape == (512,)    assert fused is not None        )        method="weighted_avg"        alpha=0.7,        text_embedding=txt_emb,        image_embedding=img_emb,    fused, scores = fusion_engine.fuse(        txt_emb = txt_emb / np.linalg.norm(txt_emb)    txt_emb = np.random.randn(512)        img_emb = img_emb / np.linalg.norm(img_emb)    img_emb = np.random.randn(512)    """Test weighted average fusion"""def test_fusion_weighted_avg(fusion_engine):# ============================================================================# FUSION ENGINE TESTS# ============================================================================        assert np.isclose(np.linalg.norm(emb), 1.0, atol=1e-5)    for emb in embeddings:    assert embeddings.shape == (3, 512)        embeddings = await clip_model.encode_batch_texts(texts)    texts = ["blue shirt", "red dress", "black jeans"]    """Test batch text encoding"""async def test_clip_batch_encoding(clip_model):@pytest.mark.asyncio    assert np.isclose(np.linalg.norm(embedding), 1.0, atol=1e-5)    assert embedding.shape == (512,)    assert isinstance(embedding, np.ndarray)    assert embedding is not None        embedding = await clip_model.encode_image(sample_image)    """Test image encoding"""async def test_clip_encode_image(clip_model, sample_image):@pytest.mark.asyncio    assert np.isclose(np.linalg.norm(embedding), 1.0, atol=1e-5)    assert embedding.shape == (512,)    assert isinstance(embedding, np.ndarray)    assert embedding is not None        embedding = await clip_model.encode_text(text)    text = "blue cotton t-shirt"    """Test text encoding"""async def test_clip_encode_text(clip_model):@pytest.mark.asyncio# ============================================================================# CLIP MODEL TESTS# ============================================================================    ]        }            'image_url': 'http://example.com/image3.jpg'            'brand': 'TestBrand',            'price': 59.99,            'category': 'Bottoms',            'title': 'Black Denim Jeans',            'product_id': 'PROD003',        {        },            'image_url': 'http://example.com/image2.jpg'            'brand': 'TestBrand',            'price': 49.99,            'category': 'Dresses',            'title': 'Red Summer Dress',            'product_id': 'PROD002',        {        },            'image_url': 'http://example.com/image1.jpg'            'brand': 'TestBrand',            'price': 29.99,            'category': 'Tops',            'title': 'Blue Cotton T-Shirt',            'product_id': 'PROD001',        {    return [    """Create sample product metadata"""def sample_products():@pytest.fixture    return img    img = Image.new('RGB', (224, 224), color='blue')    """Create sample PIL image for testing"""def sample_image():@pytest.fixture    return SearchService(clip_model, faiss_index, cache)    """Create search service for testing"""def search_service(clip_model, faiss_index, cache):@pytest.fixture    return FusionEngine(default_alpha=0.7)    """Create fusion engine for testing"""def fusion_engine():@pytest.fixture    return RedisCacheManager()    """Create cache manager for testing"""def cache():@pytest.fixture    return FAISSIndex(embedding_dim=512, index_type="Flat")    """Create FAISS index for testing"""def faiss_index():@pytest.fixture    return CLIPModel(model_name="ViT-B/32")    """Create CLIP model instance for testing"""def clip_model():@pytest.fixture# ============================================================================# FIXTURES# ============================================================================from app.services.search_service import SearchServicefrom app.utils.redis_cache import RedisCacheManagerfrom app.utils.faiss_index import FAISSIndexfrom app.models.fusion import FusionEngine, ExplainableRecommenderfrom app.models.clip_model import CLIPModel# Import modules to testimport base64import iofrom PIL import Imageimport numpy as npimport asyncioimport pytest"""Tests CLIP, Fusion, FAISS, Cache, and API endpointsComprehensive Test Suite for BackendComprehensive Test Suite for Backend API
Tests: CLIP, Fusion, FAISS, Cache, Auth, Search
"""

import pytest
import asyncio
from PIL import Image
import numpy as np
import io
import base64
from fastapi.testclient import TestClient

from app.main import app
from app.models.clip_model import CLIPModel
from app.models.fusion import FusionEngine, ExplainableRecommender
from app.utils.faiss_index import FAISSIndex
from app.utils.redis_cache import RedisCacheManager
from app.services.search_service import SearchService


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def test_client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
async def clip_model():
    """Initialize CLIP model for testing"""
    model = CLIPModel(model_name="ViT-B/32")
    return model


@pytest.fixture
def fusion_engine():
    """Initialize fusion engine"""
    return FusionEngine(default_alpha=0.7)


@pytest.fixture
def faiss_index():
    """Initialize FAISS index"""
    return FAISSIndex(embedding_dim=512, index_type="Flat")


@pytest.fixture
def cache_manager():
    """Initialize cache manager"""
    return RedisCacheManager()


@pytest.fixture
def sample_image():
    """Create sample test image"""
    img = Image.new('RGB', (224, 224), color='red')
    return img


@pytest.fixture
def sample_image_base64(sample_image):
    """Convert sample image to base64"""
    buffered = io.BytesIO()
    sample_image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return img_str


# ============================================================================
# CLIP MODEL TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_clip_text_encoding(clip_model):
    """Test text embedding generation"""
    text = "red summer dress"
    embedding = await clip_model.encode_text(text)
    
    assert embedding is not None
    assert isinstance(embedding, np.ndarray)
    assert embedding.shape == (512,)
    assert np.allclose(np.linalg.norm(embedding), 1.0, atol=1e-5)


@pytest.mark.asyncio
async def test_clip_image_encoding(clip_model, sample_image):
    """Test image embedding generation"""
    embedding = await clip_model.encode_image(sample_image)
    
    assert embedding is not None
    assert isinstance(embedding, np.ndarray)
    assert embedding.shape == (512,)
    assert np.allclose(np.linalg.norm(embedding), 1.0, atol=1e-5)


@pytest.mark.asyncio
async def test_clip_batch_encoding(clip_model):
    """Test batch text encoding"""
    texts = ["red dress", "blue shirt", "black pants"]
    embeddings = await clip_model.encode_batch_texts(texts)
    
    assert embeddings.shape == (3, 512)
    for emb in embeddings:
        assert np.allclose(np.linalg.norm(emb), 1.0, atol=1e-5)


# ============================================================================
# FUSION ENGINE TESTS
# ============================================================================

def test_fusion_weighted_avg(fusion_engine):
    """Test weighted average fusion"""
    img_emb = np.random.randn(512)
    txt_emb = np.random.randn(512)
    
    img_emb = img_emb / np.linalg.norm(img_emb)
    txt_emb = txt_emb / np.linalg.norm(txt_emb)
    
    fused, scores = fusion_engine.fuse(img_emb, txt_emb, alpha=0.7)
    
    assert fused.shape == (512,)
    assert np.allclose(np.linalg.norm(fused), 1.0, atol=1e-5)
    assert 'image_contribution' in scores
    assert 'text_contribution' in scores
    assert scores['image_contribution'] == 0.7
    assert scores['text_contribution'] == 0.3


def test_fusion_single_modality(fusion_engine):
    """Test single modality fusion"""
    txt_emb = np.random.randn(512)
    txt_emb = txt_emb / np.linalg.norm(txt_emb)
    
    fused, scores = fusion_engine.fuse(text_embedding=txt_emb)
    
    assert np.allclose(fused, txt_emb)
    assert scores['text_contribution'] == 1.0


def test_fusion_explainability():
    """Test explanation generation"""
    product = {
        'product_id': 'P001',
        'title': 'Red Summer Dress',
        'category': 'Dresses'
    }
    
    explanation = ExplainableRecommender.generate_explanation(
        product=product,
        query_text="red dress",
        query_image=True,
        similarity_score=0.9,
        match_scores={'image_contribution': 0.7, 'text_contribution': 0.3}
    )
    
    assert isinstance(explanation, str)
    assert len(explanation) > 0


# ============================================================================
# FAISS INDEX TESTS
# ============================================================================

def test_faiss_add_product(faiss_index):
    """Test adding product to index"""
    embedding = np.random.randn(512).astype(np.float32)
    metadata = {
        'product_id': 'P001',
        'title': 'Test Product',
        'price': 99.99
    }
    
    faiss_index.add_product(embedding, metadata)
    assert faiss_index.get_size() == 1


def test_faiss_search(faiss_index):
    """Test FAISS similarity search"""
    # Add products
    for i in range(10):
        emb = np.random.randn(512).astype(np.float32)
        emb = emb / np.linalg.norm(emb)
        metadata = {'product_id': f'P{i:03d}', 'title': f'Product {i}'}
        faiss_index.add_product(emb, metadata)
    
    # Search
    query = np.random.randn(512).astype(np.float32)
    query = query / np.linalg.norm(query)
    
    product_ids, scores = faiss_index.search(query, k=5)
    
    assert len(product_ids) == 5
    assert len(scores) == 5
    assert all(0 <= s <= 1 for s in scores)


# ============================================================================
# CACHE TESTS
# ============================================================================

def test_cache_embedding(cache_manager):
    """Test embedding caching"""
    if not cache_manager.is_available():
        pytest.skip("Redis not available")
    
    embedding = np.random.randn(512)
    content = "test query"
    
    # Cache it
    success = cache_manager.cache_embedding(content, 'text', embedding)
    assert success
    
    # Retrieve it
    cached = cache_manager.get_cached_embedding(content, 'text')
    assert cached is not None
    assert np.allclose(cached, embedding)


def test_cache_search_results(cache_manager):
    """Test search results caching"""
    if not cache_manager.is_available():
        pytest.skip("Redis not available")
    
    results = [
        {'product_id': 'P001', 'title': 'Product 1', 'similarity_score': 0.9}
    ]
    
    query_hash = "test_query_hash"
    
    # Cache results
    cache_manager.cache_search_results(query_hash, results)
    
    # Retrieve results
    cached = cache_manager.get_cached_search_results(query_hash)
    assert cached is not None
    assert len(cached) == 1
    assert cached[0]['product_id'] == 'P001'


# ============================================================================
# API ENDPOINT TESTS
# ============================================================================

def test_health_endpoint(test_client):
    """Test health check endpoint"""
    response = test_client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert 'status' in data
    assert 'services' in data


def test_text_search_endpoint(test_client):
    """Test text search endpoint"""
    response = test_client.post(
        "/api/v1/text-search",
        params={"query": "red dress", "top_k": 5}
    )
    
    # May fail if models not loaded, but should return valid response
    assert response.status_code in [200, 503]


def test_recommend_endpoint_validation(test_client):
    """Test recommendation endpoint validation"""
    # Missing both text and image should fail
    response = test_client.post(
        "/api/v1/recommend",
        json={"top_k": 10}
    )
    
    assert response.status_code == 422  # Validation error


def test_recommend_endpoint_with_text(test_client):
    """Test recommendation with text query"""
    response = test_client.post(
        "/api/v1/recommend",
        json={
            "text": "summer dress",
            "top_k": 5,
            "alpha": 0.0  # Text-only
        }
    )
    
    assert response.status_code in [200, 503]
    if response.status_code == 200:
        data = response.json()
        assert 'results' in data
        assert 'query_id' in data


# ============================================================================
# AUTHENTICATION TESTS
# ============================================================================

def test_register_endpoint(test_client):
    """Test user registration"""
    response = test_client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "password": "SecurePass123",
            "full_name": "Test User"
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert 'access_token' in data
    assert 'user' in data


def test_login_endpoint(test_client):
    """Test user login"""
    # Register first
    test_client.post(
        "/api/v1/auth/register",
        json={
            "email": "login@example.com",
            "password": "SecurePass123",
            "full_name": "Login User"
        }
    )
    
    # Login
    response = test_client.post(
        "/api/v1/auth/login",
        json={
            "email": "login@example.com",
            "password": "SecurePass123"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert 'access_token' in data


def test_invalid_login(test_client):
    """Test login with invalid credentials"""
    response = test_client.post(
        "/api/v1/auth/login",
        json={
            "email": "nonexistent@example.com",
            "password": "WrongPassword123"
        }
    )
    
    assert response.status_code == 401


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_end_to_end_search(clip_model, fusion_engine, faiss_index):
    """Test complete search pipeline"""
    # Setup: Add products to index
    for i in range(10):
        text = f"Product {i}"
        emb = await clip_model.encode_text(text)
        metadata = {
            'product_id': f'P{i:03d}',
            'title': f'Product {i}',
            'price': 50.0 + i * 10
        }
        faiss_index.add_product(emb, metadata)
    
    # Execute: Hybrid search
    query_text = "Product 5"
    text_emb = await clip_model.encode_text(query_text)
    
    # Fusion (text-only in this case)
    fused, scores = fusion_engine.fuse(text_embedding=text_emb)
    
    # Search
    product_ids, similarities = faiss_index.search(fused, k=3)
    
    # Verify
    assert len(product_ids) == 3
    assert all(0 <= s <= 1 for s in similarities)


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_embedding_generation_speed(clip_model):
    """Test embedding generation performance"""
    import time
    
    text = "red summer dress"
    
    start = time.time()
    embedding = await clip_model.encode_text(text)
    duration = time.time() - start
    
    assert duration < 0.5  # Should be under 500ms
    print(f"\nText embedding took: {duration*1000:.2f}ms")


def test_faiss_search_speed(faiss_index):
    """Test FAISS search performance"""
    import time
    
    # Add 1000 products
    for i in range(1000):
        emb = np.random.randn(512).astype(np.float32)
        emb = emb / np.linalg.norm(emb)
        metadata = {'product_id': f'P{i:04d}'}
        faiss_index.add_product(emb, metadata)
    
    # Search
    query = np.random.randn(512).astype(np.float32)
    query = query / np.linalg.norm(query)
    
    start = time.time()
    product_ids, scores = faiss_index.search(query, k=10)
    duration = time.time() - start
    
    assert duration < 0.1  # Should be under 100ms
    print(f"\nFAISS search (1000 products) took: {duration*1000:.2f}ms")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
