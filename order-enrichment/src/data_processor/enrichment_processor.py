"""Data processor for order enrichment with landing page resolution and source attribution."""

import base64
import json
import logging
import re
from typing import Dict, List, Any, Optional, Tuple
from urllib.parse import urlsplit, parse_qs, unquote

logger = logging.getLogger(__name__)


class EnrichmentProcessor:
    """Processes order data to resolve landing pages and extract attribution sources."""

    def __init__(self):
        """Initialize the enrichment processor."""
        self.source_patterns = self._initialize_source_patterns()

    def _initialize_source_patterns(self) -> Dict[str, List[str]]:
        """
        Initialize source detection patterns.

        Returns:
            Dictionary mapping source names to their detection patterns
        """
        return {
            'Klaviyo': ['klaviyo', '_kx='],
            'Meta': ['facebook', 'meta', 'instagram', 'fbclid=', 'utm_source=fb', 'utm_source=ig'],
            'Google': ['utm_source=google', 'gclid=', 'gad_source=', 'gbraid=', 'srsltid='],
            'Snapchat': ['snapchat', 'snapcid=', 'snap_campaign_id=', 'sccid='],
            'Bing': ['syclid='],
            'Klarna': ['utm_source=klarna'],
            'Pinterest': ['pinterest', 'pins_campaign_id=', 'epik='],
            'TikTok': ['source=tiktok', 'ttclid='],
            'Shop Pay': ['shop_pay']
        }

    def _b64url_decode(self, seg: str) -> bytes:
        """
        Decode base64url encoded string.

        Args:
            seg: Base64url encoded string

        Returns:
            Decoded bytes
        """
        seg = (seg or "").strip().replace(" ", "")
        seg += "=" * ((4 - len(seg) % 4) % 4)
        try:
            return base64.urlsafe_b64decode(seg)
        except Exception as e:
            logger.warning(f"Failed to decode base64url string: {str(e)}")
            return b""

    def _decode_jwt_payload(self, jwt_token: str) -> Optional[Dict]:
        """
        Decode JWT token payload.

        Args:
            jwt_token: JWT token string

        Returns:
            Decoded payload dictionary or None if decode fails
        """
        try:
            parts = (jwt_token or "").strip().split(".")
            if len(parts) != 3:
                return None
            
            payload_bytes = self._b64url_decode(parts[1])
            if not payload_bytes:
                return None
                
            return json.loads(payload_bytes.decode("utf-8"))
        except Exception as e:
            logger.warning(f"Failed to decode JWT payload: {str(e)}")
            return None

    def extract_jwt_landing_page(self, url_or_path: str) -> Optional[str]:
        """
        Extract landing page from JWT token in URL parameters.

        Args:
            url_or_path: URL or path that may contain JWT token

        Returns:
            Decoded landing page URL or None if not found
        """
        if not url_or_path:
            return None

        try:
            # Handle relative paths
            if url_or_path.startswith("/"):
                full_url = "https://dummy" + url_or_path
            else:
                full_url = url_or_path

            # Parse query parameters
            parsed = urlsplit(full_url)
            query_params = parse_qs(parsed.query, keep_blank_values=True)
            
            token = query_params.get("token", [None])[0]
            if not token:
                return None

            # Decode JWT payload
            payload = self._decode_jwt_payload(token)
            if payload and isinstance(payload, dict):
                landing_page = payload.get("landing_page")
                if landing_page:
                    return unquote(landing_page)
        except Exception as e:
            logger.warning(f"Error extracting JWT landing page from {url_or_path}: {str(e)}")

        return None

    def resolve_landing_page(self, url_or_path: str) -> Tuple[str, bool]:
        """
        Resolve landing page URL and determine if it was JWT decoded.

        Args:
            url_or_path: Original landing page URL or path

        Returns:
            Tuple of (resolved_url, was_jwt_decoded)
        """
        if not url_or_path:
            return "", False

        jwt_decoded_url = self.extract_jwt_landing_page(url_or_path)
        if jwt_decoded_url:
            return jwt_decoded_url, True
        
        return url_or_path, False

    def detect_all_sources(self, url: str) -> List[str]:
        """
        Detect all attribution sources present in a URL.

        Args:
            url: URL to analyze for source patterns

        Returns:
            List of detected sources, sorted alphabetically
        """
        if not url:
            return ['Unknown']

        url_lower = url.lower()
        detected_sources = []

        for source_name, patterns in self.source_patterns.items():
            if any(pattern in url_lower for pattern in patterns):
                detected_sources.append(source_name)

        return sorted(set(detected_sources)) if detected_sources else ['Unknown']

    def extract_utm_param(self, url: str, param: str) -> str:
        """
        Extract UTM parameter from URL.

        Args:
            url: URL to extract parameter from
            param: Parameter name (e.g., 'utm_campaign')

        Returns:
            Parameter value or empty string if not found
        """
        if not url:
            return ""

        try:
            pattern = rf"[?&]{re.escape(param)}=([^&#]*)"
            match = re.search(pattern, url, re.IGNORECASE)
            if match:
                return unquote(match.group(1))
        except Exception as e:
            logger.warning(f"Error extracting {param} from {url}: {str(e)}")

        return ""

    def extract_all_utm_params(self, url: str) -> Dict[str, str]:
        """
        Extract all UTM and campaign parameters from URL.

        Args:
            url: URL to extract parameters from

        Returns:
            Dictionary of parameter names to values
        """
        utm_params = {
            'utm_medium': self.extract_utm_param(url, 'utm_medium'),
            'utm_campaign': self.extract_utm_param(url, 'utm_campaign'),
            'utm_content': self.extract_utm_param(url, 'utm_content'),
            'utm_term': self.extract_utm_param(url, 'utm_term'),
            'utm_id': self.extract_utm_param(url, 'utm_id'),
            'campaign_id': self.extract_utm_param(url, 'campaign_id'),
            'ad_id': self.extract_utm_param(url, 'ad_id')
        }

        return utm_params

    def process_order(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single order to enrich it with attribution data.

        Args:
            order: Order dictionary from Neo4j

        Returns:
            Enriched order dictionary
        """
        try:
            original_landing_page = order.get('landingPage', '') or ''
            
            # Resolve landing page
            resolved_landing_page, decoded_from_jwt = self.resolve_landing_page(original_landing_page)
            
            # Detect sources
            all_sources = self.detect_all_sources(resolved_landing_page)
            attribution_source = all_sources[-1] if all_sources else 'Unknown'  # Take last (highest priority)
            all_sources_str = " + ".join(all_sources)
            
            # Extract UTM parameters
            utm_params = self.extract_all_utm_params(resolved_landing_page)
            
            # Build enriched order
            enriched_order = {
                'neo4j_order_id': order.get('id'),
                'external_order_id': order.get('externalOrderId'),
                'created_date': order.get('createdDate'),
                'order_amount': order.get('orderAmount'),
                'original_landing_page': original_landing_page,
                'resolved_landing_page': resolved_landing_page,
                'decoded_from_jwt': decoded_from_jwt,
                'attribution_source': attribution_source,
                'all_sources': all_sources_str,
                **utm_params
            }

            logger.debug(f"Processed order {order.get('id')} with attribution: {attribution_source}")
            return enriched_order

        except Exception as e:
            logger.error(f"Error processing order {order.get('id', 'unknown')}: {str(e)}")
            # Return minimal enrichment on error
            return {
                'neo4j_order_id': order.get('id'),
                'external_order_id': order.get('externalOrderId'),
                'created_date': order.get('createdDate'),
                'order_amount': order.get('orderAmount'),
                'original_landing_page': order.get('landingPage', ''),
                'resolved_landing_page': order.get('landingPage', ''),
                'decoded_from_jwt': False,
                'attribution_source': 'Unknown',
                'all_sources': 'Unknown',
                'utm_medium': '',
                'utm_campaign': '',
                'utm_content': '',
                'utm_term': '',
                'utm_id': '',
                'campaign_id': '',
                'ad_id': ''
            }

    def process_orders_batch(self, orders: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process a batch of orders for enrichment.

        Args:
            orders: List of order dictionaries from Neo4j

        Returns:
            List of enriched order dictionaries
        """
        enriched_orders = []
        
        for order in orders:
            try:
                enriched_order = self.process_order(order)
                enriched_orders.append(enriched_order)
            except Exception as e:
                logger.error(f"Failed to process order in batch: {str(e)}")
                # Continue with other orders even if one fails
                continue

        logger.info(f"Processed {len(enriched_orders)} out of {len(orders)} orders in batch")
        return enriched_orders