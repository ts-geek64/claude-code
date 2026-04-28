"""HTTP client for Shopify GraphQL API with retry logic."""

import logging
import time
from typing import Any, Dict, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config.settings import settings


logger = logging.getLogger(__name__)


class ShopifyHTTPClient:
    """HTTP client with retry and rate-limit handling."""

    def __init__(self, shop_domain: str, access_token: str):
        """
        Initialize HTTP client for a Shopify store.

        Args:
            shop_domain: Shopify myshopify.com domain
            access_token: Decrypted access token
        """
        self.shop_domain = shop_domain
        self.access_token = access_token
        self.base_url = f"https://{shop_domain}/admin/api/{settings.SHOPIFY_API_VERSION}/graphql.json"
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        """
        Create requests session with retry strategy.

        Returns:
            Configured session
        """
        session = requests.Session()

        # Configure retry strategy for network errors only
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["POST"],
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)

        # Set default headers
        session.headers.update(
            {
                "Content-Type": "application/json",
                "X-Shopify-Access-Token": self.access_token,
            }
        )

        return session

    def execute_query(
        self, query: str, variables: Optional[Dict[str, Any]] = None
    ) -> Dict:
        """
        Execute GraphQL query with exponential backoff for rate limits.

        Args:
            query: GraphQL query string
            variables: Query variables

        Returns:
            Response data dictionary

        Raises:
            Exception: If request fails after retries
        """
        payload = {"query": query}
        if variables:
            payload["variables"] = variables

        attempt = 0
        backoff = settings.INITIAL_BACKOFF

        while attempt < settings.MAX_RETRIES:
            try:
                response = self.session.post(
                    self.base_url,
                    json=payload,
                    timeout=settings.SHOPIFY_REQUEST_TIMEOUT,
                )

                # Handle rate limiting
                if response.status_code == 429:
                    attempt += 1
                    if attempt >= settings.MAX_RETRIES:
                        raise Exception(
                            f"Rate limit exceeded after {settings.MAX_RETRIES} retries"
                        )

                    logger.warning(
                        f"Rate limited. Retrying in {backoff}s (attempt {attempt})"
                    )
                    time.sleep(backoff)
                    backoff = min(backoff * 2, settings.MAX_BACKOFF)
                    continue

                # Raise for other HTTP errors
                response.raise_for_status()

                data = response.json()

                # Check for GraphQL errors
                if "errors" in data:
                    error_messages = [
                        err.get("message", "Unknown error") for err in data["errors"]
                    ]
                    raise Exception(f"GraphQL errors: {', '.join(error_messages)}")

                return data

            except requests.exceptions.Timeout:
                attempt += 1
                if attempt >= settings.MAX_RETRIES:
                    raise Exception(
                        f"Request timeout after {settings.MAX_RETRIES} retries"
                    )

                logger.warning(
                    f"Request timeout. Retrying in {backoff}s (attempt {attempt})"
                )
                time.sleep(backoff)
                backoff = min(backoff * 2, settings.MAX_BACKOFF)

            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed: {str(e)}")
                raise

        raise Exception(f"Failed after {settings.MAX_RETRIES} attempts")

    def health_check(self) -> bool:
        """
        Perform lightweight health check query.

        Returns:
            True if API is accessible, False otherwise
        """
        query = """
            {
                shop {
                    id
                    name
                    myshopifyDomain
                }
            }
        """

        try:
            response = self.execute_query(query)
            shop_data = response.get("data", {}).get("shop")

            if shop_data:
                logger.info(f"Health check passed for {shop_data.get('name')}")
                return True

            return False

        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return False

    def close(self) -> None:
        """Close HTTP session."""
        if self.session:
            self.session.close()
