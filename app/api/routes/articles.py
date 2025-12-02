from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from clients.shopware5_client import Shopware5Client
from clients.shopify_client import ShopifyClient

router = APIRouter()


# ==================== SHOPWARE 5 ARTICLE ENDPOINTS ====================

@router.get("/shopware/articles")
async def get_sw5_articles(
    limit: int = Query(50, ge=1, le=250),
    offset: int = Query(0, ge=0)
):
    """
    Get list of articles from Shopware 5
    """
    try:
        client = Shopware5Client()
        return client.get_articles(limit=limit, offset=offset)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/shopware/articles/{article_id}")
async def get_sw5_article(article_id: int):
    """
    Get single article from Shopware 5 by ID
    """
    try:
        client = Shopware5Client()
        return client.get_article(article_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/shopware/fields")
async def get_sw5_article_fields(identifier: Optional[str] = None):
    """
    Get available article fields from Shopware 5
    Optionally provide an identifier (article number or ID) to get fields from a specific article
    """
    try:
        client = Shopware5Client()

        # If specific identifier provided, get that article's fields
        if identifier:
            # Try to get the article by ID or number
            try:
                article_id = int(identifier)
                article = client.get_article(article_id)
            except ValueError:
                # Not a number, try as article number
                articles = client.get_articles(limit=1)
                article = None
                if 'data' in articles:
                    for a in articles['data']:
                        if a.get('mainDetail', {}).get('number') == identifier:
                            article = a
                            break

                if not article:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Artikel mit Identifier '{identifier}' nicht gefunden"
                    )

            fields = client.extract_fields_from_data(article)
        else:
            # Get fields from multiple articles
            fields = client.get_article_fields()

        return {"fields": fields}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/test")
async def test_sw5_connection():
    """
    Test Shopware 5 connection
    """
    try:
        client = Shopware5Client()
        result = client.test_connection()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== SHOPIFY PRODUCT ENDPOINTS ====================

@router.get("/shopify/products")
async def get_shopify_products(limit: int = Query(50, ge=1, le=250)):
    """
    Get list of products from Shopify
    """
    try:
        client = ShopifyClient()
        return client.get_products(limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/shopify/products/find-by-sku/{sku}")
async def find_product_by_sku(sku: str):
    """
    Find Shopify product by SKU
    """
    try:
        client = ShopifyClient()
        return client.find_product_by_sku(sku)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/shopify/fields")
async def get_shopify_product_fields(identifier: Optional[str] = None):
    """
    Get available product fields from Shopify
    Optionally provide an identifier (product ID or SKU) to get fields from a specific product
    """
    try:
        client = ShopifyClient()

        # If specific identifier provided, get that product's fields
        if identifier:
            # Try to find by SKU first, then by ID
            try:
                product = client.find_product_by_sku(identifier)
            except:
                try:
                    # Try as product ID
                    product_id = identifier.replace('gid://shopify/Product/', '')
                    products = client.get_products(limit=1)
                    product = None
                    if 'products' in products:
                        for p in products['products']:
                            if str(p['id']) == product_id:
                                product = p
                                break

                    if not product:
                        raise HTTPException(
                            status_code=404,
                            detail=f"Produkt mit Identifier '{identifier}' nicht gefunden"
                        )
                except Exception as e:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Produkt mit Identifier '{identifier}' nicht gefunden"
                    )

            fields = client._extract_fields_from_object(product, prefix="")
        else:
            # Get fields from multiple products
            fields = client.get_shopify_product_fields()

        return {"fields": fields}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
