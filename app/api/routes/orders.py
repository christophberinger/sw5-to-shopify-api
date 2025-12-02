from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from clients.shopware5_client import Shopware5Client
from clients.shopify_client import ShopifyClient

router = APIRouter()


# ==================== SHOPWARE 5 ORDER ENDPOINTS ====================

@router.get("/shopware/orders")
async def get_sw5_orders(
    limit: int = Query(50, ge=1, le=250),
    offset: int = Query(0, ge=0),
    status: Optional[str] = None
):
    """
    Get list of orders from Shopware 5
    """
    try:
        client = Shopware5Client()
        return client.get_orders(limit=limit, offset=offset, status=status)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/shopware/orders/{order_id}")
async def get_sw5_order(order_id: int):
    """
    Get single order from Shopware 5 by ID
    """
    try:
        client = Shopware5Client()
        return client.get_order(order_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/shopware/fields")
async def get_sw5_order_fields(order_number: Optional[str] = None):
    """
    Get available order fields from Shopware 5
    Optionally provide an order number to get fields from a specific order
    """
    try:
        client = Shopware5Client()

        # If specific order number provided, get that order's fields
        if order_number:
            order = client.get_order_by_number(order_number)
            if order:
                fields = client._extract_fields_from_object(order, prefix="")
                return {"fields": fields}
            else:
                raise HTTPException(status_code=404, detail=f"Order with number {order_number} not found")

        # Otherwise get generic order fields
        fields = client.get_order_fields()
        return {"fields": fields}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== SHOPIFY ORDER ENDPOINTS ====================

@router.get("/shopify/orders")
async def get_shopify_orders(
    limit: int = Query(50, ge=1, le=250),
    status: str = Query("any", description="Order status filter"),
    page_info: Optional[str] = None
):
    """
    Get list of orders from Shopify (READ-ONLY)
    Note: Shopify orders cannot be created via API, only read
    """
    try:
        client = ShopifyClient()
        return client.get_orders(limit=limit, status=status, page_info=page_info)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/shopify/orders/{order_id}")
async def get_shopify_order(order_id: int):
    """
    Get single order from Shopify by ID (READ-ONLY)
    """
    try:
        client = ShopifyClient()
        return client.get_order(order_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/shopify/fields")
async def get_shopify_order_fields():
    """
    Get available order fields from Shopify
    Note: Orders are READ-ONLY via API (created via checkout only)
    """
    try:
        client = ShopifyClient()
        fields = client.get_order_fields()
        return {"fields": fields, "read_only": True, "note": "Shopify orders are created via checkout, not API"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== CONNECTION TEST ====================

@router.get("/test")
async def test_connections():
    """
    Test connections to both Shopware 5 and Shopify for order endpoints
    """
    results = {
        "shopware5": {"success": False},
        "shopify": {"success": False}
    }

    # Test Shopware 5
    try:
        sw5_client = Shopware5Client()
        orders = sw5_client.get_orders(limit=1)
        if orders.get('success') == False:
            results["shopware5"] = {"success": False, "error": orders.get('message', 'Unknown error')}
        else:
            results["shopware5"] = {"success": True, "message": "Order API accessible"}
    except Exception as e:
        results["shopware5"] = {"success": False, "error": str(e)}

    # Test Shopify
    try:
        shopify_client = ShopifyClient()
        orders = shopify_client.get_orders(limit=1)
        results["shopify"] = {"success": True, "message": "Order API accessible (read-only)"}
    except Exception as e:
        results["shopify"] = {"success": False, "error": str(e)}

    return results
