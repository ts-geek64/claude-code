"""Data processor for normalizing Shopify GraphQL responses."""

import json
import logging
import base64
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse, parse_qs, unquote


logger = logging.getLogger(__name__)


class DataProcessor:
    """Process and normalize Shopify GraphQL data."""

    @staticmethod
    def parse_timestamp(timestamp: Optional[str]) -> Optional[datetime]:
        """Parse ISO 8601 timestamp string into UTC datetime."""
        if not timestamp:
            return None
        try:
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            return dt.astimezone(timezone.utc)
        except Exception as e:
            logger.warning(f"Failed to parse timestamp '{timestamp}': {str(e)}")
            return None

    @staticmethod
    def map_financial_status(status: Optional[str]) -> Optional[str]:
        """Map Shopify financial status to database enum."""
        if not status:
            return None
        status_map = {
            "PENDING": "pending",
            "AUTHORIZED": "authorized",
            "PARTIALLY_PAID": "partially_paid",
            "PAID": "paid",
            "PARTIALLY_REFUNDED": "partially_refunded",
            "REFUNDED": "refunded",
            "VOIDED": "voided",
        }
        return status_map.get(status.upper(), "pending")

    @staticmethod
    def map_fulfillment_status(status: Optional[str]) -> Optional[str]:
        """Map Shopify fulfillment status to database enum."""
        if not status:
            return "null"
        status_map = {
            "FULFILLED": "fulfilled",
            "PARTIAL": "partial",
            "RESTOCKED": "restocked",
            "UNFULFILLED": "unfulfilled",
            "NULL": "null",
        }
        return status_map.get(status.upper(), "null")

    @staticmethod
    def map_rfm_group(rfm: Optional[str]) -> str:
        """Map Shopify RFM group to database enum."""
        if not rfm:
            return "NEW"
        valid_groups = {
            "ACTIVE",
            "ALMOST_LOST",
            "AT_RISK",
            "CHAMPIONS",
            "DORMANT",
            "LOYAL",
            "NEEDS_ATTENTION",
            "NEW",
            "PREVIOUSLY_LOYAL",
            "PROMISING",
            "PROSPECTS",
        }
        rfm_upper = rfm.upper()
        return rfm_upper if rfm_upper in valid_groups else "NEW"

    @staticmethod
    def _b64url_decode(segment: str) -> bytes:
        """Safely base64url-decode a JWT segment string to bytes."""
        try:
            segment = (segment or "").strip().replace(" ", "")
            segment += "=" * ((4 - len(segment) % 4) % 4)
            return base64.urlsafe_b64decode(segment)
        except Exception:
            return b""

    @staticmethod
    def _decode_jwt_payload(jwt_token: str) -> Optional[Dict]:
        """Decode JWT payload without verifying signature."""
        try:
            parts = (jwt_token or "").strip().split(".")
            if len(parts) != 3:
                return None
            payload_bytes = DataProcessor._b64url_decode(parts[1])
            if not payload_bytes:
                return None
            return json.loads(payload_bytes.decode("utf-8"))
        except Exception:
            return None

    @staticmethod
    def _parse_url(url_or_path: Optional[str]):
        """
        Parse a URL (or root-relative path) once and return the parsed object.
        All URL-based extraction methods share this single parse result.
        """
        if not url_or_path:
            return None
        full = url_or_path
        if isinstance(full, str) and full.startswith("/"):
            full = "https://dummy" + full
        try:
            return urlparse(full)
        except Exception:
            return None

    @staticmethod
    def _extract_jwt_landing_from_parsed(parsed) -> Optional[str]:
        """Extract landing_page from a JWT token query param, given a pre-parsed URL."""
        if parsed is None:
            return None
        try:
            params = parse_qs(parsed.query, keep_blank_values=True)
            token_values = params.get("token")
            token = token_values[0] if token_values else None
            if not token:
                return None
            payload = DataProcessor._decode_jwt_payload(token)
            if payload and isinstance(payload, dict):
                landing = payload.get("landing_page")
                if landing:
                    return unquote(landing)
        except Exception:
            pass
        return None

    @staticmethod
    def _resolve_and_parse_landing(
        raw_url: Optional[str],
    ) -> Tuple[str, Optional[object], Dict[str, str]]:
        """
        Single-pass URL resolution: parse once, extract JWT landing if present,
        then extract all UTM parameters from the resolved URL.

        Returns:
            (resolved_landing, parsed_resolved, utm_params_dict)
        """
        if not raw_url:
            return (
                "",
                None,
                {
                    "utm_medium": "Unknown",
                    "utm_campaign": "Unknown",
                    "utm_content": "Unknown",
                    "utm_term": "Unknown",
                    "utm_id": "Unknown",
                },
            )

        # Parse the raw URL once
        parsed_raw = DataProcessor._parse_url(raw_url)

        # Check for JWT token → resolved landing page
        jwt_landing = DataProcessor._extract_jwt_landing_from_parsed(parsed_raw)
        resolved = jwt_landing if jwt_landing else raw_url

        # Parse the resolved URL (may differ from raw if JWT decode changed it)
        parsed_resolved = (
            DataProcessor._parse_url(resolved) if jwt_landing else parsed_raw
        )

        # Extract UTM params from the resolved URL in a single parse_qs call
        utm_params = {
            "utm_medium": "Unknown",
            "utm_campaign": "Unknown",
            "utm_content": "Unknown",
            "utm_term": "Unknown",
            "utm_id": "Unknown",
        }
        if parsed_resolved:
            try:
                params = parse_qs(parsed_resolved.query, keep_blank_values=True)
                for key in utm_params:
                    if key in params and params[key]:
                        utm_params[key] = params[key][0]
            except Exception as e:
                logger.warning(f"Error extracting UTM parameters: {str(e)}")

        return resolved, parsed_resolved, utm_params

    @staticmethod
    def _determine_utm_source_from_parsed(
        parsed, utm_params: Dict[str, str], resolved_url: str
    ) -> str:
        """
        Determine UTM source from a pre-parsed URL + already-extracted UTM params.
        Avoids re-parsing the URL string.
        """
        # Explicit utm_source takes priority
        if parsed:
            try:
                params = parse_qs(parsed.query, keep_blank_values=True)
                if "utm_source" in params and params["utm_source"]:
                    source_value = params["utm_source"][0].lower()
                    source_map = {
                        "google": "Google",
                        "google_ads": "Google",
                        "fb": "Meta",
                        "facebook": "Meta",
                        "ig": "Meta",
                        "instagram": "Meta",
                        "meta": "Meta",
                        "klaviyo": "Klaviyo",
                        "snapchat": "Snapchat",
                        "bing": "Bing",
                        "klarna": "Klarna",
                        "pinterest": "Pinterest",
                        "tiktok": "TikTok",
                    }
                    return source_map.get(source_value, source_value.capitalize())
            except Exception:
                pass

        # Fall back to keyword detection on the resolved URL
        return DataProcessor._detect_source_from_url(resolved_url)

    @staticmethod
    def _detect_source_from_url(url: str) -> str:
        """Detect traffic source from URL keywords."""
        if not url:
            return "Unknown"
        if any(k in url for k in ["klaviyo", "_kx="]):
            return "Klaviyo"
        if any(
            m in url
            for m in [
                "Facebook",
                "facebook",
                "Meta",
                "meta",
                "Instagram",
                "instagram",
                "fbclid=",
                "utm_source=fb",
                "utm_source=ig",
            ]
        ):
            return "Meta"
        if any(
            g in url
            for g in [
                "utm_source=google",
                "gclid=",
                "gad_source=",
                "gbraid=",
                "srsltid=",
            ]
        ):
            return "Google"
        if any(
            s in url for s in ["snapchat", "snapcid=", "snap_campaign_id=", "sccid="]
        ):
            return "Snapchat"
        if "syclid=" in url:
            return "Bing"
        if "utm_source=klarna" in url:
            return "Klarna"
        if any(p in url for p in ["pinterest", "pins_campaign_id=", "epik="]):
            return "Pinterest"
        if any(t in url for t in ["source=tiktok", "ttclid="]):
            return "TikTok"
        if "shop_pay" in url:
            return "Shop Pay"
        return "Unknown"

    # ── Kept for backward compatibility ──────────────────────────────────────
    @staticmethod
    def resolve_landing(url_or_path: Optional[str]) -> str:
        resolved, _, _ = DataProcessor._resolve_and_parse_landing(url_or_path)
        return resolved

    @staticmethod
    def extract_utm_parameters(url: str) -> Dict[str, str]:
        _, _, utm = DataProcessor._resolve_and_parse_landing(url)
        return utm

    @staticmethod
    def detect_all_sources(url: str) -> List[str]:
        source = DataProcessor._detect_source_from_url(url)
        return [source]

    @staticmethod
    def determine_utm_source(landing_resolved: str) -> str:
        _, parsed, utm = DataProcessor._resolve_and_parse_landing(landing_resolved)
        return DataProcessor._determine_utm_source_from_parsed(
            parsed, utm, landing_resolved
        )

    # ─────────────────────────────────────────────────────────────────────────

    def process_customer(self, customer_node: Dict) -> Dict:
        """Process customer GraphQL node into database format."""
        try:
            default_email = customer_node.get("defaultEmailAddress") or {}
            default_phone = customer_node.get("defaultPhoneNumber") or {}
            amount_spent = customer_node.get("amountSpent") or {}
            statistics = customer_node.get("statistics") or {}
            address = customer_node.get("defaultAddress") or {}

            return {
                "shopify_customer_id": customer_node.get("id"),
                "display_name": customer_node.get("displayName"),
                "email": default_email.get("emailAddress"),
                "first_name": customer_node.get("firstName"),
                "last_name": customer_node.get("lastName"),
                "phone": default_phone.get("phoneNumber"),
                "locale": customer_node.get("locale"),
                "has_accepted_marketing": customer_node.get("acceptsMarketing", False),
                "marketing_opt_in_level": None,
                "email_marketing_state": default_email.get("marketingState"),
                "sms_marketing_state": default_phone.get("marketingState"),
                "total_spent": float(amount_spent.get("amount", 0)),
                "orders_count": customer_node.get("numberOfOrders", 0),
                "predicted_spend_tier": statistics.get("predictedSpendTier") or "LOW",
                "rfm_group": self.map_rfm_group(statistics.get("rfmGroup")) or "NEW",
                "lifetime_duration": customer_node.get("lifetimeDuration"),
                "is_email_verified": customer_node.get("verifiedEmail", False),
                "is_tax_exempt": customer_node.get("taxExempt", False),
                "tax_exemptions": (
                    json.dumps(customer_node.get("taxExemptions"))
                    if customer_node.get("taxExemptions")
                    else None
                ),
                "state": customer_node.get("state"),
                "tags": (
                    ", ".join(customer_node.get("tags", []))
                    if customer_node.get("tags")
                    else None
                ),
                "note": customer_node.get("note"),
                "default_address_id": address.get("id") if address else None,
                "company": address.get("company") if address else None,
                "address1": address.get("address1") if address else None,
                "address2": address.get("address2") if address else None,
                "city": address.get("city") if address else None,
                "province": address.get("province") if address else None,
                "province_code": address.get("provinceCode") if address else None,
                "country": address.get("country") if address else None,
                "country_code": address.get("countryCodeV2") if address else None,
                "zip": address.get("zip") if address else None,
                "latitude": address.get("latitude") if address else None,
                "longitude": address.get("longitude") if address else None,
                "formatted": (
                    ", ".join(address.get("formatted", []))
                    if address and address.get("formatted")
                    else None
                ),
                "shopify_created_at": self.parse_timestamp(
                    customer_node.get("createdAt")
                ),
                "shopify_updated_at": self.parse_timestamp(
                    customer_node.get("updatedAt")
                ),
                "last_purchased_at": self.parse_timestamp(
                    (customer_node.get("lastOrder") or {}).get("createdAt")
                ),
            }
        except Exception as e:
            logger.error(f"Failed to process customer: {str(e)}")
            raise

    def process_order(self, order_node: Dict) -> Dict:
        """
        Process order GraphQL node into database format.

        Optimization: each landing page URL is parsed exactly once.
        The original code called resolve_landing + determine_utm_source +
        extract_utm_parameters independently, each doing their own urlparse.
        Now a single _resolve_and_parse_landing call covers all three.
        """
        try:
            customer = order_node.get("customer") or {}
            current_total = (order_node.get("currentTotalPriceSet") or {}).get(
                "shopMoney"
            ) or {}
            current_discounts = (order_node.get("currentTotalDiscountsSet") or {}).get(
                "shopMoney"
            ) or {}
            total_tax = (order_node.get("totalTaxSet") or {}).get("shopMoney") or {}
            total_shipping = (order_node.get("totalShippingPriceSet") or {}).get(
                "shopMoney"
            ) or {}
            total_refunded = (order_node.get("totalRefundedShippingSet") or {}).get(
                "shopMoney"
            ) or {}
            transactions = order_node.get("transactions") or []

            net_payment = (order_node.get("netPaymentSet") or {}).get("shopMoney") or {}
            refunds_data = order_node.get("refunds") or {}
            refund_nodes = (
                refunds_data
                if isinstance(refunds_data, list)
                else refunds_data.get("nodes", [])
            )
            total_refunded_amt = sum(
                float(
                    ((r.get("totalRefundedSet") or {}).get("shopMoney") or {}).get(
                        "amount", 0
                    )
                )
                for r in refund_nodes
            )

            order_name = order_node.get("name", "")
            order_number = 0
            if order_name:
                numeric_match = re.search(r"\d+", order_name)
                if numeric_match:
                    order_number = int(numeric_match.group())

            gateways = [t.get("gateway") for t in transactions if t.get("gateway")]

            customer_journey = order_node.get("customerJourneySummary") or {}

            # ── Last visit: single parse covers resolve + UTM extraction ──
            last_visit = customer_journey.get("lastVisit") or {}
            raw_last_landing = last_visit.get("landingPage")
            last_shopify_utm = last_visit.get("utmParameters") or {}

            last_resolved, last_parsed, last_extracted_utm = (
                self._resolve_and_parse_landing(raw_last_landing)
            )
            last_utm_source = self._determine_utm_source_from_parsed(
                last_parsed, last_extracted_utm, last_resolved
            )

            # ── First visit: single parse covers resolve + UTM extraction ──
            first_visit = customer_journey.get("firstVisit") or {}
            raw_first_landing = first_visit.get("landingPage")
            first_shopify_utm = first_visit.get("utmParameters") or {}

            first_resolved, first_parsed, first_extracted_utm = (
                self._resolve_and_parse_landing(raw_first_landing)
            )
            first_utm_source = self._determine_utm_source_from_parsed(
                first_parsed, first_extracted_utm, first_resolved
            )

            return {
                "shopify_order_id": order_node.get("id"),
                "shopify_customer_id": customer.get("id") if customer else None,
                "order_number": order_number,
                "order_name": order_name,
                "email": order_node.get("email"),
                "phone": order_node.get("phone"),
                "financial_status": self.map_financial_status(
                    order_node.get("displayFinancialStatus")
                ),
                "fulfillment_status": self.map_fulfillment_status(
                    order_node.get("displayFulfillmentStatus")
                ),
                "order_status": "pending",
                "return_status": order_node.get("returnStatus"),
                "is_confirmed": order_node.get("confirmed", True),
                "is_test_order": order_node.get("test", False),
                "currency": order_node.get("currencyCode", "USD"),
                "total_tax": float(total_tax.get("amount", 0)),
                "total_discounts": float(current_discounts.get("amount", 0)),
                "total_shipping": float(total_shipping.get("amount", 0)),
                "total_price": float(current_total.get("amount", 0)),
                "total_refunded_shipping": float(total_refunded.get("amount", 0)),
                "total_refunded_amount": total_refunded_amt,
                "net_payment_amount": float(net_payment.get("amount", 0)),
                "note": None,
                "tags": None,
                "discount_codes": order_node.get("discountCodes"),
                "payment_gateway_names": gateways if gateways else None,
                # Last visit
                "last_landing_page": last_resolved,
                "last_utm_source": last_utm_source,
                "last_utm_medium": last_shopify_utm.get("medium")
                or last_extracted_utm.get("utm_medium"),
                "last_utm_campaign": last_shopify_utm.get("campaign")
                or last_extracted_utm.get("utm_campaign"),
                "last_utm_content": last_shopify_utm.get("content")
                or last_extracted_utm.get("utm_content"),
                "last_utm_term": last_shopify_utm.get("term")
                or last_extracted_utm.get("utm_term"),
                "last_utm_id": last_extracted_utm.get("utm_id"),
                "last_original_landing_page": raw_last_landing,
                "last_original_utm_source": last_shopify_utm.get("source"),
                # First visit
                "first_landing_page": first_resolved,
                "first_utm_source": first_utm_source,
                "first_utm_medium": first_shopify_utm.get("medium")
                or first_extracted_utm.get("utm_medium"),
                "first_utm_campaign": first_shopify_utm.get("campaign")
                or first_extracted_utm.get("utm_campaign"),
                "first_utm_content": first_shopify_utm.get("content")
                or first_extracted_utm.get("utm_content"),
                "first_utm_term": first_shopify_utm.get("term")
                or first_extracted_utm.get("utm_term"),
                "first_utm_id": first_extracted_utm.get("utm_id"),
                "first_original_landing_page": raw_first_landing,
                "first_original_utm_source": first_shopify_utm.get("source"),
                "cancelled_at": self.parse_timestamp(order_node.get("cancelledAt")),
                "cancel_reason": order_node.get("cancelReason"),
                "closed_at": self.parse_timestamp(order_node.get("closedAt")),
                "shopify_created_at": self.parse_timestamp(order_node.get("createdAt")),
                "shopify_updated_at": self.parse_timestamp(order_node.get("updatedAt")),
            }

        except Exception as e:
            logger.error(f"Failed to process order: {str(e)}")
            raise

    @staticmethod
    def map_product_status(status: Optional[str]) -> str:
        """Map Shopify product status to database enum."""
        if not status:
            return "ACTIVE"
        return {"ACTIVE": "ACTIVE", "ARCHIVED": "ARCHIVED", "DRAFT": "DRAFT"}.get(
            status.upper(), "ACTIVE"
        )

    def process_product(self, product_node: Dict) -> Dict:
        """Process product GraphQL node into database format."""
        try:
            seo = product_node.get("seo") or {}
            featured_media = product_node.get("featuredMedia") or {}
            featured_preview = (featured_media.get("preview") or {}).get("image") or {}
            media_nodes = (product_node.get("media") or {}).get("nodes") or []
            variants = product_node.get("variants", {}).get("nodes", [])
            options = product_node.get("options", [])

            media_url = None
            media_count = len(media_nodes)
            if media_nodes:
                first_media = media_nodes[0]
                media_preview = (first_media.get("preview") or {}).get("image") or {}
                media_url = media_preview.get("url")

            first_variant = variants[0] if variants else None
            first_unit_cost = (
                (first_variant.get("inventoryItem", {}).get("unitCost") or {})
                if first_variant
                else {}
            )

            product = {
                "shopify_product_id": product_node.get("id"),
                "title": product_node.get("title"),
                "handle": product_node.get("handle"),
                "description_html": product_node.get("descriptionHtml"),
                "product_type": product_node.get("productType"),
                "vendor": product_node.get("vendor"),
                "status": self.map_product_status(product_node.get("status")),
                "price": (
                    float(first_variant.get("price", 0)) if first_variant else None
                ),
                "compare_at_price": (
                    float(first_variant.get("compareAtPrice"))
                    if first_variant and first_variant.get("compareAtPrice")
                    else None
                ),
                "unit_cost_amount": (
                    float(first_unit_cost.get("amount", 0))
                    if first_unit_cost.get("amount")
                    else None
                ),
                "unit_cost_currency_code": first_unit_cost.get("currencyCode"),
                "total_inventory": product_node.get("totalInventory", 0),
                "tags": (
                    ", ".join(product_node.get("tags", []))
                    if product_node.get("tags")
                    else None
                ),
                "seo_title": seo.get("title"),
                "seo_description": seo.get("description"),
                "published_at": self.parse_timestamp(product_node.get("publishedAt")),
                "featured_media_alt": (
                    featured_media.get("alt") or featured_preview.get("altText")
                ),
                "featured_media_url": featured_preview.get("url"),
                "media_url": media_url,
                "media_count": media_count,
                "variants_count": len(variants),
                "options": (
                    [
                        {
                            "id": opt.get("id"),
                            "name": opt.get("name"),
                            "values": opt.get("values", []),
                            "position": opt.get("position"),
                        }
                        for opt in options
                    ]
                    if options
                    else None
                ),
                "shopify_created_at": self.parse_timestamp(
                    product_node.get("createdAt")
                ),
                "shopify_updated_at": self.parse_timestamp(
                    product_node.get("updatedAt")
                ),
            }

            processed_variants = []
            for variant_node in variants:
                selected_options = variant_node.get("selectedOptions", [])
                unit_cost = variant_node.get("inventoryItem", {}).get("unitCost") or {}

                options_vals = [opt.get("value") for opt in selected_options[:3]]
                while len(options_vals) < 3:
                    options_vals.append(None)

                variant = {
                    "shopify_variant_id": variant_node.get("id"),
                    "shopify_product_id": product_node.get("id"),
                    "title": variant_node.get("title"),
                    "sku": variant_node.get("sku"),
                    "barcode": variant_node.get("barcode"),
                    "price": float(variant_node.get("price", 0)),
                    "compare_at_price": (
                        float(variant_node.get("compareAtPrice"))
                        if variant_node.get("compareAtPrice")
                        else None
                    ),
                    "unit_cost_amount": (
                        float(unit_cost.get("amount", 0))
                        if unit_cost.get("amount")
                        else None
                    ),
                    "unit_cost_currency_code": unit_cost.get("currencyCode"),
                    "inventory_quantity": variant_node.get("inventoryQuantity", 0),
                    "inventory_policy": variant_node.get("inventoryPolicy"),
                    "position": variant_node.get("position"),
                    "option1": options_vals[0],
                    "option2": options_vals[1],
                    "option3": options_vals[2],
                    "is_available_for_sale": variant_node.get("availableForSale", True),
                    "shopify_created_at": self.parse_timestamp(
                        variant_node.get("createdAt")
                    ),
                    "shopify_updated_at": self.parse_timestamp(
                        variant_node.get("updatedAt")
                    ),
                }
                processed_variants.append(variant)

            return {"product": product, "variants": processed_variants}

        except Exception as e:
            logger.error(f"Failed to process product: {str(e)}")
            raise

    def process_order_line_items(self, order_node: Dict) -> List[Dict]:
        """Process order line items from order GraphQL node."""
        try:
            line_items_nodes = (order_node.get("lineItems") or {}).get("nodes") or []
            processed_items = []

            for item_node in line_items_nodes:
                variant = item_node.get("variant") or {}
                product = variant.get("product") or {}

                original_price = (item_node.get("originalUnitPriceSet") or {}).get(
                    "shopMoney"
                ) or {}
                discounted_price = (item_node.get("discountedUnitPriceSet") or {}).get(
                    "shopMoney"
                ) or {}
                total_discount = (item_node.get("totalDiscountSet") or {}).get(
                    "shopMoney"
                ) or {}

                price = float(discounted_price.get("amount", 0)) or float(
                    original_price.get("amount", 0)
                )

                processed_items.append(
                    {
                        "shopify_line_item_id": item_node.get("id"),
                        "shopify_product_id": product.get("id"),
                        "shopify_variant_id": variant.get("id"),
                        "product_title": item_node.get("title"),
                        "variant_title": variant.get("title"),
                        "sku": variant.get("sku"),
                        "quantity": item_node.get("quantity", 1),
                        "price": price,
                        "total_discount": float(total_discount.get("amount", 0)),
                    }
                )

            return processed_items

        except Exception as e:
            logger.error(f"Failed to process line items: {str(e)}")
            raise
