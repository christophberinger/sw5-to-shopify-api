from fastapi import APIRouter, HTTPException, Body
from typing import Dict, List, Any, Union
from pydantic import BaseModel
from clients.shopware5_client import Shopware5Client
from clients.shopify_client import ShopifyClient
from utils.transformations import apply_transformation

router = APIRouter()


class TransformationRule(BaseModel):
    type: str = "direct"  # direct, replace, regex, split_join, custom
    find: str = ""  # for replace/regex
    replace: str = ""  # for replace/regex
    split_delimiter: str = ""  # for split_join
    join_delimiter: str = ""  # for split_join
    custom_code: str = ""  # for custom transformations


class FieldMapping(BaseModel):
    sw5_field: str
    shopify_field: str
    transformation: TransformationRule = TransformationRule()


class MappingConfig(BaseModel):
    mappings: List[FieldMapping]


class ProductSyncRequest(BaseModel):
    sw5_article_ids: List[Union[int, str]]
    mapping: List[FieldMapping]
    mode: str = "update"  # update, create, or upsert


def validate_mapping_for_sync(mappings: List[FieldMapping], mode: str) -> Dict[str, Any]:
    """
    Validate that the mapping includes all required Shopify fields
    """
    mapped_fields = [m.shopify_field for m in mappings]

    missing_fields = []
    warnings = []

    # Check for required product fields (needed for create and upsert modes)
    if mode in ["create", "upsert"]:
        if "title" not in mapped_fields:
            missing_fields.append("title")

    # Check for required variant fields
    has_variant_price = any(f.startswith("variants[].") and "price" in f for f in mapped_fields)
    if not has_variant_price:
        missing_fields.append("variants[].price")

    # SKU is REQUIRED for update and upsert modes (to find existing products)
    has_variant_sku = any(f.startswith("variants[].") and "sku" in f for f in mapped_fields)
    if not has_variant_sku:
        if mode in ["update", "upsert"]:
            missing_fields.append("variants[].sku (PFLICHTFELD für Update/Upsert - ohne SKU werden immer neue Produkte erstellt!)")
        else:
            warnings.append("variants[].sku nicht gemappt - stark empfohlen für Produktidentifikation")

    if missing_fields:
        return {
            "valid": False,
            "message": f"Pflichtfelder fehlen: {', '.join(missing_fields)}. Bitte fügen Sie diese Felder zu Ihrem Mapping hinzu.",
            "missing_fields": missing_fields,
            "warnings": warnings
        }

    return {
        "valid": True,
        "message": "Mapping ist gültig",
        "missing_fields": [],
        "warnings": warnings
    }


def validate_shopify_product(product: Dict, mode: str) -> Dict[str, Any]:
    """
    Validate that the transformed product has all required fields
    """
    missing_fields = []

    # Check for required product fields
    if mode in ["create", "upsert"]:
        if not product.get("title"):
            missing_fields.append("title (Wert ist leer oder nicht vorhanden)")

    # Check for variants and price
    if "variants" in product and len(product["variants"]) > 0:
        variant = product["variants"][0]
        if "price" not in variant or variant["price"] is None:
            missing_fields.append("variants[].price (Wert ist leer oder nicht vorhanden)")

        # SKU is required for update/upsert to find existing products
        if mode in ["update", "upsert"]:
            if "sku" not in variant or not variant["sku"]:
                missing_fields.append("variants[].sku (Wert ist leer oder nicht vorhanden - PFLICHTFELD für Update/Upsert!)")
    else:
        missing_fields.append("variants (keine Varianten gefunden)")

    if missing_fields:
        return {
            "valid": False,
            "message": f"Fehlende oder leere Produktfelder: {', '.join(missing_fields)}"
        }

    return {
        "valid": True,
        "message": "Product ist gültig"
    }


