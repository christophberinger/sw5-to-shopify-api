from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from clients.shopware5_client import Shopware5Client
from clients.shopify_client import ShopifyClient

router = APIRouter()


# ==================== SHOPWARE 5 CUSTOMER ENDPOINTS ====================

@router.get("/shopware/customers")
async def get_sw5_customers(
    limit: int = Query(50, ge=1, le=250),
    offset: int = Query(0, ge=0)
):
    """
    Get list of customers from Shopware 5
    """
    try:
        client = Shopware5Client()
        return client.get_customers(limit=limit, offset=offset)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/shopware/customers/{customer_id}")
async def get_sw5_customer(customer_id: int):
    """
    Get single customer from Shopware 5 by ID
    """
    try:
        client = Shopware5Client()
        return client.get_customer(customer_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/shopware/fields")
async def get_sw5_customer_fields(email: Optional[str] = None):
    """
    Get available customer fields from Shopware 5
    Optionally provide an email to get fields from a specific customer
    """
    try:
        client = Shopware5Client()

        # If specific email provided, get that customer's fields
        if email:
            customer = client.get_customer_by_email(email)
            if customer:
                fields = client._extract_fields_from_object(customer, prefix="")
                return {"fields": fields}
            else:
                raise HTTPException(status_code=404, detail=f"Customer with email {email} not found")

        # Otherwise get generic customer fields
        fields = client.get_customer_fields()
        return {"fields": fields}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== SHOPIFY CUSTOMER ENDPOINTS ====================

@router.get("/shopify/customers")
async def get_shopify_customers(
    limit: int = Query(50, ge=1, le=250),
    page_info: Optional[str] = None
):
    """
    Get list of customers from Shopify
    """
    try:
        client = ShopifyClient()
        return client.get_customers(limit=limit, page_info=page_info)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/shopify/customers/{customer_id}")
async def get_shopify_customer(customer_id: int):
    """
    Get single customer from Shopify by ID
    """
    try:
        client = ShopifyClient()
        return client.get_customer(customer_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/shopify/fields")
async def get_shopify_customer_fields():
    """
    Get available customer fields from Shopify
    """
    try:
        client = ShopifyClient()
        fields = client.get_customer_fields()
        return {"fields": fields}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== CONNECTION TEST ====================

@router.get("/test")
async def test_connections():
    """
    Test connections to both Shopware 5 and Shopify for customer endpoints
    """
    results = {
        "shopware5": {"success": False},
        "shopify": {"success": False}
    }

    # Test Shopware 5
    try:
        sw5_client = Shopware5Client()
        customers = sw5_client.get_customers(limit=1)
        if customers.get('success') == False:
            results["shopware5"] = {"success": False, "error": customers.get('message', 'Unknown error')}
        else:
            results["shopware5"] = {"success": True, "message": "Customer API accessible"}
    except Exception as e:
        results["shopware5"] = {"success": False, "error": str(e)}

    # Test Shopify
    try:
        shopify_client = ShopifyClient()
        customers = shopify_client.get_customers(limit=1)
        results["shopify"] = {"success": True, "message": "Customer API accessible"}
    except Exception as e:
        results["shopify"] = {"success": False, "error": str(e)}

    return results
