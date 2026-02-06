"""
Financial MCP Client
====================
A comprehensive module for currency conversion, exchange rates, and stock/crypto data 
via RapidAPI (using both Currency Conversion and Alpha Vantage APIs).

Functions:
    - convert_currency: Convert amount from one currency to another
    - get_latest_rates: Get current exchange rates for a base currency
    - get_stock_data: Get intraday or monthly stock time series
    - get_crypto_data: Get daily or monthly crypto market data
    - search_stocks: Search for stock symbols by name/keyword

Usage:
    from backend.mcp.exchange_rate import FinancialClient
    
    client = FinancialClient(api_key="your_api_key")
    rate = client.convert_currency("USD", "INR", 100)
"""

import os
import http.client
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from urllib.parse import quote


@dataclass
class FinanceConfig:
    """Configuration for Financial API clients."""
    api_key: str
    currency_host: str = "currency-conversion-and-exchange-rates.p.rapidapi.com"
    alpha_vantage_host: str = "alpha-vantage.p.rapidapi.com"


class FinancialClient:
        def llm_convert_currency(self, payload: str) -> dict:
            """LLM adapter: Convert currency. Payload: {"from_curr": str, "to_curr": str, "amount": float}"""
            import json
            try:
                args = json.loads(payload)
                result = self.convert_currency(
                    args["from_curr"], args["to_curr"], float(args["amount"])
                )
                return {"status": "success", "result": result}
            except Exception as e:
                return {"status": "error", "message": str(e)}
    """
    Client for financial data including currency, stocks, and crypto.
    
    Combines 'Currency Conversion' and 'Alpha Vantage' APIs.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize with RapidAPI key."""
        key = api_key or os.getenv("RAPIDAPI_KEY")
        if not key:
            raise ValueError("RAPIDAPI_KEY is required.")
        self.config = FinanceConfig(api_key=key)
        self._headers = {
            "x-rapidapi-key": self.config.api_key,
            "Content-Type": "application/json"
        }

    def _make_request(self, host: str, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Internal helper for HTTP requests."""
        conn = http.client.HTTPSConnection(host)
        
        # Build query string
        query_parts = [f"{k}={quote(str(v))}" for k, v in params.items() if v is not None]
        url = f"{endpoint}?{'&'.join(query_parts)}" if query_parts else endpoint
        
        try:
            headers = self._headers.copy()
            headers["x-rapidapi-host"] = host
            conn.request("GET", url, headers=headers)
            response = conn.getresponse()
            data = response.read().decode("utf-8")
            
            if response.status != 200:
                return {"status": "error", "code": response.status, "message": data}
            
            return json.loads(data)
        except Exception as e:
            return {"status": "error", "message": str(e)}
        finally:
            conn.close()

    # --- Currency Endpoints ---

    def convert_currency(self, from_curr: str, to_curr: str, amount: float) -> Dict[str, Any]:
        """Convert an amount from one currency to another."""
        params = {"from": from_curr, "to": to_curr, "amount": amount}
        return self._make_request(self.config.currency_host, "/convert", params)

    def get_latest_rates(self, base: str = "USD", symbols: Optional[List[str]] = None) -> Dict[str, Any]:
        """Get latest exchange rates."""
        params = {"base": base}
        if symbols:
            params["symbols"] = ",".join(symbols)
        return self._make_request(self.config.currency_host, "/latest", params)

    def get_historical_rates(self, date: str, base: str = "USD", symbols: Optional[List[str]] = None) -> Dict[str, Any]:
        """Get rates for a specific date (YYYY-MM-DD)."""
        params = {"base": base}
        if symbols:
            params["symbols"] = ",".join(symbols)
        return self._make_request(self.config.currency_host, f"/{date}", params)

    def get_currency_timeseries(self, start_date: str, end_date: str, base: str = "USD", symbols: Optional[List[str]] = None) -> Dict[str, Any]:
        """Get currency rates over a time period."""
        params = {
            "start_date": start_date,
            "end_date": end_date,
            "base": base
        }
        if symbols:
            params["symbols"] = ",".join(symbols)
        return self._make_request(self.config.currency_host, "/timeseries", params)

    def get_supported_currencies(self) -> Dict[str, Any]:
        """Get list of all supported currency symbols."""
        return self._make_request(self.config.currency_host, "/symbols", {})

    # --- Alpha Vantage (Stocks/Crypto) Endpoints ---

    def search_stocks(self, keywords: str) -> Dict[str, Any]:
        """Search for stock symbols and businesses."""
        params = {
            "function": "SYMBOL_SEARCH",
            "keywords": keywords,
            "datatype": "json"
        }
        return self._make_request(self.config.alpha_vantage_host, "/query", params)

    def get_stock_intraday(self, symbol: str, interval: str = "5min", output_size: str = "compact") -> Dict[str, Any]:
        """Get intraday stock time series (1min, 5min, 15min, 30min, 60min)."""
        params = {
            "function": "TIME_SERIES_INTRADAY",
            "symbol": symbol,
            "interval": interval,
            "output_size": output_size,
            "datatype": "json"
        }
        return self._make_request(self.config.alpha_vantage_host, "/query", params)

    def get_stock_monthly(self, symbol: str) -> Dict[str, Any]:
        """Get monthly stock time series."""
        params = {
            "function": "TIME_SERIES_MONTHLY",
            "symbol": symbol,
            "datatype": "json"
        }
        return self._make_request(self.config.alpha_vantage_host, "/query", params)

    def get_crypto_daily(self, symbol: str, market: str = "USD") -> Dict[str, Any]:
        """Get daily crypto time series (e.g., symbol='BTC', market='USD')."""
        params = {
            "function": "DIGITAL_CURRENCY_DAILY",
            "symbol": symbol,
            "market": market,
            "datatype": "json"
        }
        return self._make_request(self.config.alpha_vantage_host, "/query", params)

    def get_crypto_monthly(self, symbol: str, market: str = "USD") -> Dict[str, Any]:
        """Get monthly crypto time series."""
        params = {
            "function": "DIGITAL_CURRENCY_MONTHLY",
            "symbol": symbol,
            "market": market,
            "datatype": "json"
        }
        return self._make_request(self.config.alpha_vantage_host, "/query", params)


# --- Convenience Functions ---

_default_client: Optional[FinancialClient] = None

def _get_client() -> FinancialClient:
    global _default_client
    if _default_client is None:
        _default_client = FinancialClient()
    return _default_client

def convert_currency(from_curr: str, to_curr: str, amount: float):
    return _get_client().convert_currency(from_curr, to_curr, amount)

def search_stocks(keywords: str):
    return _get_client().search_stocks(keywords)

def get_latest_rates(base: str = "USD"):
    return _get_client().get_latest_rates(base)

if __name__ == "__main__":
    # Quick test if RAPIDAPI_KEY is set
    if os.getenv("RAPIDAPI_KEY"):
        client = FinancialClient()
        print("Testing currency conversion (USD to EUR 100):")
        print(client.convert_currency("USD", "EUR", 100))
        print("\nTesting stock search (Microsoft):")
        print(client.search_stocks("microsoft"))
    else:
        print("Set RAPIDAPI_KEY to test.")