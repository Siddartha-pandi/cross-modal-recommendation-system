
"""
Web Search Service
Multi-provider fashion product image search with automatic fallback:

  1. DuckDuckGo (ddg_images via duckduckgo_search) — no API key, retry-aware
  2. Google Custom Search API                       — 100/day free (optional)
  3. SerpAPI                                        — 100/month free (optional)

Provider selected by SEARCH_PROVIDER in .env.
Primary flow for this project uses SerpAPI and Google Custom Search.
"""
import asyncio
import logging
import time
import random
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field

from app.config.settings import settings

logger = logging.getLogger(__name__)

_executor = ThreadPoolExecutor(max_workers=2)

def _extract_price(item: dict) -> Optional[str]:
    """Try to extract price from item['price'], snippet, or title."""
    # 1. Direct price field
    price = item.get("price")
    if price not in [None, '', 0, 0.0]:
        return str(price)
    # 2. Try snippet
    snippet = item.get("snippet", "")
    # 3. Try title
    title = item.get("title", "")
    import re
    for text in [snippet, title]:
        # Look for patterns like ₹1234, Rs. 1234, INR 1234
        match = re.search(r'(₹|Rs\.?|INR)[ ]?([0-9,]+)', text)
        if match:
            return match.group(1) + match.group(2).replace(",", "")
    return None

"""
Web Search Service
Multi-provider fashion product image search with automatic fallback:

    1. DuckDuckGo (ddg_images via duckduckgo_search) — no API key, retry-aware
    2. Google Custom Search API                       — 100/day free (optional)
    3. SerpAPI                                        — 100/month free (optional)

Provider selected by SEARCH_PROVIDER in .env.
Primary flow for this project uses SerpAPI and Google Custom Search.
"""
import asyncio
import logging
import time
import random
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field

from app.config.settings import settings

logger = logging.getLogger(__name__)

_executor = ThreadPoolExecutor(max_workers=2)


@dataclass
class CandidateProduct:
    """A candidate product retrieved from web search."""
    title:     str
    url:       str
    image_url: str
    source:    str
    position:  int = 0
    snippet:   Optional[str] = None
    price:     Optional[str] = None
    extra:     Dict[str, Any] = field(default_factory=dict)


def _extract_source(url: str) -> str:
    lower = url.lower()
    if "myntra"   in lower: return "Myntra"
    if "amazon"   in lower: return "Amazon"
    if "flipkart" in lower: return "Flipkart"
    if "ajio"     in lower: return "AJIO"
    return "E-Commerce"


def _domain_ok(url: str, domains: List[str]) -> bool:
    return any(d in url.lower() for d in domains)


# ─────────────────────────────────────────────────────────────────────────────
# Provider 1: DuckDuckGo (with retry + back-off)
# ─────────────────────────────────────────────────────────────────────────────

def _ddg_sync(query: str, max_results: int, retries: int = 3) -> List[Dict]:
    """
    Synchronous DuckDuckGo image search with exponential back-off on rate-limits.
    Runs inside a thread pool so it won't block the FastAPI event loop.
    """
    from ddgs import DDGS
    from ddgs.exceptions import RatelimitException, DDGSException

    for attempt in range(retries):
        try:
            with DDGS() as ddgs:
                results = list(ddgs.images(query, max_results=max_results, safesearch="moderate"))
            logger.info(f"DDG attempt {attempt+1}: got {len(results)} raw results")
            return results
        except RatelimitException:
            wait = 2 ** attempt + random.uniform(0, 1)
            logger.warning(f"DDG rate-limited (attempt {attempt+1}/{retries}). Waiting {wait:.1f}s…")
            time.sleep(wait)
        except DDGSException as e:
            logger.warning(f"DDG search error (attempt {attempt+1}): {e}")
            time.sleep(1)
        except Exception as e:
            logger.error(f"Unexpected DDG error: {e}")
            break

    return []


async def _search_duckduckgo(query: str, num: int) -> List[CandidateProduct]:
    """Async wrapper for DuckDuckGo image search."""
    loop = asyncio.get_event_loop()
    raw = await loop.run_in_executor(_executor, _ddg_sync, query, num * 3)

    candidates: List[CandidateProduct] = []
    seen: set = set()

    for i, item in enumerate(raw):
        image_url = item.get("image") or item.get("thumbnail", "")
        page_url  = item.get("url", "")
        title     = item.get("title", "").strip()

        if not (image_url and page_url and title):
            continue
        if page_url in seen:
            continue
        if not _domain_ok(page_url, settings.SEARCH_DOMAINS) and \
           not _domain_ok(image_url, settings.SEARCH_DOMAINS):
            continue

        seen.add(page_url)
        candidates.append(CandidateProduct(
            title=title, url=page_url, image_url=image_url,
            source=_extract_source(page_url),
            position=i,
        ))

        if len(candidates) >= num:
            break

    logger.info(f"DDG: {len(candidates)} domain-matched candidates")
    return candidates