@router.post("/transform")
async def transform_product(
    sw5_article_id: int = Body(...),
    mapping: List[FieldMapping] = Body(...)
):
    """
    Transform a SW5 article to Shopify product format using mapping
    """
    try:
        sw5_client = Shopware5Client()
        article = sw5_client.get_article(sw5_article_id)

        # Transform article based on mapping
        shopify_product = transform_article_to_product(article, mapping)

        return {
            "sw5_article": article,
            "shopify_product": shopify_product,
            "mapping_applied": len(mapping)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync")
async def sync_products(request: ProductSyncRequest):
    """
    Sync products from SW5 to Shopify using mapping
    """
    try:
        # Validate mapping before starting sync
        validation_result = validate_mapping_for_sync(request.mapping, request.mode)
        if not validation_result["valid"]:
            raise HTTPException(
                status_code=400,
                detail=f"Mapping validation failed: {validation_result['message']}"
            )

        sw5_client = Shopware5Client()
        shopify_client = ShopifyClient()

        # Get metafield definitions to use correct types
        metafield_defs = shopify_client.get_metafield_definitions()
        metafield_types = {
            f"{mf['namespace']}.{mf['key']}": mf.get('type', 'single_line_text_field')
            for mf in metafield_defs
        }

        results = []
        total_articles = len(request.sw5_article_ids)

        for index, article_id in enumerate(request.sw5_article_ids, start=1):
            # Progress indicator
            print(f"\n{'#'*60}")
            print(f"PROGRESS: {index}/{total_articles} ({int(index/total_articles*100)}%)")
            print(f"{'#'*60}\n")

            try:
                # Get SW5 article (supports both int ID and string order number)
                if isinstance(article_id, int):
                    article = sw5_client.get_article(article_id)
                else:
                    # Try as order number first, fall back to ID if numeric string
                    try:
                        article = sw5_client.get_article_by_number(str(article_id))
                    except:
                        # If string is numeric, try as ID
                        if str(article_id).isdigit():
                            article = sw5_client.get_article(int(article_id))
                        else:
                            raise

                # Debug: Check what we got from SW5
                print(f"\n{'='*60}")
                print(f"Processing Article ID: {article_id}")
                print(f"Sync Mode: {request.mode}")
                print(f"\n=== SW5 ARTICLE DATA ===")
                print(f"Article ID: {article.get('id')}")
                print(f"Article Name: {article.get('name')}")
                print(f"Article Number: {article.get('mainDetail', {}).get('number') if article.get('mainDetail') else 'NO mainDetail'}")
                print(f"Has mainDetail: {bool(article.get('mainDetail'))}")
                if article.get('mainDetail'):
                    main_detail = article['mainDetail']
                    print(f"  - mainDetail.number: {main_detail.get('number')}")
                    print(f"  - mainDetail.price: {main_detail.get('prices', [{}])[0].get('price') if main_detail.get('prices') else 'NO PRICES'}")
                else:
                    print(f"  ⚠️  WARNING: No mainDetail found - this will cause missing variants!")
                print(f"Article keys: {list(article.keys())}")
                print(f"========================\n")

                # Determine if we need existing product data for update
                existing_product = None

                if request.mode in ["update", "upsert"]:
                    sku = get_value_from_article(article, "mainDetail.number")
                    print(f"Extracted SKU from SW5 article: '{sku}'")

                    if sku:
                        print(f"Searching for existing product with SKU '{sku}' in Shopify...")
                        existing = shopify_client.find_product_by_sku(sku)

                        if existing:
                            print(f"✓ Found existing product: ID {existing['id']}")
                            # Fetch full product details including variant IDs
                            existing_product = shopify_client.get_product(existing['id'])
                            print(f"✓ Fetched full product details")
                        else:
                            print(f"✗ No existing product found with SKU '{sku}'")
                            if request.mode == "upsert":
                                print("  → Will CREATE new product")
                            else:
                                print("  → Will FAIL (update mode requires existing product)")
                    else:
                        print("✗ No SKU found in SW5 article (mainDetail.number is empty)")
                        print("  → Cannot search for existing product without SKU")
                else:
                    print(f"Mode is 'create' - skipping existing product search")

                print(f"{'='*60}\n")

                # Transform to Shopify format (pass existing product to preserve IDs)
                shopify_product = transform_article_to_product(
                    article,
                    request.mapping,
                    metafield_types,
                    existing_product
                )

                # Debug: Log metafield values
                if 'metafields' in shopify_product:
                    for mf in shopify_product['metafields']:
                        print(f"DEBUG: Metafield {mf['namespace']}.{mf['key']} type={mf['type']} value={mf['value'][:100]}")

                # Validate transformed product
                product_validation = validate_shopify_product(shopify_product, request.mode)
                if not product_validation["valid"]:
                    raise Exception(f"Product validation failed: {product_validation['message']}")

                # Sync to Shopify based on mode
                print(f"=== SYNCING TO SHOPIFY ===")
                if request.mode == "create":
                    print(f"Action: CREATE new product (mode=create)")
                    result = shopify_client.create_product(shopify_product)
                    status = "created"
                    print(f"✓ Created product with ID: {result.get('product', {}).get('id')}")
                elif request.mode == "update":
                    if existing_product:
                        product_id = existing_product['product']['id']
                        print(f"Action: UPDATE existing product ID {product_id}")
                        result = shopify_client.update_product(product_id, shopify_product)
                        status = "updated"
                        print(f"✓ Updated product ID: {product_id}")
                    else:
                        sku = get_value_from_article(article, "mainDetail.number")
                        raise Exception(f"Product with SKU {sku} not found in Shopify")
                else:  # upsert
                    if existing_product:
                        product_id = existing_product['product']['id']
                        print(f"Action: UPDATE existing product ID {product_id} (mode=upsert, product found)")
                        result = shopify_client.update_product(product_id, shopify_product)
                        status = "updated"
                        print(f"✓ Updated product ID: {product_id}")
                    else:
                        print(f"Action: CREATE new product (mode=upsert, no existing product found)")
                        result = shopify_client.create_product(shopify_product)
                        status = "created"
                        print(f"✓ Created product with ID: {result.get('product', {}).get('id')}")
                print(f"========================\n")

                results.append({
                    "sw5_article_id": article_id,
                    "status": status,
                    "success": True,
                    "shopify_product_id": result.get('product', {}).get('id')
                })

            except Exception as e:
                results.append({
                    "sw5_article_id": article_id,
                    "status": "error",
                    "success": False,
                    "error": str(e)
                })

        # Final summary
        successful = sum(1 for r in results if r['success'])
        failed = sum(1 for r in results if not r['success'])
        print(f"\n{'='*60}")
        print(f"SYNC ABGESCHLOSSEN")
        print(f"Total: {len(request.sw5_article_ids)} | Erfolgreich: {successful} | Fehlgeschlagen: {failed}")
        print(f"{'='*60}\n")

        return {
            "total": len(request.sw5_article_ids),
            "successful": successful,
            "failed": failed,
            "results": results
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def get_value_from_article(article: Dict, path: str) -> Any:
    """
    Get value from article using dot notation path
    Example: "mainDetail.number" -> article['mainDetail']['number']
    """
    try:
        keys = path.split('.')
        value = article

        for key in keys:
            # Handle array notation
            if '[' in key and ']' in key:
                key_name = key[:key.index('[')]
                index = int(key[key.index('[') + 1:key.index(']')])
                value = value[key_name][index]
            else:
                value = value[key]

        return value
    except (KeyError, IndexError, TypeError):
        return None


def transform_article_to_product(
    article: Dict,
    mappings: List[FieldMapping],
    metafield_types: Dict[str, str] = None,
    existing_product: Dict = None
) -> Dict:
    """
    Transform SW5 article to Shopify product using mappings with transformations

    Args:
        article: SW5 article data
        mappings: Field mappings
        metafield_types: Optional dict mapping "namespace.key" to metafield type
        existing_product: Optional existing Shopify product (for updates, to preserve IDs)
    """
    article_id = article.get('id', 'unknown')
    print(f"\n=== TRANSFORM DEBUG for Article {article_id} ===")
    print(f"Number of mappings: {len(mappings)}")

    # Log what's being mapped
    mapped_fields = [m.shopify_field for m in mappings]
    print(f"Mapped Shopify fields: {mapped_fields}")

    # Check for required fields in mapping
    has_title = any('title' == f for f in mapped_fields)
    has_variant_price = any(f.startswith('variants[].') and 'price' in f for f in mapped_fields)
    print(f"Has 'title' mapping: {has_title}")
    print(f"Has 'variants[].price' mapping: {has_variant_price}")

    shopify_product = {}
    variants = [{}]

    if metafield_types is None:
        metafield_types = {}

    # If updating an existing product and it has variants, preserve the first variant's ID
    if existing_product and 'product' in existing_product:
        existing_variants = existing_product['product'].get('variants', [])
        if existing_variants and len(existing_variants) > 0:
            variants[0]['id'] = existing_variants[0].get('id')

    for mapping in mappings:
        sw5_value = get_value_from_article(article, mapping.sw5_field)

        if sw5_value is None:
            print(f"  ⚠️  {mapping.sw5_field} -> {mapping.shopify_field}: No value found in SW5 article")
            continue

        print(f"  ✓ {mapping.sw5_field} -> {mapping.shopify_field}: '{str(sw5_value)[:100]}'...")

        # Determine if this is a metafield and get its type
        metafield_type_for_transform = None
        shopify_field = mapping.shopify_field
        if shopify_field.startswith("metafields[]."):
            parts = shopify_field.replace("metafields[].", "").split(".", 1)
            if len(parts) == 2:
                namespace, key = parts
                metafield_key = f"{namespace}.{key}"
                metafield_type_for_transform = metafield_types.get(metafield_key, "single_line_text_field")

        # Apply transformation rules with metafield type information
        transformation_dict = mapping.transformation.dict() if hasattr(mapping.transformation, 'dict') else mapping.transformation
        transformed_value = apply_transformation(
            sw5_value,
            transformation_dict,
            shopify_field,
            metafield_type_for_transform
        )

        # Handle variant fields
        if shopify_field.startswith("variants[]."):
            field_name = shopify_field.replace("variants[].", "")
            variants[0][field_name] = transformed_value
        # Handle metafields
        elif shopify_field.startswith("metafields[]."):
            # Extract namespace and key from path like "metafields[].custom.my_field"
            parts = shopify_field.replace("metafields[].", "").split(".", 1)
            if len(parts) == 2:
                namespace, key = parts
                if "metafields" not in shopify_product:
                    shopify_product["metafields"] = []

                # Look up the correct metafield type
                metafield_key = f"{namespace}.{key}"
                metafield_type = metafield_types.get(metafield_key, "single_line_text_field")

                shopify_product["metafields"].append({
                    "namespace": namespace,
                    "key": key,
                    "value": str(transformed_value),
                    "type": metafield_type
                })
        else:
            shopify_product[shopify_field] = transformed_value

    # Add variants if any variant fields were mapped
    if variants[0]:
        shopify_product["variants"] = variants

    # Debug: Log final product structure
    print(f"\n=== FINAL PRODUCT STRUCTURE ===")
    print(f"Product has 'title': {'title' in shopify_product}")
    if 'title' in shopify_product:
        print(f"  title value: '{shopify_product['title'][:100]}...'")
    print(f"Product has 'variants': {'variants' in shopify_product}")
    if 'variants' in shopify_product:
        print(f"  Number of variants: {len(shopify_product['variants'])}")
        if len(shopify_product['variants']) > 0:
            variant = shopify_product['variants'][0]
            print(f"  Variant has 'price': {'price' in variant}")
            if 'price' in variant:
                print(f"    price value: {variant['price']}")
            print(f"  Variant fields: {list(variant.keys())}")
    print(f"Product fields: {list(shopify_product.keys())}")
    print("=" * 40 + "\n")

    return shopify_product


@router.get("/validate")
async def validate_mapping(mapping: List[FieldMapping] = Body(...)):
    """
    Validate a mapping configuration
    """
    try:
        sw5_client = Shopware5Client()
        shopify_client = ShopifyClient()

        # Get available fields
        sw5_fields = sw5_client.get_article_fields()
        shopify_fields = shopify_client.get_shopify_product_fields()

        sw5_field_paths = [f['path'] for f in sw5_fields]
        shopify_field_paths = [f['path'] for f in shopify_fields]

        validation_results = []

        for m in mapping:
            result = {
                "sw5_field": m.sw5_field,
                "shopify_field": m.shopify_field,
                "valid": True,
                "warnings": []
            }

            # Check if SW5 field exists
            if m.sw5_field not in sw5_field_paths:
                result["warnings"].append(f"SW5 field '{m.sw5_field}' not found in sample data")

            # Check if Shopify field exists
            if m.shopify_field not in shopify_field_paths:
                result["warnings"].append(f"Shopify field '{m.shopify_field}' not found in schema")

            if result["warnings"]:
                result["valid"] = False

            validation_results.append(result)

        return {
            "valid": all(r["valid"] for r in validation_results),
            "results": validation_results
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
