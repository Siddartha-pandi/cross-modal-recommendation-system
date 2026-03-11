"""
Query Understanding Module
Advanced semantic parsing and attribute extraction for fashion queries.

Implements:
- Attribute extraction (color, category, gender, style, pattern)
- Query expansion
- Semantic intent recognition
- Fashion-specific entity recognition
"""
import re
import logging
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
from collections import defaultdict

from app.core.fashion_taxonomy import (
    ALL_CATEGORY_TERMS,
    COMMON_PATTERNS,
    SLEEVE_TYPES,
    COLLAR_TYPES,
    NECKLINES,
    LENGTH_TYPES,
    SOLE_TYPES,
    CLOSURE_TYPES,
    USE_TYPES,
    SEASON_KEYWORDS,
)

logger = logging.getLogger(__name__)


@dataclass
class QueryAttributes:
    """Extracted attributes from user query."""
    colors: List[str] = field(default_factory=list)
    categories: List[str] = field(default_factory=list)
    patterns: List[str] = field(default_factory=list)
    materials: List[str] = field(default_factory=list)
    genders: List[str] = field(default_factory=list)
    occasions: List[str] = field(default_factory=list)
    styles: List[str] = field(default_factory=list)
    brands: List[str] = field(default_factory=list)
    sizes: List[str] = field(default_factory=list)
    sleeve_types: List[str] = field(default_factory=list)
    collar_types: List[str] = field(default_factory=list)
    neckline_types: List[str] = field(default_factory=list)
    length_types: List[str] = field(default_factory=list)
    sole_types: List[str] = field(default_factory=list)
    closure_types: List[str] = field(default_factory=list)
    use_types: List[str] = field(default_factory=list)
    seasons: List[str] = field(default_factory=list)
    price_range: Optional[Tuple[float, float]] = None
    raw_tokens: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for logging/JSON."""
        return {
            "colors": self.colors,
            "categories": self.categories,
            "patterns": self.patterns,
            "materials": self.materials,
            "genders": self.genders,
            "occasions": self.occasions,
            "styles": self.styles,
            "brands": self.brands,
            "sizes": self.sizes,
            "sleeve_types": self.sleeve_types,
            "collar_types": self.collar_types,
            "neckline_types": self.neckline_types,
            "length_types": self.length_types,
            "sole_types": self.sole_types,
            "closure_types": self.closure_types,
            "use_types": self.use_types,
            "seasons": self.seasons,
            "price_range": self.price_range,
        }
    
    def get_all_attributes(self) -> List[str]:
        """Get all extracted attributes as flat list."""
        attrs = []
        attrs.extend(self.colors)
        attrs.extend(self.categories)
        attrs.extend(self.patterns)
        attrs.extend(self.materials)
        attrs.extend(self.genders)
        attrs.extend(self.occasions)
        attrs.extend(self.styles)
        attrs.extend(self.seasons)
        return attrs


# ─── Fashion Vocabulary Database ────────────────────────────────────────────

COLORS = {
    "red", "blue", "green", "black", "white", "yellow", "pink", "purple",
    "orange", "brown", "grey", "gray", "navy", "beige", "maroon", "olive",
    "teal", "cyan", "coral", "lavender", "cream", "gold", "silver", "khaki",
    "indigo", "mint", "peach", "burgundy", "mustard", "charcoal", "rust",
    "sage", "wine", "chocolate", "tan", "ivory", "emerald", "sapphire",
}

CATEGORIES = {
    # Upper body
    "t-shirt", "tshirt", "shirt", "blouse", "top", "tunic", "kurti", "kurta",
    "hoodie", "sweatshirt", "polo", "tank top", "crop top", "camisole",
    
    # Dresses
    "dress", "gown", "frock", "midi", "maxi", "sundress", "bodycon",
    
    # Outerwear
    "jacket", "blazer", "coat", "windbreaker", "cardigan", "sweater",
    "pullover", "shrug", "vest", "parka", "trench coat",
    
    # Lower body
    "jeans", "denim", "trousers", "pants", "shorts", "skirt", "leggings",
    "palazzos", "capris", "culottes", "joggers", "chinos",
    
    # Traditional
    "saree", "sari", "anarkali", "lehenga", "salwar", "churidar",
    "dupatta", "sherwani", "kurta pajama",
    
    # Footwear
    "shoes", "boots", "sneakers", "heels", "sandals", "loafers", "flats",
    "pumps", "wedges", "slippers", "mules", "oxfords", "brogues",
    
    # Accessories
    "bag", "handbag", "purse", "wallet", "watch", "scarf", "belt", "cap",
    "hat", "sunglasses", "jewelry", "necklace", "bracelet", "earrings",
    "ring", "backpack", "tote", "clutch", "satchel",
    
    # Innerwear
    "bra", "lingerie", "underwear", "boxers", "briefs", "socks",
}

CATEGORIES.update(set(ALL_CATEGORY_TERMS))

PATTERNS = {
    "floral", "striped", "printed", "solid", "plain", "graphic", "checkered",
    "plaid", "polka dot", "embroidered", "abstract", "animal print",
    "camouflage", "geometric", "tie-dye", "paisley", "chevron", "houndstooth",
    "argyle", "herringbone", "leopard", "zebra", "snakeskin",
}

PATTERNS.update(set(COMMON_PATTERNS))

MATERIALS = {
    "cotton", "silk", "denim", "leather", "wool", "linen", "polyester",
    "velvet", "satin", "chiffon", "georgette", "rayon", "nylon", "spandex",
    "jersey", "fleece", "corduroy", "suede", "cashmere", "khadi",
}

GENDERS = {
    "men", "women", "unisex", "boys", "girls", "kids", "children",
    "male", "female", "mens", "womens",
}

OCCASIONS = {
    "casual", "formal", "party", "ethnic", "wedding", "sports", "office",
    "beach", "festive", "traditional", "workout", "gym", "running",
    "everyday", "loungewear", "nightwear", "sleepwear", "activewear",
}

STYLES = {
    "slim fit", "regular fit", "loose fit", "oversized", "fitted",
    "relaxed", "skinny", "straight", "bootcut", "flared", "tapered",
    "vintage", "retro", "modern", "classic", "bohemian", "boho",
    "minimalist", "edgy", "preppy", "sporty", "chic", "elegant",
    "trendy", "contemporary", "traditional",
}

BRANDS = {
    "nike", "adidas", "puma", "zara", "h&m", "levis", "gap", "uniqlo",
    "mango", "forever 21", "tommy hilfiger", "calvin klein", "gucci",
    "prada", "versace", "armani", "burberry", "chanel", "dior",
    "fabindia", "biba", "w", "westside", "and", "only", "vero moda",
}

SIZES = {
    "xs", "s", "m", "l", "xl", "xxl", "xxxl",
    "extra small", "small", "medium", "large", "extra large",
    "28", "30", "32", "34", "36", "38", "40", "42", "44",
    "6", "8", "10", "12", "14", "16", "18",
}

SEASONS = set(SEASON_KEYWORDS)

# Synonyms for query expansion
SYNONYMS = {
    "tshirt": ["t-shirt", "tee", "shirt"],
    "jeans": ["denim pants", "denim jeans"],
    "sneakers": ["sports shoes", "trainers", "running shoes"],
    "jacket": ["coat", "blazer", "outerwear"],
    "dress": ["frock", "gown"],
    "casual": ["everyday", "informal"],
    "formal": ["office", "professional", "business"],
}


class QueryUnderstandingService:
    """
    Advanced query understanding with attribute extraction and expansion.
    
    Pipeline:
    1. Tokenization and preprocessing
    2. Multi-pass attribute extraction
    3. Entity recognition
    4. Query expansion
    5. Intent classification
    """
    
    def __init__(self):
        self.colors = COLORS
        self.categories = CATEGORIES
        self.patterns = PATTERNS
        self.materials = MATERIALS
        self.genders = GENDERS
        self.occasions = OCCASIONS
        self.styles = STYLES
        self.brands = BRANDS
        self.sizes = SIZES
        self.sleeve_types = set(SLEEVE_TYPES)
        self.collar_types = set(COLLAR_TYPES)
        self.neckline_types = set(NECKLINES)
        self.length_types = set(LENGTH_TYPES)
        self.sole_types = set(SOLE_TYPES)
        self.closure_types = set(CLOSURE_TYPES)
        self.use_types = set(USE_TYPES)
        self.seasons = SEASONS
        self.synonyms = SYNONYMS
        
        # Compile multi-word patterns for better matching
        self._compile_patterns()
        logger.info("QueryUnderstandingService initialized")
    
    def _compile_patterns(self):
        """Pre-compile regex patterns for multi-word matching."""
        self.multi_word_styles = sorted(
            [s for s in self.styles if " " in s],
            key=lambda x: len(x),
            reverse=True
        )
        self.multi_word_categories = sorted(
            [c for c in self.categories if " " in c],
            key=lambda x: len(x),
            reverse=True
        )
    
    def understand(self, text: str) -> QueryAttributes:
        """
        Main entry point: extract all attributes from query text.
        
        Args:
            text: Raw user query (e.g., "blue casual shirt for men")
        
        Returns:
            QueryAttributes object with all extracted features
        """
        if not text or not text.strip():
            return QueryAttributes()
        
        # Normalize and tokenize
        text_lower = text.lower().strip()
        
        # Extract attributes
        attributes = QueryAttributes()
        attributes.raw_tokens = self._tokenize(text_lower)
        
        # Multi-pass extraction (order matters for multi-word phrases)
        attributes.colors = self._extract_colors(text_lower)
        attributes.patterns = self._extract_patterns(text_lower)
        attributes.materials = self._extract_materials(text_lower)
        attributes.genders = self._extract_genders(text_lower)
        attributes.occasions = self._extract_occasions(text_lower)
        attributes.styles = self._extract_styles(text_lower)
        attributes.brands = self._extract_brands(text_lower)
        attributes.sizes = self._extract_sizes(text_lower)
        attributes.sleeve_types = self._extract_sleeve_types(text_lower)
        attributes.collar_types = self._extract_collar_types(text_lower)
        attributes.neckline_types = self._extract_neckline_types(text_lower)
        attributes.length_types = self._extract_length_types(text_lower)
        attributes.sole_types = self._extract_sole_types(text_lower)
        attributes.closure_types = self._extract_closure_types(text_lower)
        attributes.use_types = self._extract_use_types(text_lower)
        attributes.seasons = self._extract_seasons(text_lower)
        attributes.categories = self._extract_categories(text_lower)
        attributes.price_range = self._extract_price_range(text_lower)
        
        logger.debug(f"Extracted attributes: {attributes.to_dict()}")
        return attributes
    
    def expand_query(self, text: str, attributes: Optional[QueryAttributes] = None) -> str:
        """
        Expand query with synonyms and related terms.
        
        Args:
            text: Original query
            attributes: Pre-extracted attributes (optional, will extract if None)
        
        Returns:
            Expanded query string
        """
        if attributes is None:
            attributes = self.understand(text)
        
        expanded_terms = set([text])
        
        # Add synonyms for each token
        for token in attributes.raw_tokens:
            if token in self.synonyms:
                expanded_terms.update(self.synonyms[token])
        
        # Add attribute-based expansions
        if attributes.categories:
            expanded_terms.update(attributes.categories)
        
        # Combine into expanded query
        expanded = " ".join(sorted(expanded_terms, key=len, reverse=True))
        logger.debug(f"Expanded query: '{text}' → '{expanded}'")
        return expanded
    
    def get_structured_query(self, text: str) -> Dict[str, Any]:
        """
        Generate structured query representation.
        
        Returns:
        {
            "original": str,
            "attributes": QueryAttributes,
            "expanded": str,
            "intent": str,
            "confidence": float
        }
        """
        attributes = self.understand(text)
        expanded = self.expand_query(text, attributes)
        intent = self._classify_intent(attributes)
        confidence = self._compute_confidence(attributes)
        
        return {
            "original": text,
            "attributes": attributes.to_dict(),
            "expanded": expanded,
            "intent": intent,
            "confidence": confidence,
            "primary_category": attributes.categories[0] if attributes.categories else None,
        }
    
    # ─── Private Extraction Methods ─────────────────────────────────────────
    
    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization preserving important words."""
        # Remove special characters but keep hyphens and spaces
        text = re.sub(r'[^\w\s-]', ' ', text)
        tokens = text.split()
        return [t for t in tokens if len(t) > 1]
    
    def _extract_colors(self, text: str) -> List[str]:
        """Extract color attributes."""
        found = []
        for color in self.colors:
            if re.search(r'\b' + re.escape(color) + r'\b', text):
                found.append(color)
        return found
    
    def _extract_patterns(self, text: str) -> List[str]:
        """Extract pattern attributes."""
        found = []
        for pattern in self.patterns:
            if re.search(r'\b' + re.escape(pattern) + r'\b', text):
                found.append(pattern)
        return found
    
    def _extract_materials(self, text: str) -> List[str]:
        """Extract material attributes."""
        found = []
        for material in self.materials:
            if re.search(r'\b' + re.escape(material) + r'\b', text):
                found.append(material)
        return found
    
    def _extract_genders(self, text: str) -> List[str]:
        """Extract gender attributes."""
        found = []
        for gender in self.genders:
            if re.search(r'\b' + re.escape(gender) + r'\b', text):
                # Normalize to canonical form
                if gender in ["mens", "male"]:
                    if "men" not in found:
                        found.append("men")
                elif gender in ["womens", "female"]:
                    if "women" not in found:
                        found.append("women")
                else:
                    found.append(gender)
        return found
    
    def _extract_occasions(self, text: str) -> List[str]:
        """Extract occasion attributes."""
        found = []
        for occasion in self.occasions:
            if re.search(r'\b' + re.escape(occasion) + r'\b', text):
                found.append(occasion)
        return found
    
    def _extract_styles(self, text: str) -> List[str]:
        """Extract style attributes (multi-word aware)."""
        found = []
        # First check multi-word styles
        for style in self.multi_word_styles:
            if style in text:
                found.append(style)
        # Then single-word styles
        for style in self.styles:
            if " " not in style and re.search(r'\b' + re.escape(style) + r'\b', text):
                if style not in found:
                    found.append(style)
        return found
    
    def _extract_brands(self, text: str) -> List[str]:
        """Extract brand names."""
        found = []
        for brand in self.brands:
            if re.search(r'\b' + re.escape(brand) + r'\b', text):
                found.append(brand)
        return found
    
    def _extract_sizes(self, text: str) -> List[str]:
        """Extract size information."""
        found = []
        for size in self.sizes:
            if re.search(r'\b' + re.escape(size) + r'\b', text):
                found.append(size)
        return found
    
    def _extract_categories(self, text: str) -> List[str]:
        """Extract category attributes (multi-word aware)."""
        found = []
        # First check multi-word categories
        for category in self.multi_word_categories:
            if category in text:
                found.append(category)
        # Then single-word categories
        for category in self.categories:
            if " " not in category and re.search(r'\b' + re.escape(category) + r'\b', text):
                if category not in found:
                    found.append(category)
        return found

    def _extract_sleeve_types(self, text: str) -> List[str]:
        found = []
        for sleeve in self.sleeve_types:
            if sleeve in text:
                found.append(sleeve)
        return found

    def _extract_collar_types(self, text: str) -> List[str]:
        found = []
        for collar in self.collar_types:
            if collar in text:
                found.append(collar)
        return found

    def _extract_neckline_types(self, text: str) -> List[str]:
        found = []
        for neckline in self.neckline_types:
            if neckline in text:
                found.append(neckline)
        return found

    def _extract_length_types(self, text: str) -> List[str]:
        found = []
        for length in self.length_types:
            if re.search(r'\b' + re.escape(length) + r'\b', text):
                found.append(length)
        return found

    def _extract_sole_types(self, text: str) -> List[str]:
        found = []
        for sole in self.sole_types:
            if re.search(r'\b' + re.escape(sole) + r'\b', text):
                found.append(sole)
        return found

    def _extract_closure_types(self, text: str) -> List[str]:
        found = []
        for closure in self.closure_types:
            if closure in text:
                found.append(closure)
        return found

    def _extract_use_types(self, text: str) -> List[str]:
        found = []
        for use_type in self.use_types:
            if re.search(r'\b' + re.escape(use_type) + r'\b', text):
                found.append(use_type)
        return found

    def _extract_seasons(self, text: str) -> List[str]:
        found = []
        for season in self.seasons:
            if re.search(r'\b' + re.escape(season) + r'\b', text):
                found.append(season)
        return found
    
    def _extract_price_range(self, text: str) -> Optional[Tuple[float, float]]:
        """Extract price range if mentioned."""
        # Pattern: "under 2000", "below 1000", "between 1000 and 2000"
        under_match = re.search(r'under\s+(\d+)', text)
        if under_match:
            return (0, float(under_match.group(1)))
        
        below_match = re.search(r'below\s+(\d+)', text)
        if below_match:
            return (0, float(below_match.group(1)))
        
        between_match = re.search(r'between\s+(\d+)\s+and\s+(\d+)', text)
        if between_match:
            return (float(between_match.group(1)), float(between_match.group(2)))
        
        return None
    
    def _classify_intent(self, attributes: QueryAttributes) -> str:
        """Classify user intent based on attributes."""
        if attributes.categories:
            if attributes.colors or attributes.patterns:
                return "specific_search"  # Looking for specific styled item
            return "category_browse"      # Browsing category
        
        if attributes.colors or attributes.patterns:
            return "style_search"          # Looking for style/color
        
        if attributes.occasions:
            return "occasion_search"       # Looking for occasion-based items
        
        return "general_search"
    
    def _compute_confidence(self, attributes: QueryAttributes) -> float:
        """Compute confidence score based on extracted attributes."""
        score = 0.0
        
        # More attributes = higher confidence
        if attributes.categories:
            score += 0.3
        if attributes.colors:
            score += 0.2
        if attributes.genders:
            score += 0.15
        if attributes.patterns:
            score += 0.15
        if attributes.occasions:
            score += 0.1
        if attributes.materials:
            score += 0.1
        if attributes.seasons:
            score += 0.1
        
        return min(score, 1.0)


# ─── Singleton Instance ──────────────────────────────────────────────────────

query_understanding_service = QueryUnderstandingService()