# ─────────────────────────────────────────────────────────────────────────────
# Provider 2: Google Custom Search API
# ─────────────────────────────────────────────────────────────────────────────

async def _search_google(query: str, num: int) -> List[CandidateProduct]:
    import aiohttp
    if not settings.GOOGLE_API_KEY or not settings.GOOGLE_CX:
        raise RuntimeError(
            "GOOGLE_API_KEY or GOOGLE_CX not set in backend/.env\n"
            "To set up Google Custom Search API:\n"
            "1. Enable 'Custom Search JSON API' at https://console.cloud.google.com/apis/library\n"
            "2. Create API key at https://console.cloud.google.com/apis/credentials\n"
            "3. Create Custom Search Engine at https://programmablesearchengine.google.com/\n"
            "4. Add GOOGLE_API_KEY and GOOGLE_CX to backend/.env"
        )

    timeout      = aiohttp.ClientTimeout(total=20)
    target_count = min(num, settings.MAX_CANDIDATES)
    per_page     = min(target_count, 10)
    pages        = max(1, (target_count + per_page - 1) // per_page)
    candidates: List[CandidateProduct] = []
    seen: set    = set()

    async with aiohttp.ClientSession(timeout=timeout) as session:
        for page in range(pages):
            params = {
                "key": settings.GOOGLE_API_KEY,
                "cx":  settings.GOOGLE_CX,
                "q":   query,
                "num": str(per_page),
                "start": str(page * per_page + 1),
                "searchType": "image",
                "safe": "active",
                "gl":  "in",
                "hl":  "en",
            }
            async with session.get(
                "https://www.googleapis.com/customsearch/v1", params=params
            ) as resp:
                if resp.status != 200:
                    body = await resp.text()
                    raise RuntimeError(
                        f"Google Custom Search API returned HTTP {resp.status}. "
                        "Check GOOGLE_API_KEY and GOOGLE_CX in backend/.env\n"
                        f"Response: {body[:200]}"
                    )
                data = await resp.json(content_type=None)

            for i, item in enumerate(data.get("items", [])):
                page_url  = item.get("image", {}).get("contextLink") or item.get("link", "")
                image_url = item.get("link", "")
                title     = item.get("title", "").strip()
                if not (page_url and image_url and title) or page_url in seen:
                    continue
                if not _domain_ok(page_url, settings.SEARCH_DOMAINS):
                    continue
                seen.add(page_url)
                candidates.append(CandidateProduct(
                    title=title, url=page_url, image_url=image_url,
                    source=_extract_source(page_url),
                    position=len(candidates), snippet=item.get("snippet"),
                ))

                if len(candidates) >= target_count:
                    return candidates[:target_count]

    return candidates[:target_count]


# ─────────────────────────────────────────────────────────────────────────────
# Provider 3: SerpAPI
# ─────────────────────────────────────────────────────────────────────────────

def _serpapi_sync(query: str, num: int, engine: str = "google") -> Dict[str, Any]:
    from serpapi import GoogleSearch

    params = {
        "engine": engine,
        "q": query,
        "api_key": settings.SERP_API_KEY,
        "num": min(num, settings.MAX_CANDIDATES),
        "gl": "in",
        "hl": "en",
        "safe": "active",
    }
    # google_images supports image-specific pagination via ijn
    if engine == "google_images":
        params["ijn"] = "0"

    search = GoogleSearch(params)
    return search.get_dict()


async def _search_serpapi(query: str, num: int) -> List[CandidateProduct]:
    target_count = min(num, settings.MAX_CANDIDATES)

    if not settings.SERP_API_KEY or settings.SERP_API_KEY.strip() == "":
        raise RuntimeError(
            "SERP_API_KEY not set in backend/.env\n"
            "Get your API key from https://serpapi.com/ and add it to backend/.env\n"
            "Example: SERP_API_KEY=your_serpapi_key_here"
        )

    loop = asyncio.get_event_loop()
    data = await loop.run_in_executor(_executor, _serpapi_sync, query, num, "google")

    if data.get("error"):
        raise RuntimeError(f"SerpAPI error: {data.get('error')}")

    candidates: List[CandidateProduct] = []
    seen: set = set()
    for item in data.get("shopping_results", []) + data.get("organic_results", []):
        img   = item.get("thumbnail") or item.get("image") or item.get("original", "")
        link  = item.get("link", "")
        title = item.get("title", "")
        if not (link and title) or link in seen:
            continue
        if not _domain_ok(link, settings.SEARCH_DOMAINS):
            continue

        # Organic Google results often have no thumbnail. Keep link/title and try
        # to enrich image URL from a follow-up google_images query.
        if not img:
            continue

        seen.add(link)
        candidates.append(CandidateProduct(
            title=title, url=link, image_url=img,
            source=_extract_source(link),
            position=len(candidates),
            price=_extract_price(item) or '0',
            snippet=item.get("snippet"),
        ))

        if len(candidates) >= target_count:
            break

    # If regular Google SERP had sparse image fields, augment with google_images.
    if len(candidates) < target_count:
        img_data = await loop.run_in_executor(_executor, _serpapi_sync, query, num * 3, "google_images")
        if img_data.get("error"):
            logger.warning(f"SerpAPI google_images error: {img_data.get('error')}")
        else:
            for item in img_data.get("images_results", []):
                link = item.get("link", "")
                if not link or link in seen:
                    continue
                if not _domain_ok(link, settings.SEARCH_DOMAINS):
                    continue

                img = item.get("original") or item.get("thumbnail") or item.get("image", "")
                title = item.get("title", "")
                if not (img and title):
                    continue

                seen.add(link)
                candidates.append(CandidateProduct(
                    title=title,
                    url=link,
                    image_url=img,
                    source=_extract_source(link),
                    position=len(candidates),
                    price=_extract_price(item) or '0',
                    snippet=item.get("snippet"),
                    extra={"engine": "google_images"},
                ))

                if len(candidates) >= target_count:
                    break

    logger.info(
        "SerpAPI candidates: %s (google shopping+organic + google_images fallback)",
        len(candidates),
    )
    return candidates[:target_count]


# ─────────────────────────────────────────────────────────────────────────────
# Public facade
# ─────────────────────────────────────────────────────────────────────────────

class WebSearchService:
    """
        Provider priority (set SEARCH_PROVIDER in .env):
            "serpapi"    — SerpAPI (Google-backed results)  ← RECOMMENDED
            "google"     — Google Custom Search API
            "duckduckgo" — backup only
    """

    async def search(
        self,
        query: str,
        num_results: int = None,
    ) -> List[CandidateProduct]:
        num      = num_results or settings.SEARCH_NUM_RESULTS
        provider = settings.SEARCH_PROVIDER.lower().strip()

        # Accept common typo/alias so env values like "serapi" still work.
        if provider == "serapi":
            provider = "serpapi"

        async def _try(name: str) -> List[CandidateProduct]:
            """Try a provider and return [] on expected config errors."""
            try:
                if name == "serpapi":
                    return await _search_serpapi(query, num)
                if name == "google":
                    return await _search_google(query, num)
                if name == "duckduckgo":
                    return await _search_duckduckgo(query, num)
                logger.warning(f"Unknown provider '{name}'")
                return []
            except RuntimeError as e:
                logger.warning(f"Provider '{name}' unavailable: {e}")
                return []

        try:
            if provider == "serpapi":
                results = await _try("serpapi")
                if not results:
                    logger.warning("SerpAPI returned 0 results, trying Google CSE")
                    results = await _try("google")
            elif provider == "google":
                results = await _try("google")
                if not results:
                    logger.warning("Google CSE returned 0 results, trying SerpAPI")
                    results = await _try("serpapi")
            elif provider == "duckduckgo":
                results = await _try("duckduckgo")
            else:
                logger.warning(f"Unknown SEARCH_PROVIDER '{provider}', using SerpAPI")
                results = await _try("serpapi")

            # Final safety fallback
            if not results:
                logger.warning("Primary providers returned 0 results — falling back to DuckDuckGo")
                results = await _try("duckduckgo")

            return results

        except Exception as e:
            logger.error(f"Search error ({provider}): {e}", exc_info=True)
            raise RuntimeError(f"Web search failed: {e}")


# Module-level singleton
web_search_service = WebSearchService()
