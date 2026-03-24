"""
Price Scraper Utility
Asynchronously scrapes product prices from Indian e-commerce websites.

Supported sites (site-specific CSS selectors):
  • Myntra   — .pdp-price strong | .pdp-discount-container strong
  • Amazon   — .a-price-whole | span[data-a-color=price] .a-offscreen
  • Flipkart — ._30jeq3 | ._1_WHN1
  • AJIO     — .prod-sp | .product-price

Falls back to a regex scan of all visible text for ₹ / Rs. / INR patterns
when the primary selector does not match.
"""
import asyncio
import logging
import re
from typing import Optional

import aiohttp

logger = logging.getLogger(__name__)

# ── Browser-like headers to reduce bot-detection blocks ─────────────────────
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-IN,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
}

# ── Site-specific CSS selectors (ordered by specificity / reliability) ────────
_SITE_SELECTORS: dict[str, list[str]] = {
    "myntra": [
        ".pdp-price strong",
        ".pdp-discount-container strong",
        "p.pdp-price",
        ".pdp-mrp strong",
    ],
    "amazon": [
        ".a-price > .a-offscreen",
        ".a-price-whole",
        "#priceblock_ourprice",
        "#priceblock_dealprice",
        "span[data-a-color='price'] .a-offscreen",
        ".apexPriceToPay .a-offscreen",
    ],
    "flipkart": [
        "._30jeq3",
        "._1_WHN1",
        ".CEmiEU > div:first-child",
        "div[class*='_30jeq3']",
    ],
    "ajio": [
        ".prod-sp",
        ".product-price",
        "span.prod-discount",
        ".prod-price-wrap .prod-sp",
    ],
}

# ── INR regex for full-page fallback ─────────────────────────────────────────
_PRICE_RE = re.compile(
    r"(?:₹|Rs\.?\s*|INR\s*)\s*([\d,]+(?:\.\d{1,2})?)",
    re.IGNORECASE,
)


def _detect_site(url: str) -> Optional[str]:
    lower = url.lower()
    for site in _SITE_SELECTORS:
        if site in lower:
            return site
    return None


def _parse_raw(raw: str) -> Optional[str]:
    """Clean a raw price string and return the numeric part, or None."""
    raw = raw.strip()
    if not raw:
        return None
    # strip currency symbols / labels
    cleaned = re.sub(r"[₹Rs.\s,INR]", "", raw, flags=re.IGNORECASE).strip()
    # remove any remaining non-numeric except '.'
    cleaned = re.sub(r"[^\d.]", "", cleaned)
    try:
        val = float(cleaned)
        if val > 0:
            return str(int(val))   # return as integer string, e.g. "1299"
    except ValueError:
        pass
    return None


async def scrape_price(url: str, timeout: int = 8) -> Optional[str]:
    """
    Fetch the product page at *url* and try to extract the INR price.

    Returns:
        A numeric string like "1299" on success, or None on failure.
    """
    try:
        async with aiohttp.ClientSession(
            headers=_HEADERS,
            connector=aiohttp.TCPConnector(ssl=False),
            timeout=aiohttp.ClientTimeout(total=timeout),
        ) as session:
            async with session.get(url, allow_redirects=True) as resp:
                if resp.status != 200:
                    logger.debug(f"[PriceScraper] HTTP {resp.status} for {url[:70]}")
                    return None
                html = await resp.text(errors="replace")
    except asyncio.TimeoutError:
        logger.debug(f"[PriceScraper] Timeout: {url[:70]}")
        return None
    except Exception as exc:
        logger.debug(f"[PriceScraper] Fetch error for {url[:70]}: {exc}")
        return None

    # ── Try BeautifulSoup with site-specific selectors ────────────────────
    try:
        from bs4 import BeautifulSoup  # optional fast-path
        soup = BeautifulSoup(html, "html.parser")

        site = _detect_site(url)
        if site:
            for selector in _SITE_SELECTORS[site]:
                el = soup.select_one(selector)
                if el:
                    price = _parse_raw(el.get_text())
                    if price:
                        logger.debug(
                            f"[PriceScraper] ✓ {site} selector '{selector}': ₹{price}"
                        )
                        return price

        # ── BeautifulSoup regex fallback — scan all text nodes ────────────
        text = soup.get_text(separator=" ", strip=True)
        match = _PRICE_RE.search(text)
        if match:
            price = _parse_raw(match.group(1))
            if price:
                logger.debug(f"[PriceScraper] ✓ regex fallback: ₹{price}")
                return price

    except ImportError:
        # BeautifulSoup not installed — fall through to pure-regex path
        pass
    except Exception as exc:
        logger.debug(f"[PriceScraper] BS4 parse error: {exc}")

    # ── Pure regex fallback on raw HTML ──────────────────────────────────
    match = _PRICE_RE.search(html)
    if match:
        price = _parse_raw(match.group(1))
        if price:
            logger.debug(f"[PriceScraper] ✓ raw-html regex: ₹{price}")
            return price

    logger.debug(f"[PriceScraper] ✗ no price found for {url[:70]}")
    return None


async def scrape_prices_bulk(
    url_map: dict[str, str],   # { product_url: current_price_or_empty }
    timeout: int = 8,
    max_concurrent: int = 6,
) -> dict[str, Optional[str]]:
    """
    Batch-scrape prices for multiple product URLs concurrently.
    Only scrapes URLs whose current price is falsy/zero.

    Args:
        url_map: mapping of product URL → existing price string
        timeout: per-request timeout in seconds
        max_concurrent: max simultaneous HTTP requests

    Returns:
        mapping of product URL → scraped price (or None)
    """
    to_scrape = [url for url, price in url_map.items()
                 if not price or price in ('0', '0.0')]

    if not to_scrape:
        return {}

    semaphore = asyncio.Semaphore(max_concurrent)

    async def _bounded(url: str):
        async with semaphore:
            return url, await scrape_price(url, timeout)

    tasks = [_bounded(url) for url in to_scrape]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    out: dict[str, Optional[str]] = {}
    for res in results:
        if isinstance(res, Exception):
            logger.debug(f"[PriceScraper] task error: {res}")
            continue
        url, price = res
        out[url] = price

    scraped = sum(1 for p in out.values() if p)
    logger.info(
        f"[PriceScraper] bulk: scraped {scraped}/{len(to_scrape)} prices"
    )
    return out
