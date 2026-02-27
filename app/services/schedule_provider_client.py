import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from random import randint

from config import settings


@dataclass
class QuoteResult:
    provider_name: str
    external_quote_id: str
    price_amount: Decimal
    currency: str
    payment_url: str
    expires_at: datetime
    payload: dict


class ScheduleProviderClient:
    async def get_quote_stub(
        self,
        request_id: int,
        total_duration_minutes: int,
        base_currency: str | None,
    ) -> QuoteResult:
        amount = Decimal(max(total_duration_minutes, 30)) * Decimal("0.85")
        currency = (base_currency or settings.default_currency).upper()
        quote_id = f"stub-{uuid.uuid4()}"
        return QuoteResult(
            provider_name="stub_provider",
            external_quote_id=quote_id,
            price_amount=amount.quantize(Decimal("0.01")),
            currency=currency,
            payment_url=f"https://pay.example.com/checkout/{quote_id}",
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=randint(20, 60)),
            payload={"mode": "stub", "request_id": str(request_id)},
        )
