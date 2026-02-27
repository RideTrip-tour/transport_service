import pytest

from app.services.schedule_provider_client import ScheduleProviderClient


@pytest.mark.asyncio
async def test_quote_stub_returns_payment_url_and_currency():
    client = ScheduleProviderClient()

    quote = await client.get_quote_stub(
        request_id=123,
        total_duration_minutes=95,
        base_currency="EUR",
    )

    assert quote.currency == "EUR"
    assert quote.payment_url.startswith("https://pay.example.com/checkout/")
    assert quote.price_amount > 0
    assert quote.provider_name == "stub_provider"
