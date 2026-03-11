"""
Query Generator Service
Converts multimodal user inputs into structured web-search queries
restricted to fashion e-commerce domains.
"""
import re
import logging
from typing import Optional, List, Tuple

from app.config.settings import settings

logger = logging.getLogger(__name__)

# ── Fashion vocabulary ─────────────────────────────────────────────────────

GARMENT_TYPES: List[str] = [
    "t-shirt", "tshirt", "shirt", "blouse", "top", "tunic", "kurti", "kurta",
    "hoodie", "sweatshirt", "polo", "dress", "gown", "frock", "midi", "maxi",
    "jacket", "blazer", "coat", "windbreaker", "cardigan", "sweater",
    "jeans", "denim", "trousers", "pants", "shorts", "skirt", "leggings",
    "palazzos", "saree", "sari", "anarkali", "lehenga", "salwar", "churidar",
    "shoes", "boots", "sneakers", "heels", "sandals", "loafers", "flats",
    "bag", "handbag", "purse", "watch", "scarf", "belt", "cap", "hat",
    "sunglasses", "ethnic wear",
]

COLORS: List[str] = [
    "red", "blue", "green", "black", "white", "yellow", "pink", "purple",
    "orange", "brown", "grey", "gray", "navy", "beige", "maroon", "olive",
    "teal", "cyan", "coral", "lavender", "cream", "gold", "silver", "khaki",
    "indigo", "mint", "peach", "burgundy", "mustard",
]

PATTERNS: List[str] = [
    "floral", "striped", "printed", "solid", "plain", "graphic", "checkered",
    "plaid", "polka", "embroidered", "abstract", "animal print", "camouflage",
    "geometric", "tie-dye",
]

GENDERS: List[str] = ["men", "women", "unisex", "boys", "girls", "kids"]

OCCASIONS: List[str] = [
    "casual", "formal", "party", "ethnic", "wedding", "sports", "office",
    "beach", "festive", "traditional",
]

# Common English stop words to strip from raw queries
STOP_WORDS = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "need", "dare", "ought",
    "used", "to", "of", "in", "for", "on", "with", "at", "by", "from",
    "into", "through", "and", "or", "but", "if", "because", "as", "until",
    "while", "that", "this", "these", "those", "i", "me", "my", "we", "our",
    "you", "your", "it", "its", "they", "them", "their", "what", "which",
    "who", "whom", "how", "am", "very", "just", "also", "so", "then",
    "than", "too", "up", "out", "about", "get", "looking", "want", "need",
    "buy", "show", "find", "search", "standing", "sitting", "walking",
    "background", "view", "front", "back", "side", "close-up", "portrait",
    "wearing", "holding", "posing", "photo", "image", "picture", "outdoor",
    "indoor", "wall", "floor", "isolated", "studio", "shot",
}


class QueryGenerator:
    """
    Generates e-commerce web search queries from text and optional
    image-derived keywords.

    Pipeline:
    1. Tokenise + clean the raw text input.
    2. Extract fashion-relevant terms (colour, pattern, garment, gender, occasion).
    3. Assemble a short, focused search phrase.
    4. Append site-restriction suffix for Indian e-commerce domains.
    """

    def __init__(self, domains: Optional[List[str]] = None):
        self.domains = domains or settings.SEARCH_DOMAINS

    # ──────────────────────────────────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────────────────────────────────

    def generate(
        self,
        text: Optional[str] = None,
        image_caption: Optional[str] = None,
    ) -> Tuple[str, str]:
        """
        Generate a short search phrase and the full site-restricted query.

        Args:
            text: Raw user text query (e.g. "blue casual shirt for men").
            image_caption: Optional caption derived from an image (e.g. BLIP output).

        Returns:
            (search_phrase, full_query) where:
                search_phrase  — clean keyword phrase  ("blue casual shirt men")
                full_query     — phrase + site restriction
        """
        combined = self._merge_inputs(text, image_caption)
        if not combined:
            logger.warning("QueryGenerator received empty input; using generic query")
            combined = "fashion clothing"

        tokens = self._tokenise(combined)
        keywords = self._extract_keywords(tokens)

        # Fallback: if extraction found nothing, use raw cleaned tokens
        if not keywords:
            keywords = [t for t in tokens if t not in STOP_WORDS][:6]

        search_phrase = " ".join(keywords[:8])          # cap at 8 terms
        domain_suffix = self._build_domain_suffix()
        full_query = f"{search_phrase} {domain_suffix}"

        logger.info(f"Generated query | phrase='{search_phrase}'")
        logger.debug(f"Full query  : {full_query}")
        return search_phrase, full_query

    # ──────────────────────────────────────────────────────────────────────────
    # Private helpers
    # ──────────────────────────────────────────────────────────────────────────

    def _merge_inputs(self, text: Optional[str], caption: Optional[str]) -> str:
        parts = []
        if text:
            parts.append(text.strip())
        if caption:
            parts.append(caption.strip())
        return " ".join(parts)

    def _tokenise(self, raw: str) -> List[str]:
        """Lowercase, remove punctuation, split into tokens."""
        cleaned = raw.lower()
        cleaned = re.sub(r"[^a-z0-9\s\-]", " ", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned.split()

    def _extract_keywords(self, tokens: List[str]) -> List[str]:
        """
        Extract fashion-relevant terms in priority order:
        [colour] [pattern] [garment] [gender] [occasion] [fashion]
        """
        text = " ".join(tokens)
        keywords: List[str] = []
        seen: set = set()

        def _add(term: str):
            if term not in seen:
                keywords.append(term)
                seen.add(term)

        # Multi-word terms first (longest match wins)
        for vocab_list in [GARMENT_TYPES, PATTERNS, OCCASIONS]:
            multi = [t for t in vocab_list if " " in t]
            for term in sorted(multi, key=len, reverse=True):
                if term in text:
                    _add(term)

        # Single-word colour
        for color in COLORS:
            if color in tokens:
                _add(color)
                break  # one colour is enough

        # Single-word pattern
        for pat in PATTERNS:
            if " " not in pat and pat in tokens:
                _add(pat)
                break

        # Garment type (single-word)
        for garment in GARMENT_TYPES:
            if " " not in garment and garment in tokens:
                _add(garment)
                break

        # Gender
        for gender in GENDERS:
            if gender in tokens:
                _add(gender)
                break

        # Occasion
        for occasion in OCCASIONS:
            if " " not in occasion and occasion in tokens:
                _add(occasion)
                break

        # Always append "fashion" as a trailing anchor
        _add("fashion")

        return keywords

    def _build_domain_suffix(self) -> str:
        """
        Build the domain-restriction part of the query.

        Always use strict site: restriction to keep results on e-commerce domains.
        """
        # strict site: syntax for Google CSE / SerpAPI
        parts = [f"site:{d}" for d in self.domains]
        return " OR ".join(parts)

    # Keep old method name as alias for backward compat
    def _build_site_restriction(self) -> str:
        return self._build_domain_suffix()


# Module-level singleton
query_generator = QueryGenerator()
