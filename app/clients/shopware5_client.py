import requests
from typing import Dict, List, Optional, Any
from requests.auth import HTTPDigestAuth
from config import settings


class Shopware5Client:
    def __init__(self):
        self.base_url = settings.sw5_api_url.rstrip('/')
        self.auth = HTTPDigestAuth(settings.sw5_api_username, settings.sw5_api_key)
        self.session = requests.Session()
        self.session.auth = self.auth

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """Make HTTP request to Shopware 5 API"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Shopware 5 API Error: {str(e)}")

    def get_articles(self, limit: int = 100, offset: int = 0) -> Dict:
        """
        Get articles from Shopware 5
        """
        params = {
            'limit': limit,
            'start': offset
        }
        return self._make_request('GET', 'articles', params=params)

    def get_article(self, article_id: int) -> Dict:
        """
        Get single article by ID
        """
        result = self._make_request('GET', f'articles/{article_id}')

        # Unwrap the 'data' key (SW5 API returns {"data": {...}})
        if result.get('data'):
            return result['data']

        # If no data, the article doesn't exist
        raise Exception(f"Article with ID {article_id} not found in Shopware 5")

    def get_article_by_number(self, order_number: str) -> Dict:
        """
        Get article by order number using useNumberAsId parameter
        """
        try:
            # Use the direct API method with useNumberAsId=true
            # This is much faster than filtering
            params = {'useNumberAsId': 'true'}
            result = self._make_request('GET', f'articles/{order_number}', params=params)

            if result.get('data'):
                return result['data']

            raise Exception(f"Article with number '{order_number}' not found in Shopware 5")
        except Exception as e:
            if "not found" in str(e).lower() or "404" in str(e):
                raise Exception(f"Article with number '{order_number}' not found in Shopware 5")
            raise Exception(f"Error finding article {order_number}: {str(e)}")

    def get_article_fields(self) -> List[Dict[str, Any]]:
        """
        Get all available article fields from Shopware 5
        This returns a schema of available fields by analyzing multiple articles
        """
        # Get multiple articles to extract all possible fields
        articles = self.get_articles(limit=20)

        if not articles.get('data') or len(articles['data']) == 0:
            return []

        # Collect all unique field paths from all articles
        all_field_paths = {}

        for article in articles['data']:
            fields = self._extract_fields_from_object(article, prefix="")
            for field in fields:
                # Use path as key to avoid duplicates, keep first occurrence with sample
                if field['path'] not in all_field_paths:
                    all_field_paths[field['path']] = field

        return list(all_field_paths.values())

    def _extract_fields_from_object(self, obj: Any, prefix: str = "") -> List[Dict[str, Any]]:
        """
        Recursively extract fields from a nested object
        """
        fields = []

        if isinstance(obj, dict):
            for key, value in obj.items():
                field_path = f"{prefix}.{key}" if prefix else key
                field_type = type(value).__name__

                # Special handling for propertyValues - extract all values
                if key == "propertyValues" and isinstance(value, list) and len(value) > 0:
                    # Create a combined field with all property values
                    all_values = [item.get('value', '') for item in value if isinstance(item, dict) and 'value' in item]
                    combined_value = " | ".join(all_values)

                    fields.append({
                        "path": "propertyValues.value",
                        "type": "string",
                        "sample_value": combined_value[:100] if combined_value else None,
                        "description": f"Property values (combined from {len(all_values)} items)"
                    })

                    # Also add individual fields from first item for reference
                    if isinstance(value[0], dict):
                        fields.extend(self._extract_fields_from_object(value[0], f"{field_path}[0]"))
                else:
                    # Add the field
                    fields.append({
                        "path": field_path,
                        "type": field_type,
                        "sample_value": str(value)[:100] if value is not None else None
                    })

                    # Recurse into nested objects (but limit depth)
                    if isinstance(value, dict) and prefix.count('.') < 2:
                        fields.extend(self._extract_fields_from_object(value, field_path))
                    elif isinstance(value, list) and len(value) > 0 and prefix.count('.') < 2 and key != "propertyValues":
                        # Sample first item in array (skip propertyValues as it's handled above)
                        fields.extend(self._extract_fields_from_object(value[0], f"{field_path}[0]"))

        return fields

    def get_pickware_fields(self, article_id: int) -> Optional[Dict]:
        """
        Get Pickware specific fields for an article
        Note: This depends on how Pickware stores its data in SW5
        Pickware typically uses the 'attribute' object in articles
        """
        article = self.get_article(article_id)

        # Pickware fields are typically stored in attributes
        if 'attribute' in article and article['attribute']:
            # Filter for Pickware-specific attributes
            pickware_fields = {}
            for key, value in article['attribute'].items():
                if 'pickware' in key.lower() or key.startswith('attr'):
                    pickware_fields[key] = value

            return pickware_fields if pickware_fields else None

        return None

    # ==================== CUSTOMER METHODS ====================

    def get_customers(self, limit: int = 100, offset: int = 0) -> Dict:
        """
        Get customers from Shopware 5
        """
        params = {
            'limit': limit,
            'start': offset
        }
        return self._make_request('GET', 'customers', params=params)

    def get_customer(self, customer_id: int) -> Dict:
        """
        Get single customer by ID
        """
        result = self._make_request('GET', f'customers/{customer_id}')

        if result.get('data'):
            return result['data']

        raise Exception(f"Customer with ID {customer_id} not found in Shopware 5")

    def get_customer_by_email(self, email: str) -> Optional[Dict]:
        """
        Get customer by email address
        Note: SW5 API doesn't support direct email lookup, so we fetch and filter
        """
        try:
            # Fetch customers and search for matching email
            customers = self.get_customers(limit=100)

            if customers.get('data'):
                for customer in customers['data']:
                    if customer.get('email', '').lower() == email.lower():
                        return customer

            return None
        except Exception as e:
            raise Exception(f"Error searching for customer by email: {str(e)}")

    def get_customer_fields(self) -> List[Dict[str, Any]]:
        """
        Get all available customer fields from Shopware 5
        """
        customers = self.get_customers(limit=10)

        if not customers.get('data') or len(customers['data']) == 0:
            return []

        all_field_paths = {}
        for customer in customers['data']:
            fields = self._extract_fields_from_object(customer, prefix="")
            for field in fields:
                if field['path'] not in all_field_paths:
                    all_field_paths[field['path']] = field

        return list(all_field_paths.values())

    # ==================== ORDER METHODS ====================

    def get_orders(self, limit: int = 100, offset: int = 0, status: str = None) -> Dict:
        """
        Get orders from Shopware 5
        """
        params = {
            'limit': limit,
            'start': offset
        }
        if status:
            params['filter'] = [{'property': 'status', 'value': status}]

        return self._make_request('GET', 'orders', params=params)

    def get_order(self, order_id: int) -> Dict:
        """
        Get single order by ID
        """
        result = self._make_request('GET', f'orders/{order_id}')

        if result.get('data'):
            return result['data']

        raise Exception(f"Order with ID {order_id} not found in Shopware 5")

    def get_order_by_number(self, order_number: str) -> Optional[Dict]:
        """
        Get order by order number
        """
        try:
            # SW5 API doesn't support useNumberAsId for orders
            # We need to fetch and filter
            orders = self.get_orders(limit=100)

            if orders.get('data'):
                for order in orders['data']:
                    if order.get('number') == order_number:
                        return order

            return None
        except Exception as e:
            raise Exception(f"Error finding order by number: {str(e)}")

    def get_order_fields(self) -> List[Dict[str, Any]]:
        """
        Get all available order fields from Shopware 5
        """
        orders = self.get_orders(limit=10)

        if not orders.get('data') or len(orders['data']) == 0:
            return []

        all_field_paths = {}
        for order in orders['data']:
            fields = self._extract_fields_from_object(order, prefix="")
            for field in fields:
                if field['path'] not in all_field_paths:
                    all_field_paths[field['path']] = field

        return list(all_field_paths.values())

    # ==================== CONNECTION TEST ====================

    def test_connection(self) -> Dict:
        """
        Test connection to Shopware 5 API
        """
        try:
            response = self._make_request('GET', 'version')
            return {
                "success": True,
                "version": response.get('version', 'unknown'),
                "revision": response.get('revision', 'unknown')
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
