import requests
from typing import Dict, Any

class ExchangeRateMCP:
    def __init__(self):
        self.api_key = "d0cc33ea84da" # Mock key or use env var
        self.base_url = "https://v6.exchangerate-api.com/v6"

    def convert(self, amount: float, from_currency: str, to_currency: str) -> float:
        print(f"[ExchangeRateMCP] Converting {amount} {from_currency} -> {to_currency}")
        rate = self._get_rate(from_currency, to_currency)
        return amount * rate

    def _get_rate(self, from_curr: str, to_curr: str) -> float:
        # Mock rates
        rates = {
            "USD": {"EUR": 0.92, "GBP": 0.79, "INR": 83.0},
            "EUR": {"USD": 1.09},
        }
        return rates.get(from_curr, {}).get(to_curr, 1.0)

exchange_rate_mcp = ExchangeRateMCP()
