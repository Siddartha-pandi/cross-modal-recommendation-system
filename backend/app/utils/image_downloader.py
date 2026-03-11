"""
Image Downloader Utility
Asynchronously downloads product images in parallel with caching and
graceful timeout/error handling.
"""
import asyncio
import hashlib
import logging
import os
from io import BytesIO
from typing import List, Optional, Tuple

import aiohttp
import diskcache
from PIL import Image

from app.config.settings import settings

logger = logging.getLogger(__name__)

# ── Disk cache setup ─────────────────────────────────────────────────────────
_cache = diskcache.Cache(settings.CACHE_DIR)

# Minimal browser-like headers to avoid 403s on e-commerce sites
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.google.com/",
}


def _cache_key(url: str) -> str:
    return "img_" + hashlib.md5(url.encode()).hexdigest()


async def _download_single(
    session: aiohttp.ClientSession,
    url: str,
    timeout: int,
) -> Optional[Image.Image]:
    """
    Download a single image URL and return a PIL Image (RGB).
    Returns None on any failure.
    """
    # Check disk cache first
    key = _cache_key(url)
    cached = _cache.get(key)
    if cached is not None:
        try:
            return Image.open(BytesIO(cached)).convert("RGB")
        except Exception:
            pass  # corrupted cache entry — re-download

    try:
        async with session.get(
            url,
            headers=_HEADERS,
            timeout=aiohttp.ClientTimeout(total=timeout),
            allow_redirects=True,
            ssl=False,
        ) as resp:
            if resp.status != 200:
                logger.debug(f"HTTP {resp.status} for {url[:60]}")
                return None
            raw = await resp.read()

        # Validate it's a real image
        img = Image.open(BytesIO(raw)).convert("RGB")

        # Store raw bytes in cache with TTL
        _cache.set(key, raw, expire=settings.CACHE_TTL)
        return img

    except asyncio.TimeoutError:
        logger.debug(f"Timeout downloading {url[:60]}")
        return None
    except Exception as e:
        logger.debug(f"Failed to download {url[:60]}: {e}")
        return None


async def download_images(
    urls: List[str],
    timeout: int = None,
    max_concurrent: int = None,
) -> List[Tuple[str, Image.Image]]:
    """
    Download a list of image URLs concurrently.

    Args:
        urls: List of image URLs to download.
        timeout: Per-image timeout in seconds (default from settings).
        max_concurrent: Maximum concurrent downloads (default from settings).

    Returns:
        List of (url, PIL.Image) tuples for successfully downloaded images,
        preserving the original ordering (failed downloads are omitted).
    """
    timeout = timeout or settings.DOWNLOAD_TIMEOUT
    max_concurrent = max_concurrent or settings.MAX_CONCURRENT_DOWNLOADS

    if not urls:
        return []

    semaphore = asyncio.Semaphore(max_concurrent)

    async def _bounded(url: str) -> Tuple[str, Optional[Image.Image]]:
        async with semaphore:
            img = await _download_single(session, url, timeout)
            return url, img

    connector = aiohttp.TCPConnector(limit=max_concurrent, ssl=False)
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [_bounded(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    successful: List[Tuple[str, Image.Image]] = []
    for result in results:
        if isinstance(result, Exception):
            logger.debug(f"Download task raised: {result}")
            continue
        url, img = result
        if img is not None:
            successful.append((url, img))

    logger.info(
        f"Downloaded {len(successful)}/{len(urls)} images "
        f"(skipped {len(urls) - len(successful)} failures)"
    )
    return successful
