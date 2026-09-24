import os
from dataclasses import dataclass
from urllib.parse import quote

import httpx


class PaymentConfigurationError(RuntimeError):
    pass


class PaymentProviderError(RuntimeError):
    pass


@dataclass
class CheckoutSession:
    provider_reference: str
    checkout_url: str
    status: str


class ThawaniClient:
    def __init__(self, client: httpx.Client | None = None):
        self.secret_key = os.getenv("THAWANI_SECRET_KEY", "").strip()
        self.publishable_key = os.getenv("THAWANI_PUBLISHABLE_KEY", "").strip()
        self.api_base = os.getenv("THAWANI_API_BASE", "https://uatcheckout.thawani.om/api/v1").rstrip("/")
        self.checkout_base = os.getenv("THAWANI_CHECKOUT_BASE", "https://uatcheckout.thawani.om/pay").rstrip("/")
        self.client = client or httpx.Client(timeout=20.0)

    @property
    def configured(self) -> bool:
        return bool(self.secret_key and self.publishable_key)

    def _headers(self) -> dict[str, str]:
        if not self.configured:
            raise PaymentConfigurationError("Thawani credentials are not configured")
        return {"Content-Type": "application/json", "thawani-api-key": self.secret_key}

    def create_checkout(
        self,
        *,
        order_id: int,
        product_name: str,
        amount_minor: int,
        currency: str,
        success_url: str,
        cancel_url: str,
        buyer_name: str,
        buyer_email: str,
    ) -> CheckoutSession:
        if currency != "OMR":
            raise PaymentProviderError("Thawani checkout is currently enabled only for OMR orders")
        payload = {
            "client_reference_id": f"pickbyme-order-{order_id}",
            "mode": "payment",
            "products": [{"name": product_name, "quantity": 1, "unit_amount": amount_minor}],
            "success_url": success_url,
            "cancel_url": cancel_url,
            "metadata": {
                "order_id": str(order_id),
                "buyer_name": buyer_name,
                "buyer_email": buyer_email,
            },
        }
        try:
            response = self.client.post(f"{self.api_base}/checkout/session", headers=self._headers(), json=payload)
            response.raise_for_status()
            body = response.json()
        except Exception as exc:
            raise PaymentProviderError(f"Could not create Thawani checkout: {exc}") from exc
        if not body.get("success") or not body.get("data", {}).get("session_id"):
            raise PaymentProviderError(body.get("description") or "Thawani did not return a checkout session")
        session_id = body["data"]["session_id"]
        checkout_url = f"{self.checkout_base}/{quote(session_id)}?key={quote(self.publishable_key)}"
        return CheckoutSession(
            provider_reference=session_id,
            checkout_url=checkout_url,
            status=body["data"].get("payment_status", "unpaid"),
        )

    def retrieve_checkout(self, session_id: str) -> dict:
        try:
            response = self.client.get(
                f"{self.api_base}/checkout/session/{quote(session_id)}",
                headers=self._headers(),
            )
            response.raise_for_status()
            body = response.json()
        except Exception as exc:
            raise PaymentProviderError(f"Could not retrieve Thawani checkout: {exc}") from exc
        if not body.get("success"):
            raise PaymentProviderError(body.get("description") or "Could not verify Thawani checkout")
        return body.get("data", {})

    def is_paid(self, session_id: str) -> bool:
        data = self.retrieve_checkout(session_id)
        return str(data.get("payment_status", "")).lower() == "paid"
