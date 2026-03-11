"""
Centralised application settings using Pydantic-Settings.
All values can be overridden via environment variables or a .env file.
"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # ── CLIP Model ────────────────────────────────────────────────────────────
    # ViT-L/14 is used for the live /recommend pipeline (1024-dim embeddings)
    CLIP_MODEL_LARGE: str = "ViT-L/14"
    # ViT-B/32 is kept for the existing FAISS /search pipeline (512-dim)
    CLIP_MODEL_SMALL: str = "ViT-B/32"
    
    # ── BLIP Model ───────────────────────────────────────────────────────────
    # Upgrade to 'large' for higher captioning accuracy (approx. 1.8GB)
    BLIP_MODEL: str = "Salesforce/blip-image-captioning-large"

    # ── Web Search Provider ───────────────────────────────────────────────────
    # Options: "serpapi" (or alias "serapi") | "google" | "duckduckgo"
    # Recommended default for this project: SerpAPI (Google-backed results)
    SEARCH_PROVIDER: str = "serpapi"

    # ── Google Custom Search API (100 free queries/day) ───────────────────────
    GOOGLE_API_KEY: str = ""    # From Google Cloud Console → Credentials
    GOOGLE_CX: str = ""         # Custom Search Engine ID (Programmable Search Engine)

    # ── SerpAPI (legacy / fallback) ───────────────────────────────────────────
    SERP_API_KEY: str = ""

    # Common search settings
    # Target candidate pool for ranking should typically be 30-50.
    SEARCH_NUM_RESULTS: int = 40

    # Target e-commerce domains (restricted search)
    SEARCH_DOMAINS: List[str] = [
        "myntra.com",
        "amazon.in",
        "flipkart.com",
        "ajio.com",
        "zara.com",
        "hm.com",
    ]

    # ── Embedding Fusion ─────────────────────────────────────────────────────
    IMAGE_ALPHA: float = 0.6   # Weight for image embedding
    TEXT_BETA: float = 0.4     # Weight for text embedding (= 1 - alpha)

    # ── Retrieval ────────────────────────────────────────────────────────────
    TOP_K: int = 10             # Top-K results to return
    MAX_CANDIDATES: int = 50    # Max candidate products from web search

    # ── Image Downloader ─────────────────────────────────────────────────────
    DOWNLOAD_TIMEOUT: int = 8   # Per-image download timeout (seconds)
    MAX_CONCURRENT_DOWNLOADS: int = 10

    # ── Cache ─────────────────────────────────────────────────────────────────
    CACHE_TTL: int = 3600       # Cache TTL in seconds (1 hour)
    CACHE_DIR: str = "/tmp/fashion_recommend_cache"

    # ── API Server ────────────────────────────────────────────────────────────
    HOST: str = "0.0.0.0"
    PORT: int = 8001
    DEBUG: bool = False

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"


# Singleton instance — import this everywhere
settings = Settings()
