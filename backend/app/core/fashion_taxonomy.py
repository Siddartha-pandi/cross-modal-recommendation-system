"""Fashion taxonomy and seasonal preference definitions."""

SHIRT_SUBCATEGORIES = [
    "formal shirt",
    "casual shirt",
    "printed shirt",
    "checked shirt",
    "denim shirt",
    "linen shirt",
    "oversized shirt",
    "crop shirt",
    "blouse shirt",
]

SHOE_SUBCATEGORIES = [
    "sneakers",
    "running shoes",
    "formal shoes",
    "loafers",
    "boots",
    "sandals",
    "high heels",
    "flats",
    "slippers",
]

DRESS_SUBCATEGORIES = [
    "casual frock",
    "party wear dress",
    "maxi dress",
    "mini dress",
    "midi dress",
    "a-line dress",
    "bodycon dress",
    "floral dress",
    "summer dress",
]

COMMON_PATTERNS = [
    "solid",
    "plain",
    "striped",
    "checked",
    "plaid",
    "floral",
    "polka dot",
    "geometric",
    "abstract",
    "animal print",
]

SLEEVE_TYPES = ["full sleeve", "half sleeve", "sleeveless"]
COLLAR_TYPES = ["spread collar", "mandarin collar", "button-down collar"]
NECKLINES = ["round neck", "v-neck", "square neck"]
LENGTH_TYPES = ["mini", "midi", "maxi"]
SHOE_MATERIALS = ["leather", "mesh", "synthetic"]
SOLE_TYPES = ["rubber", "eva", "foam"]
CLOSURE_TYPES = ["lace-up", "slip-on", "velcro"]
USE_TYPES = ["casual", "sports", "formal"]

SEASON_KEYWORDS = ["summer", "winter", "spring", "all"]

SEASONAL_RECOMMENDATIONS = {
    "summer": {
        "categories": ["shirt", "frock", "dress", "sandals", "sneakers", "linen shirt"],
        "materials": ["cotton", "linen", "mesh"],
        "styles": ["light", "breathable", "bright colors"],
    },
    "winter": {
        "categories": ["jacket", "hoodie", "boots", "full sleeve shirt"],
        "materials": ["wool", "denim", "leather", "thick fabrics"],
        "styles": ["dark colors", "layered outfits"],
    },
    "spring": {
        "categories": ["floral dress", "pastel shirt", "light jacket"],
        "materials": ["cotton", "linen"],
        "styles": ["light", "soft colors"],
    },
}

ALL_CATEGORY_TERMS = sorted(
    set(
        ["shirt", "shoes", "shoe", "frock", "dress", "dresses"]
        + SHIRT_SUBCATEGORIES
        + SHOE_SUBCATEGORIES
        + DRESS_SUBCATEGORIES
    )
)
