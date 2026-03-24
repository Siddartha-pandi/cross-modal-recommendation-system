"""
Shopping cart and order routes
"""
from fastapi import APIRouter, HTTPException, Depends
from urllib.parse import unquote
from typing import List, Dict, Any
import logging

from app.auth.utils import get_current_user
from app.schemas.cart import (
    CartStore, OrderStore, CartItem, CartResponse, 
    AddToCartRequest, CheckoutRequest, OrderResponse, calculate_total_price
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/cart", tags=["Shopping Cart & Orders"])


@router.get("/", response_model=CartResponse)
async def get_cart(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get user's shopping cart"""
    user_id = current_user.get("user_id")
    cart_data = CartStore.get_cart(user_id)
    items = [CartItem(**item) for item in cart_data["items"]]
    
    return CartResponse(
        user_id=user_id,
        items=items,
        total_price=calculate_total_price(items),
        item_count=len(items)
    )


@router.post("/add", response_model=CartResponse)
async def add_to_cart(
    request: AddToCartRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Add item to cart"""
    try:
        user_id = current_user.get("user_id")
        logger.info(f"Adding to cart for user {user_id}: {request.product_id} - {request.title}")
        
        item = CartItem(
            product_id=request.product_id,
            title=request.title,
            price=request.price,
            quantity=request.quantity,
            image_url=request.image_url
        )
        
        cart_data = CartStore.add_item(user_id, item)
        items = [CartItem(**item) for item in cart_data["items"]]
        
        logger.info(f"User {user_id} successfully added {request.title} to cart. Cart now has {len(items)} items")
        
        return CartResponse(
            user_id=user_id,
            items=items,
            total_price=calculate_total_price(items),
            item_count=len(items)
        )
    except Exception as e:
        logger.error(f"Error adding to cart for user {current_user.get('user_id')}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to add item to cart: {str(e)}")


@router.delete("/remove/{product_id:path}", response_model=CartResponse)
async def remove_from_cart(
    product_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Remove item from cart"""
    try:
        user_id = current_user.get("user_id")
        decoded_product_id = unquote(product_id)
        logger.info(f"[remove_from_cart] user_id: {user_id}, product_id: {product_id}, decoded_product_id: {decoded_product_id}")
        # Remove item if present, otherwise just return cart (idempotent)
        cart_data = CartStore.remove_item(user_id, decoded_product_id)
        items = [CartItem(**item) for item in cart_data["items"]]
        logger.info(f"User {user_id} removed product {decoded_product_id} from cart (idempotent)")
        return CartResponse(
            user_id=user_id,
            items=items,
            total_price=calculate_total_price(items),
            item_count=len(items)
        )
    except Exception as e:
        logger.error(f"Error removing from cart: {e}")
        # Always return success if not found (idempotent)
        return CartResponse(
            user_id=current_user.get("user_id"),
            items=[],
            total_price=0.0,
            item_count=0
        )


@router.put("/update/{product_id:path}/{quantity}", response_model=CartResponse)
async def update_cart_item(
    product_id: str,
    quantity: int,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Update item quantity in cart"""
    try:
        if quantity <= 0:
            # If quantity is 0 or less, treat it as a removal
            return await remove_from_cart(product_id, current_user)

        user_id = current_user.get("user_id")
        decoded_product_id = unquote(product_id)
        
        cart_data = CartStore.update_quantity(user_id, decoded_product_id, quantity)
        items = [CartItem(**item) for item in cart_data["items"]]
        
        logger.info(f"User {user_id} updated quantity of {decoded_product_id} to {quantity}")
        
        return CartResponse(
            user_id=user_id,
            items=items,
            total_price=calculate_total_price(items),
            item_count=len(items)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating quantity: {e}")
        raise HTTPException(status_code=500, detail="Failed to update item quantity")


@router.delete("/clear", response_model=CartResponse)
async def clear_cart(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Clear all items from cart"""
    try:
        user_id = current_user.get("user_id")
        CartStore.clear_cart(user_id)
        logger.info(f"User {user_id} cleared cart")
        
        return CartResponse(
            user_id=user_id,
            items=[],
            total_price=0.0,
            item_count=0
        )
    except Exception as e:
        logger.error(f"Error clearing cart: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear cart")


# --- Order Routes ---

order_router = APIRouter(prefix="/orders", tags=["Orders"])


@order_router.post("/checkout", response_model=OrderResponse)
async def checkout(
    request: CheckoutRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Checkout and create order from cart
    
    Steps:
    1. Get items from user's cart
    2. Validate cart has items
    3. Create order in database
    4. Clear user's cart
    5. Return order details
    """
    try:
        user_id = current_user.get("user_id")
        # Get cart items
        cart_data = CartStore.get_cart(user_id)
        items_data = cart_data.get("items", [])
        
        if not items_data:
            raise HTTPException(status_code=400, detail="Cart is empty")
        
        # Convert to CartItem objects
        items = [CartItem(**item) for item in items_data]
        total_price = calculate_total_price(items)
        
        # Validate shipping info
        if not request.shipping_address or not request.shipping_city or not request.shipping_zip:
            raise HTTPException(status_code=400, detail="Complete shipping address is required")
        
        # Create order
        order = OrderStore.create_order(
            user_id=user_id,
            items=items,
            total_price=total_price,
            shipping_address=request.shipping_address,
            shipping_city=request.shipping_city,
            shipping_zip=request.shipping_zip
        )
        
        # Clear cart after successful order
        CartStore.clear_cart(user_id)
        
        logger.info(f"Order {order['order_id']} created for user {user_id} with total ${total_price:.2f}")
        
        return OrderResponse(
            order_id=order["order_id"],
            user_id=order["user_id"],
            items=items,
            total_price=order["total_price"],
            shipping_address=order["shipping_address"],
            shipping_city=order["shipping_city"],
            shipping_zip=order["shipping_zip"],
            status=order["status"],
            created_at=order["created_at"]
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Checkout error: {e}")
        raise HTTPException(status_code=500, detail="Checkout failed")


@order_router.get("/", response_model=List[OrderResponse])
async def get_user_orders(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get all orders for current user"""
    try:
        user_id = current_user.get("user_id")
        orders = OrderStore.get_user_orders(user_id)
        return [
            OrderResponse(
                order_id=order["order_id"],
                user_id=order["user_id"],
                items=[CartItem(**item) for item in order["items"]],
                total_price=order["total_price"],
                shipping_address=order["shipping_address"],
                shipping_city=order["shipping_city"],
                shipping_zip=order["shipping_zip"],
                status=order["status"],
                created_at=order["created_at"]
            )
            for order in orders
        ]
    except Exception as e:
        logger.error(f"Error retrieving orders: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve orders")


@order_router.get("/{order_id}", response_model=OrderResponse)
async def get_order_details(
    order_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get specific order details"""
    try:
        user_id = current_user.get("user_id")
        logger.info(f"Fetching order {order_id} for user {user_id}")
        
        order = OrderStore.get_order(user_id, order_id)
        
        if not order:
            logger.warning(f"Order {order_id} not found for user {user_id}")
            # Log all orders for this user for debugging
            all_orders = OrderStore.get_user_orders(user_id)
            logger.info(f"User {user_id} has {len(all_orders)} total orders")
            if all_orders:
                order_ids = [o.get('order_id') for o in all_orders]
                logger.info(f"Available order IDs: {order_ids}")
            raise HTTPException(status_code=404, detail="Order not found")
        
        logger.info(f"Successfully retrieved order {order_id} for user {user_id}")
        return OrderResponse(
            order_id=order["order_id"],
            user_id=order["user_id"],
            items=[CartItem(**item) for item in order["items"]],
            total_price=order["total_price"],
            shipping_address=order["shipping_address"],
            shipping_city=order["shipping_city"],
            shipping_zip=order["shipping_zip"],
            status=order["status"],
            created_at=order["created_at"]
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving order {order_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve order")


@order_router.post("/{order_id}/buy-now", response_model=OrderResponse)
async def buy_now(
    order_id: str,
    request: CheckoutRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Process buy now from a single product
    In a real system, this would be called with a single item
    """
    # This endpoint allows buying an item directly without adding to cart first
    # For now, it behaves like checkout
    return await checkout(request, current_user)
