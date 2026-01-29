"""
eBay Browse API Search Example (2026 version)
---------------------------------------------
Features:
- Gets application access token using Client Credentials
- Searches items using Browse API v1 /item_summary/search
- Supports filters (price range, condition, location/marketplace)
- Prints clean results with title, price, condition, URL

Requirements:
    pip install requests python-dotenv

Get credentials:
    1. https://developer.ebay.com/
    2. My Apps → Create App (Production)
    3. Copy App ID (Client ID) and Cert ID (Client Secret)
    4. Create .env file with:
        EBAY_CLIENT_ID=your_app_id
        EBAY_CLIENT_SECRET=your_cert_id
"""

import requests
import base64
import os
import json
from datetime import datetime
from dotenv import load_dotenv

# ────────────────────────────────────────────────────────────────
# Load environment variables
# ────────────────────────────────────────────────────────────────
load_dotenv()

CLIENT_ID     = os.getenv("EBAY_CLIENT_ID")
CLIENT_SECRET = os.getenv("EBAY_CLIENT_SECRET")

if not CLIENT_ID or not CLIENT_SECRET:
    print("Error: EBAY_CLIENT_ID and EBAY_CLIENT_SECRET must be set in .env file")
    exit(1)


# ────────────────────────────────────────────────────────────────
# Step 1: Get Application Access Token (Client Credentials)
# ────────────────────────────────────────────────────────────────
def get_ebay_access_token():
    credentials = base64.b64encode(
        f"{CLIENT_ID}:{CLIENT_SECRET}".encode("utf-8")
    ).decode("utf-8")

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {credentials}"
    }

    data = {
        "grant_type": "client_credentials",
        "scope": "https://api.sandbox.ebay.com/oauth/api_scope/buy.item_summary"
    }

    url = "https://api.sandbox.ebay.com/identity/v1/oauth2/token"

    try:
        response = requests.post(url, headers=headers, data=data, timeout=10)
        response.raise_for_status()
        token_data = response.json()
        print("Token response:", json.dumps(token_data, indent=2))  # ← add this for debugging
        return token_data["access_token"]
    except requests.exceptions.RequestException as e:
        print(f"Token request failed: {e}")
        if 'response' in locals():
            print("Full response:", response.text)  # ← crucial for seeing the real error
        exit(1)

# ────────────────────────────────────────────────────────────────
# Step 2: Search items using Browse API
# ────────────────────────────────────────────────────────────────
def search_ebay_items(
    access_token: str,
    query: str,
    max_price: float = None,
    min_price: float = 0,
    condition: str = "NEW",           # NEW | USED | UNSPECIFIED
    limit: int = 10,
    marketplace: str = "EBAY-IN",     # EBAY-IN = India, EBAY-US = USA, etc.
    sort: str = "-price"              # -price = cheapest first, endingSoonest, newlyListed, etc.
):
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-EBAY-C-MARKETPLACE-ID": marketplace
    }

    params = {
        "q": query,
        "limit": str(limit),
        "sort": sort,
    }

    # Add price filter if provided
    price_filter = []
    if min_price is not None:
        price_filter.append(f"price:[{min_price}..")
    if max_price is not None:
        if price_filter:
            price_filter[-1] += f"{max_price}]"
        else:
            price_filter.append(f"price:[..{max_price}]")
    if price_filter:
        params["filter"] = ",".join(price_filter + [f"condition:{{{condition}}}"])

    url = "https://api.sandbox.ebay.com/buy/browse/v1/item_summary/search"

    try:
        response = requests.get(url, headers=headers, params=params, timeout=15)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Search failed: {e}")
        if 'response' in locals():
            print("Status:", response.status_code)
            print("Response:", response.text)
        return None


# ────────────────────────────────────────────────────────────────
# Format and display results
# ────────────────────────────────────────────────────────────────
def print_search_results(data):
    if not data or "itemSummaries" not in data or not data["itemSummaries"]:
        print("No items found.")
        return

    print(f"\n{'='*80}")
    print(f"eBay Search Results ({datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')})")
    print(f"{'='*80}\n")

    for i, item in enumerate(data["itemSummaries"], 1):
        title = item.get("title", "N/A")
        price_info = item.get("price", {})
        price = price_info.get("value", "N/A")
        currency = price_info.get("currency", "N/A")
        condition = item.get("condition", "N/A")
        url = item.get("itemWebUrl", "N/A")
        image = item.get("image", {}).get("imageUrl", "No image")

        print(f"{i}. {title}")
        print(f"   Price: {price} {currency}")
        print(f"   Condition: {condition}")
        print(f"   Link: {url}")
        if image != "No image":
            print(f"   Image: {image}")
        print("-" * 70)


# ────────────────────────────────────────────────────────────────
# Main execution
# ────────────────────────────────────────────────────────────────
def main():
    print("Getting eBay access token...")
    token = get_ebay_access_token()
    print("Token obtained successfully.\n")

    # ── Customize your search here ─────────────────────────────────────
    search_query = "sufi music CD"          # ← change this
    max_price_inr = 1500                    # ← optional
    limit_results = 8
    marketplace_id = "EBAY-IN"              # India

    print(f"Searching for: '{search_query}' (max ₹{max_price_inr or 'no limit'})")
    results = search_ebay_items(
        access_token=token,
        query=search_query,
        max_price=max_price_inr,
        limit=limit_results,
        marketplace=marketplace_id
    )

    if results:
        print_search_results(results)


if __name__ == "__main__":
    main()