import requests
from typing import Dict, List, Optional, Any
from config import settings


class ShopifyClient:
    def __init__(self):
        self.shop_url = settings.shopify_shop_url.rstrip('/')
        self.access_token = settings.shopify_access_token
        self.api_version = settings.shopify_api_version
        self.base_url = f"https://{self.shop_url}/admin/api/{self.api_version}"

        self.headers = {
            "X-Shopify-Access-Token": self.access_token,
            "Content-Type": "application/json"
        }

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """Make HTTP request to Shopify API"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}.json"

        if 'headers' in kwargs:
            kwargs['headers'].update(self.headers)
        else:
            kwargs['headers'] = self.headers

        try:
            response = requests.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            error_msg = f"Shopify API Error: {str(e)}"
            if hasattr(e.response, 'text'):
                error_msg += f" - {e.response.text}"
            raise Exception(error_msg)

    def get_products(self, limit: int = 50, page_info: Optional[str] = None) -> Dict:
        """
        Get products from Shopify
        """
        params = {'limit': limit}
        if page_info:
            params['page_info'] = page_info

        return self._make_request('GET', 'products', params=params)

    def get_product(self, product_id: int) -> Dict:
        """
        Get single product by ID
        """
        return self._make_request('GET', f'products/{product_id}')

    def create_product(self, product_data: Dict) -> Dict:
        """
        Create a new product in Shopify
        """
        return self._make_request('POST', 'products', json={"product": product_data})

    def update_product(self, product_id: int, product_data: Dict) -> Dict:
        """
        Update an existing product in Shopify
        """
        return self._make_request('PUT', f'products/{product_id}', json={"product": product_data})

    def _make_graphql_request(self, query: str, variables: Optional[Dict] = None) -> Dict:
        """Make GraphQL request to Shopify API"""
        url = f"{self.base_url.rsplit('/admin/api/', 1)[0]}/admin/api/{self.api_version}/graphql.json"

        payload = {
            "query": query
        }
        if variables:
            payload["variables"] = variables

        try:
            response = requests.post(url, json=payload, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            error_msg = f"Shopify GraphQL API Error: {str(e)}"
            if hasattr(e.response, 'text'):
                error_msg += f" - {e.response.text}"
            raise Exception(error_msg)

    def get_metafield_definitions(self, product_identifier: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get custom metafields using GraphQL API with actual values from products
        """
        try:
            # First, get metafield definitions (schema)
            query = """
            {
              metafieldDefinitions(first: 100, ownerType: PRODUCT) {
                edges {
                  node {
                    id
                    name
                    namespace
                    key
                    description
                    type {
                      name
                    }
                    ownerType
                  }
                }
              }
            }
            """

            result = self._make_graphql_request(query)

            if 'errors' in result:
                print(f"GraphQL errors: {result['errors']}")
                return self._get_metafields_from_products()

            metafields_map = {}
            edges = result.get('data', {}).get('metafieldDefinitions', {}).get('edges', [])

            for edge in edges:
                node = edge.get('node', {})
                namespace = node.get('namespace')
                key = node.get('key')

                if namespace and key:
                    field_key = f"{namespace}.{key}"
                    metafields_map[field_key] = {
                        "namespace": namespace,
                        "key": key,
                        "name": node.get('name', f"{namespace}.{key}"),
                        "type": node.get('type', {}).get('name', 'string'),
                        "description": node.get('description', 'Custom metafield'),
                        "owner_type": node.get('ownerType', 'PRODUCT')
                    }

            print(f"Found {len(metafields_map)} metafield definitions via GraphQL")

            # Now enrich with actual values from products
            metafields_with_values = self._enrich_metafields_with_values(
                list(metafields_map.values()),
                product_identifier=product_identifier
            )
            return metafields_with_values

        except Exception as e:
            print(f"Error fetching metafields via GraphQL: {e}")
            # Fallback: Try to get metafields from products directly
            return self._get_metafields_from_products()

    def _enrich_metafields_with_values(
        self,
        metafield_defs: List[Dict[str, Any]],
        product_identifier: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Enrich metafield definitions with actual values from products

        If product_identifier is provided, use that specific product for enrichment.
        Otherwise, check first 10 products for sample values.
        """
        try:
            # If specific product is requested, use it for enrichment
            if product_identifier:
                try:
                    product = self.get_product_by_identifier(product_identifier)
                    if product:
                        products = [product]
                        print(f"Using specified product {product_identifier} for metafield enrichment")
                    else:
                        # Fall back to default if product not found
                        products_response = self.get_products(limit=10)
                        products = products_response.get('products', [])
                except Exception:
                    # Fall back to default on error
                    products_response = self.get_products(limit=10)
                    products = products_response.get('products', [])
            else:
                # Only check first 10 products for sample values (fast performance)
                products_response = self.get_products(limit=10)
                products = products_response.get('products', [])

            if not products:
                return metafield_defs

            # Create a map of namespace.key -> sample values
            sample_values = {}

            for product in products:
                product_rest_id = product.get('id')
                if not product_rest_id:
                    continue

                # Convert REST API ID to GraphQL Global ID
                product_gid = f"gid://shopify/Product/{product_rest_id}"

                query = """
                query ProductMetafields($ownerId: ID!) {
                  product(id: $ownerId) {
                    metafields(first: 100) {
                      edges {
                        node {
                          namespace
                          key
                          value
                        }
                      }
                    }
                  }
                }
                """

                try:
                    result = self._make_graphql_request(query, variables={"ownerId": product_gid})

                    if 'errors' in result:
                        continue

                    product_node = result.get('data', {}).get('product', {})
                    if not product_node:
                        continue

                    metafield_edges = product_node.get('metafields', {}).get('edges', [])

                    for metafield_edge in metafield_edges:
                        metafield = metafield_edge.get('node', {})
                        namespace = metafield.get('namespace')
                        key = metafield.get('key')
                        value = metafield.get('value')

                        if namespace and key and value:
                            field_key = f"{namespace}.{key}"
                            # Only store first non-empty value found
                            if field_key not in sample_values:
                                sample_values[field_key] = str(value)[:100]

                except Exception:
                    continue

            # Enrich definitions with sample values
            enriched_count = 0
            for metafield_def in metafield_defs:
                namespace = metafield_def.get('namespace')
                key = metafield_def.get('key')
                field_key = f"{namespace}.{key}"

                if field_key in sample_values:
                    sample_value = sample_values[field_key]
                    # Update description to include example
                    current_desc = metafield_def.get('description', 'Custom metafield')
                    metafield_def['description'] = f"{current_desc} (Example: {sample_value}...)"
                    enriched_count += 1

            if enriched_count > 0:
                print(f"Enriched {enriched_count} of {len(metafield_defs)} metafields with sample values")
            return metafield_defs

        except Exception as e:
            print(f"Error enriching metafields with values: {e}")
            import traceback
            traceback.print_exc()
            return metafield_defs

    def _get_metafields_from_products(self) -> List[Dict[str, Any]]:
        """
        Fallback: Get metafields by loading products with their metafields
        """
        try:
            # First, get product IDs using REST API
            products_response = self.get_products(limit=50)
            products = products_response.get('products', [])

            if not products:
                print("No products found to extract metafields from")
                return []

            metafields_map = {}

            # For each product, query its metafields via GraphQL
            for product in products[:20]:  # Limit to first 20 products
                product_rest_id = product.get('id')
                if not product_rest_id:
                    continue

                # Convert REST API ID to GraphQL Global ID
                product_gid = f"gid://shopify/Product/{product_rest_id}"

                query = """
                query ProductMetafields($ownerId: ID!) {
                  product(id: $ownerId) {
                    metafields(first: 100) {
                      edges {
                        node {
                          namespace
                          key
                          type
                          value
                        }
                      }
                    }
                  }
                }
                """

                try:
                    result = self._make_graphql_request(query, variables={"ownerId": product_gid})

                    if 'errors' in result:
                        continue

                    product_node = result.get('data', {}).get('product', {})
                    if not product_node:
                        continue

                    metafield_edges = product_node.get('metafields', {}).get('edges', [])

                    for metafield_edge in metafield_edges:
                        metafield = metafield_edge.get('node', {})
                        namespace = metafield.get('namespace')
                        key = metafield.get('key')

                        if namespace and key:
                            field_key = f"{namespace}.{key}"
                            if field_key not in metafields_map:
                                # Infer a better type name from the value
                                value = metafield.get('value', '')
                                metafield_type = metafield.get('type', 'single_line_text_field')

                                metafields_map[field_key] = {
                                    "namespace": namespace,
                                    "key": key,
                                    "name": f"{namespace}.{key}",
                                    "type": metafield_type,
                                    "description": f"Custom metafield (Example: {str(value)[:50]}...)" if value else "Custom metafield",
                                    "owner_type": "PRODUCT"
                                }
                except Exception as e:
                    # Skip this product if there's an error
                    continue

            print(f"Found {len(metafields_map)} unique metafields from {len(products)} products")
            return list(metafields_map.values())

        except Exception as e:
            print(f"Error in fallback metafield fetch: {e}")
            return []

    def get_product_by_identifier(self, identifier: str) -> Optional[Dict]:
        """
        Get a product by SKU or Product ID
        """
        try:
            # First, try as product ID (numeric)
            if identifier.isdigit():
                try:
                    result = self.get_product(int(identifier))
                    return result.get('product')
                except:
                    pass

            # If not numeric or failed, try to find by SKU
            return self.find_product_by_sku(identifier)

        except Exception as e:
            raise Exception(f"Product with identifier '{identifier}' not found in Shopify: {str(e)}")

    def _extract_fields_from_products(self, product_identifier: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Extract all fields from real Shopify products with sample values
        Similar to Shopware's approach - analyze real product data

        If product_identifier is provided, extract fields from that specific product only
        Otherwise, extract from multiple products
        """
        try:
            if product_identifier:
                # Get specific product
                product = self.get_product_by_identifier(product_identifier)
                if not product:
                    raise Exception(f"Product with identifier '{product_identifier}' not found")

                products = [product]
                print(f"Extracting fields from product: {product.get('title', 'Unknown')} (ID: {product.get('id')})")
            else:
                # Get multiple products to extract field values
                products_response = self.get_products(limit=20)
                products = products_response.get('products', [])

                if not products:
                    print("No products found to extract fields from")
                    return []

            # Collect all unique field paths with sample values
            all_field_paths = {}

            for product in products:
                # Extract product-level fields
                fields = self._extract_fields_from_object(product, prefix="")
                for field in fields:
                    # Use path as key to avoid duplicates, keep first occurrence with sample
                    if field['path'] not in all_field_paths:
                        all_field_paths[field['path']] = field

            print(f"Extracted {len(all_field_paths)} unique fields from {len(products)} product(s)")
            return list(all_field_paths.values())

        except Exception as e:
            print(f"Error extracting fields from products: {e}")
            raise

    def _extract_fields_from_object(self, obj: Any, prefix: str = "") -> List[Dict[str, Any]]:
        """
        Recursively extract fields from a nested object (similar to Shopware client)
        """
        fields = []

        if isinstance(obj, dict):
            for key, value in obj.items():
                field_path = f"{prefix}.{key}" if prefix else key
                field_type = type(value).__name__

                # Add the field
                fields.append({
                    "path": field_path,
                    "type": field_type,
                    "sample_value": str(value)[:100] if value is not None else None,
                    "required": field_path in ['title', 'variants[].price'],  # Mark known required fields
                    "description": self._get_field_description(field_path)
                })

                # Recurse into nested objects (but limit depth)
                if isinstance(value, dict) and prefix.count('.') < 2:
                    fields.extend(self._extract_fields_from_object(value, field_path))
                elif isinstance(value, list) and len(value) > 0 and prefix.count('.') < 2:
                    # For arrays, use [] notation and sample first item
                    array_path = f"{field_path}[]"
                    if isinstance(value[0], dict):
                        # For array of objects (like variants), extract fields from first item
                        fields.extend(self._extract_fields_from_object(value[0], array_path))

        return fields

    def _get_field_description(self, field_path: str) -> str:
        """
        Get a description for a field based on its path
        """
        descriptions = {
            "title": "Product title",
            "body_html": "Product description (HTML)",
            "vendor": "Product vendor/manufacturer",
            "product_type": "Product type/category",
            "tags": "Comma-separated tags",
            "status": "Product status: active, draft, archived",
            "variants[].sku": "Stock Keeping Unit",
            "variants[].price": "Product price",
            "variants[].compare_at_price": "Compare at price (original price)",
            "variants[].barcode": "Product barcode",
            "variants[].weight": "Product weight",
            "variants[].weight_unit": "Weight unit",
            "variants[].inventory_quantity": "Inventory quantity",
            "variants[].inventory_management": "Inventory management",
            "variants[].inventory_policy": "Inventory policy",
            "variants[].taxable": "Whether product is taxable",
            "variants[].requires_shipping": "Whether product requires shipping",
            "variants[].harmonized_system_code": "HS Code / Zolltarifnummer",
            "variants[].country_code_of_origin": "Country code of origin (ISO 3166-1 alpha-2)",
            "images[].src": "Image URL",
            "images[].alt": "Image alt text",
            "options[].name": "Option name (e.g., Size, Color)",
            "options[].values": "Option values",
        }
        return descriptions.get(field_path, "")

    def get_shopify_product_fields(self, product_identifier: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all available Shopify product fields including custom metafields
        Extracted from real products with actual sample values

        Args:
            product_identifier: Optional product ID or SKU to extract fields from specific product
        """
        try:
            # Extract fields from real products
            fields = self._extract_fields_from_products(product_identifier)

            # Add custom metafields from store (enriched with values from specified product if available)
            metafield_defs = self.get_metafield_definitions(product_identifier=product_identifier)
            for metafield in metafield_defs:
                if metafield.get('owner_type') in ['PRODUCT', 'PRODUCTVARIANT']:
                    field_path = f"metafields[].{metafield['namespace']}.{metafield['key']}"

                    # Extract sample value from description if available
                    sample_value = None
                    description = metafield.get('description', 'Custom metafield')
                    if 'Example: ' in description:
                        sample_value = description.split('Example: ')[1].rstrip(')')

                    field_data = {
                        "path": field_path,
                        "type": metafield.get('type', 'string'),
                        "required": False,
                        "description": f"{metafield.get('name', '')} - {description}"
                    }

                    if sample_value:
                        field_data["sample_value"] = sample_value

                    fields.append(field_data)

            return fields

        except Exception as e:
            print(f"Error getting Shopify product fields: {e}")
            raise

    def test_connection(self) -> Dict:
        """
        Test connection to Shopify API
        """
        try:
            response = self._make_request('GET', 'shop')
            shop_data = response.get('shop', {})
            return {
                "success": True,
                "shop_name": shop_data.get('name', 'unknown'),
                "shop_domain": shop_data.get('domain', 'unknown'),
                "email": shop_data.get('email', 'unknown')
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def find_product_by_sku(self, sku: str) -> Optional[Dict]:
        """
        Find a product by SKU using GraphQL (efficient for large catalogs)
        """
        try:
            # Use GraphQL to search by SKU directly
            query = """
            query($sku: String!) {
                productVariants(first: 1, query: $sku) {
                    edges {
                        node {
                            id
                            sku
                            product {
                                id
                                legacyResourceId
                            }
                        }
                    }
                }
            }
            """

            variables = {
                "sku": f"sku:{sku}"
            }

            result = self._make_graphql_request(query, variables)

            edges = result.get('data', {}).get('productVariants', {}).get('edges', [])

            if edges and len(edges) > 0:
                node = edges[0]['node']
                product_id = node['product']['legacyResourceId']

                # Return product in format compatible with rest of code
                return {
                    'id': int(product_id)
                }

            return None

        except Exception as e:
            print(f"Error finding product by SKU {sku}: {e}")
            return None
