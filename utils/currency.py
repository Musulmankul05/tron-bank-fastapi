import json
from decimal import Decimal
from typing import Literal

import httpx
from fastapi import HTTPException

from utils.redis import redis_client


async def get_exchange_rate(
    from_curr: Literal["KGS", "EUR", "USD"], to_curr: Literal["KGS", "EUR", "USD"]
) -> Decimal:
    if from_curr == to_curr:
        return Decimal("1.0000")

    cache = await redis_client.get("exchange_rates:USD")
    if cache:
        rates = json.loads(cache)
    else:
        try:
            url = "https://open.er-api.com/v6/latest/USD"
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=5.0)
                response.raise_for_status()
                data = response.json()
                rates = data.get("rates", {})
                await redis_client.set("exchange_rates:USD", json.dumps(rates), ex=5400)
        except Exception:
            raise HTTPException(503, "Currency rate service is unavailable")

    try:
        from_rate = Decimal(str(rates[from_curr]))
        to_rate = Decimal(str(rates[to_curr]))
    except KeyError:
        raise HTTPException(
            400, "Unsupported currency"
        )

    return (to_rate / from_rate).quantize(Decimal("0.0001"))
