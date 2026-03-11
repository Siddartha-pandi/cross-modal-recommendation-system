"""Fashion knowledge graph service backed by ontology JSON."""

import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class FashionKnowledgeGraph:
    """Extracts query attributes and filters candidates using ontology knowledge."""

    def __init__(self, ontology_path: Optional[Path] = None):
        if ontology_path is None:
            ontology_path = self._default_ontology_path()
        self.ontology_path = ontology_path
        self.ontology = self._load_ontology()
        self._build_indexes()

    def _default_ontology_path(self) -> Path:
        current = Path(__file__).resolve()
        repo_root = current
        for parent in [current] + list(current.parents):
            if (parent / "data").exists() and (parent / "backend").exists():
                repo_root = parent
                break
        return repo_root / "data" / "fashion_ontology.json"

    def _load_ontology(self) -> Dict[str, Any]:
        if not self.ontology_path.exists():
            logger.warning("Ontology file not found at %s", self.ontology_path)
            return {"categories": {}, "patterns": [], "seasonal_recommendations": {}}
        with open(self.ontology_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _build_indexes(self) -> None:
        categories = self.ontology.get("categories", {})
        self.category_terms = set(categories.keys())
        self.subcategory_terms = set()
        self.attribute_values = {
            "pattern": set(self.ontology.get("patterns", [])),
            "material": set(),
            "sleeve_type": set(),
            "collar_type": set(),
            "sole_type": set(),
            "closure": set(),
            "use": set(),
            "length": set(),
            "neckline": set(),
        }
        for category_def in categories.values():
            self.subcategory_terms.update(category_def.get("subcategories", []))
            attrs = category_def.get("attributes", {})
            for key in self.attribute_values:
                self.attribute_values[key].update(attrs.get(key, []))

        self.color_terms = {
            "red", "blue", "green", "black", "white", "yellow", "pink", "purple",
            "orange", "brown", "grey", "gray", "navy", "beige", "maroon", "olive",
        }
        self.season_terms = set(self.ontology.get("seasonal_recommendations", {}).keys())
        self.occasion_terms = {"party", "casual", "formal", "sports", "wedding"}

    def extract_attributes(self, query: str) -> Dict[str, str]:
        """Return compact KG attributes similar to the requested example."""
        q = (query or "").lower()
        result: Dict[str, str] = {}

        category = self._first_match(q, self.category_terms)
        if category:
            result["category"] = category

        subcategory = self._first_match(q, self.subcategory_terms)
        if subcategory:
            result["sub_category"] = subcategory

        color = self._first_match(q, self.color_terms)
        if color:
            result["color"] = color

        pattern = self._first_match(q, self.attribute_values["pattern"])
        if pattern:
            result["pattern"] = pattern

        material = self._first_match(q, self.attribute_values["material"])
        if material:
            result["material"] = material

        season = self._first_match(q, self.season_terms)
        if season:
            result["season"] = season

        occasion = self._first_match(q, self.occasion_terms)
        if occasion:
            result["occasion"] = occasion

        return result

    def extract_attributes_for_pipeline(self, query: str) -> Dict[str, List[str]]:
        """Return list-based attributes compatible with current pipeline."""
        raw = self.extract_attributes(query)
        mapped = {
            "categories": [raw["category"]] if raw.get("category") else [],
            "patterns": [raw["pattern"]] if raw.get("pattern") else [],
            "colors": [raw["color"]] if raw.get("color") else [],
            "materials": [raw["material"]] if raw.get("material") else [],
            "seasons": [raw["season"]] if raw.get("season") else [],
            "occasions": [raw["occasion"]] if raw.get("occasion") else [],
            "subcategories": [raw["sub_category"]] if raw.get("sub_category") else [],
        }
        return mapped

    def filter_products(self, products: List[Dict[str, Any]], attributes: Dict[str, str]) -> List[Dict[str, Any]]:
        """Strict attribute filtering before ranking, as described in your design."""
        filtered: List[Dict[str, Any]] = []
        for product in products:
            if attributes.get("category") and attributes["category"] != str(product.get("category", "")).lower():
                continue
            if attributes.get("pattern") and attributes["pattern"] != str(product.get("pattern", "")).lower():
                continue
            if attributes.get("color") and attributes["color"] != str(product.get("color", "")).lower():
                continue
            filtered.append(product)
        return filtered

    def filter_candidates(self, candidates: List[Any], attributes: Dict[str, Any]) -> List[Any]:
        """Filter CandidateProduct objects using category/pattern/color/season cues."""
        if not attributes:
            return candidates

        categories = set([c.lower() for c in attributes.get("categories", [])])
        patterns = set([p.lower() for p in attributes.get("patterns", [])])
        colors = set([c.lower() for c in attributes.get("colors", [])])
        occasions = set([o.lower() for o in attributes.get("occasions", [])])

        if not (categories or patterns or colors or occasions):
            return candidates

        filtered: List[Any] = []
        for c in candidates:
            text = f"{getattr(c, 'title', '')} {getattr(c, 'snippet', '')}".lower()
            if categories and not any(term in text for term in categories):
                continue
            if patterns and not any(term in text for term in patterns):
                continue
            if colors and not any(term in text for term in colors):
                continue
            if occasions and not any(term in text for term in occasions):
                continue
            filtered.append(c)
        return filtered

    def _first_match(self, text: str, terms: set) -> Optional[str]:
        for term in sorted(terms, key=len, reverse=True):
            if re.search(r"\\b" + re.escape(term) + r"\\b", text):
                return term
        return None


fashion_knowledge_graph = FashionKnowledgeGraph()
