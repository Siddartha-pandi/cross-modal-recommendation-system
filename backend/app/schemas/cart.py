"""
Cart and Order database models
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import json
import os
from pathlib import Path
import uuid
import logging

logger = logging.getLogger(__name__)

# Data storage paths
DATA_DIR = Path(__file__).parent.parent.parent / "data"
CARTS_FILE = DATA_DIR / "carts.json"
ORDERS_FILE = DATA_DIR / "orders.json"


# --- Request/Response Models ---

class CartItem(BaseModel):
    """Cart item model"""
    product_id: str
    title: str
    price: float
    quantity: int = Field(default=1, ge=1)
    image_url: str


class CartResponse(BaseModel):
    """User cart response"""
    user_id: str
    items: List[CartItem]
    total_price: float
    item_count: int


class AddToCartRequest(BaseModel):
    """Request to add item to cart"""
    product_id: str
    title: str
    price: float
    quantity: int = Field(default=1, ge=1)
    image_url: str


class CheckoutRequest(BaseModel):
    """Checkout request"""
    shipping_address: str
    shipping_city: str
    shipping_zip: str


class OrderResponse(BaseModel):
    """Order response"""
    order_id: str
    user_id: str
    items: List[CartItem]
    total_price: float
    shipping_address: str
    shipping_city: str
    shipping_zip: str
    status: str  # pending, processing, shipped, delivered
    created_at: datetime


# --- Database Models ---

class CartStore:
    """In-memory cart storage with JSON persistence"""
    
    @staticmethod
    def _ensure_file():
        """Ensure carts.json exists"""
        CARTS_FILE.parent.mkdir(parents=True, exist_ok=True)
        if not CARTS_FILE.exists():
            CARTS_FILE.write_text(json.dumps({}))
    
    @staticmethod
    def _load_carts() -> dict:
        """Load all carts from file"""
        CartStore._ensure_file()
        try:
            return json.loads(CARTS_FILE.read_text())
        except:
            return {}
    
    @staticmethod
    def _save_carts(carts: dict):
        """Save carts to file"""
        CartStore._ensure_file()
        CARTS_FILE.write_text(json.dumps(carts, indent=2))
    
    @staticmethod
    def get_cart(user_id: str) -> dict:
        """Get user's cart"""
        carts = CartStore._load_carts()
        return carts.get(user_id, {"items": []})
    
    @staticmethod
    def add_item(user_id: str, item: CartItem) -> dict:
        """Add item to cart"""
        carts = CartStore._load_carts()
        
        if user_id not in carts:
            carts[user_id] = {"items": []}
        
        # Check if item already exists
        existing_item = None
        for idx, it in enumerate(carts[user_id]["items"]):
            if it["product_id"] == item.product_id:
                existing_item = idx
                break
        
        if existing_item is not None:
            # Update quantity
            carts[user_id]["items"][existing_item]["quantity"] += item.quantity
        else:
            # Add new item
            carts[user_id]["items"].append(item.model_dump())
        
        CartStore._save_carts(carts)
        return carts[user_id]
    
    @staticmethod
    def remove_item(user_id: str, product_id: str) -> dict:
        """Remove item from cart"""
        carts = CartStore._load_carts()
        
        if user_id in carts:
            carts[user_id]["items"] = [
                item for item in carts[user_id]["items"] 
                if item["product_id"] != product_id
            ]
        
        CartStore._save_carts(carts)
        return carts.get(user_id, {"items": []})
    
    @staticmethod
    def update_quantity(user_id: str, product_id: str, quantity: int) -> dict:
        """Update item quantity"""
        carts = CartStore._load_carts()
        
        if user_id in carts:
            for item in carts[user_id]["items"]:
                if item["product_id"] == product_id:
                    item["quantity"] = quantity
                    break
        
        CartStore._save_carts(carts)
        return carts.get(user_id, {"items": []})
    
    @staticmethod
    def clear_cart(user_id: str) -> dict:
        """Clear user's cart"""
        carts = CartStore._load_carts()
        
        if user_id in carts:
            carts[user_id]["items"] = []
        
        CartStore._save_carts(carts)
        return {"items": []}


class OrderStore:
    """Order storage with JSON persistence"""
    
    @staticmethod
    def _ensure_file():
        """Ensure orders.json exists"""
        ORDERS_FILE.parent.mkdir(parents=True, exist_ok=True)
        if not ORDERS_FILE.exists():
            ORDERS_FILE.write_text(json.dumps({}))
    
    @staticmethod
    def _load_orders() -> dict:
        """Load all orders from file"""
        OrderStore._ensure_file()
        try:
            return json.loads(ORDERS_FILE.read_text())
        except:
            return {}
    
    @staticmethod
    def _save_orders(orders: dict):
        """Save orders to file"""
        OrderStore._ensure_file()
        ORDERS_FILE.write_text(json.dumps(orders, indent=2, default=str))
    
    @staticmethod
    def create_order(
        user_id: str, 
        items: List[CartItem], 
        total_price: float,
        shipping_address: str,
        shipping_city: str,
        shipping_zip: str
    ) -> dict:
        """Create new order"""
        orders = OrderStore._load_orders()
        
        if user_id not in orders:
            orders[user_id] = []
        
        order_id = str(uuid.uuid4())[:8]
        
        order = {
            "order_id": order_id,
            "user_id": user_id,
            "items": [item.model_dump() for item in items],
            "total_price": total_price,
            "shipping_address": shipping_address,
            "shipping_city": shipping_city,
            "shipping_zip": shipping_zip,
            "status": "pending",
            "created_at": datetime.utcnow().isoformat()
        }
        
        orders[user_id].append(order)
        OrderStore._save_orders(orders)
        
        logger.info(f"Order {order_id} created for user {user_id}")
        return order
    
    @staticmethod
    def get_user_orders(user_id: str) -> list:
        """Get all orders for a user"""
        orders = OrderStore._load_orders()
        return orders.get(user_id, [])
    
    @staticmethod
    def get_order(user_id: str, order_id: str) -> Optional[dict]:
        """Get specific order"""
        orders = OrderStore._load_orders()
        user_orders = orders.get(user_id, [])
        
        for order in user_orders:
            if order["order_id"] == order_id:
                return order
        
        return None
    
    @staticmethod
    def update_order_status(user_id: str, order_id: str, status: str) -> Optional[dict]:
        """Update order status"""
        orders = OrderStore._load_orders()
        
        if user_id in orders:
            for order in orders[user_id]:
                if order["order_id"] == order_id:
                    order["status"] = status
                    OrderStore._save_orders(orders)
                    return order
        
        return None


def calculate_total_price(items: List[CartItem]) -> float:
    """Calculate total price of cart items"""
    return sum(item.price * item.quantity for item in items)
