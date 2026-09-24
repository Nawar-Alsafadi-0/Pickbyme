import json

import httpx

from app.payments import ThawaniClient


def test_thawani_checkout_and_server_side_payment_verification(monkeypatch):
    monkeypatch.setenv("THAWANI_SECRET_KEY", "test-secret")
    monkeypatch.setenv("THAWANI_PUBLISHABLE_KEY", "test-public")
    monkeypatch.setenv("THAWANI_API_BASE", "https://gateway.test/api/v1")
    monkeypatch.setenv("THAWANI_CHECKOUT_BASE", "https://gateway.test/pay")

    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "POST":
            seen["auth"] = request.headers.get("thawani-api-key")
            seen["payload"] = json.loads(request.content.decode())
            return httpx.Response(200, json={
                "success": True,
                "data": {
                    "session_id": "checkout_test_123",
                    "payment_status": "unpaid",
                },
            })
        return httpx.Response(200, json={
            "success": True,
            "data": {
                "session_id": "checkout_test_123",
                "payment_status": "paid",
            },
        })

    http = httpx.Client(transport=httpx.MockTransport(handler))
    provider = ThawaniClient(client=http)

    session = provider.create_checkout(
        order_id=42,
        product_name="Dinner for Two",
        amount_minor=25000,
        currency="OMR",
        success_url="https://pickbyme.test/success",
        cancel_url="https://pickbyme.test/cancel",
        buyer_name="Buyer",
        buyer_email="buyer@example.com",
    )

    assert session.provider_reference == "checkout_test_123"
    assert session.checkout_url == "https://gateway.test/pay/checkout_test_123?key=test-public"
    assert seen["auth"] == "test-secret"
    assert seen["payload"]["client_reference_id"] == "pickbyme-order-42"
    assert seen["payload"]["products"][0]["unit_amount"] == 25000
    assert provider.is_paid(session.provider_reference) is True
