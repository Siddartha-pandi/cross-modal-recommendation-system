"""Product schema aligned to knowledge-graph-ready product table."""

from pydantic import BaseModel
from typing import Optional


class ProductRecord(BaseModel):
    id: int
    category: str
    sub_category: str
    title: str
    description: str
    color: Optional[str] = None
    pattern: Optional[str] = None
    season: Optional[str] = None
    price: float
    image_url: str
