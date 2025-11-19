from fastapi import APIRouter, HTTPException, Query, Body
from typing import List, Dict, Any
from clients.shopify_client import ShopifyClient

router = APIRouter()


@router.get("/test")
async def test_shopify_connection():
    """Test connection to Shopify API"""
    try:
        client = ShopifyClient()
        result = client.test_connection()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/products")
async def get_products(
    limit: int = Query(default=50, ge=1, le=250),
    page_info: str = Query(default=None)
):
    """Get products from Shopify"""
    try:
        client = ShopifyClient()
        result = client.get_products(limit=limit, page_info=page_info)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/products/{product_id}")
async def get_product(product_id: int):
    """Get single product by ID"""
    try:
        client = ShopifyClient()
        result = client.get_product(product_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/fields")
async def get_product_fields(product_identifier: str = Query(default=None)):
    """Get all available Shopify product fields

    If product_identifier is provided, extract fields from that specific product (by ID or SKU)
    Otherwise, extract fields from multiple products
    """
    try:
        client = ShopifyClient()

        if product_identifier:
            try:
                fields = client.get_shopify_product_fields(product_identifier)
                # Get product info for response
                product = client.get_product_by_identifier(product_identifier)
                return {
                    "fields": fields,
                    "count": len(fields),
                    "product_identifier": product_identifier,
                    "product_title": product.get('title', 'Unknown') if product else None,
                    "product_id": product.get('id') if product else None
                }
            except Exception as e:
                print(f"Error getting fields for product {product_identifier}: {e}")
                raise HTTPException(
                    status_code=404,
                    detail=f"Produkt '{product_identifier}' nicht gefunden. Bitte prüfen Sie die Produkt-ID oder SKU."
                )
        else:
            fields = client.get_shopify_product_fields()
            return {
                "fields": fields,
                "count": len(fields)
            }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in get_product_fields: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/products")
async def create_product(product_data: Dict = Body(...)):
    """Create a new product in Shopify"""
    try:
        client = ShopifyClient()
        result = client.create_product(product_data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/products/{product_id}")
async def update_product(product_id: int, product_data: Dict = Body(...)):
    """Update an existing product in Shopify"""
    try:
        client = ShopifyClient()
        result = client.update_product(product_id, product_data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/products/find-by-sku/{sku}")
async def find_product_by_sku(sku: str):
    """Find a product by SKU"""
    try:
        client = ShopifyClient()
        result = client.find_product_by_sku(sku)
        if result is None:
            raise HTTPException(status_code=404, detail=f"Product with SKU {sku} not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
