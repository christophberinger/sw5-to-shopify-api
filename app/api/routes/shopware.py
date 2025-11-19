from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any
from clients.shopware5_client import Shopware5Client

router = APIRouter()


@router.get("/test")
async def test_shopware_connection():
    """Test connection to Shopware 5 API"""
    try:
        client = Shopware5Client()
        result = client.test_connection()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/articles")
async def get_articles(
    limit: int = Query(default=50, ge=1, le=1000),
    offset: int = Query(default=0, ge=0)
):
    """Get articles from Shopware 5"""
    try:
        client = Shopware5Client()
        result = client.get_articles(limit=limit, offset=offset)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/articles/{article_id}")
async def get_article(article_id: int):
    """Get single article by ID"""
    try:
        client = Shopware5Client()
        result = client.get_article(article_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/fields")
async def get_article_fields(article_number: str = Query(default=None)):
    """Get all available article fields from Shopware 5

    If article_number is provided, extract fields from that specific article
    Otherwise, extract fields from multiple articles
    """
    try:
        client = Shopware5Client()

        if article_number:
            try:
                # Get specific article by number
                article = client.get_article_by_number(article_number)
                fields = client._extract_fields_from_object(article, prefix="")
                return {
                    "fields": fields,
                    "count": len(fields),
                    "article_number": article_number,
                    "article_name": article.get('name', 'Unknown')
                }
            except Exception as e:
                # If article not found, log error and return empty fields
                print(f"Error finding article {article_number}: {e}")
                raise HTTPException(
                    status_code=404,
                    detail=f"Artikel '{article_number}' nicht gefunden. Bitte prüfen Sie die Artikelnummer."
                )
        else:
            # Get fields from multiple articles
            fields = client.get_article_fields()
            return {
                "fields": fields,
                "count": len(fields)
            }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in get_article_fields: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/articles/{article_id}/pickware")
async def get_pickware_fields(article_id: int):
    """Get Pickware specific fields for an article"""
    try:
        client = Shopware5Client()
        result = client.get_pickware_fields(article_id)
        if result is None:
            return {"message": "No Pickware fields found", "fields": {}}
        return {"fields": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
