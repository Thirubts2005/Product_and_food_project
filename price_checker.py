"""
price_checker.py — Simulated price comparison across Indian grocery platforms.
In production, replace with real web scraping (BeautifulSoup / Playwright).
"""
import random

# Popular items with base prices per platform (₹)
POPULAR_ITEMS = {
    "Milk":             {"Blinkit": 26,  "BigBasket": 28,  "Zepto": 27,  "Swiggy Instamart": 29},
    "Basmati Rice 5kg": {"Blinkit": 385, "BigBasket": 379, "Zepto": 395, "Swiggy Instamart": 399},
    "Toor Dal 1kg":     {"Blinkit": 148, "BigBasket": 142, "Zepto": 151, "Swiggy Instamart": 155},
    "Sunflower Oil 1L": {"Blinkit": 138, "BigBasket": 132, "Zepto": 141, "Swiggy Instamart": 145},
    "Eggs 12pcs":       {"Blinkit": 84,  "BigBasket": 88,  "Zepto": 82,  "Swiggy Instamart": 86},
    "Onion 1kg":        {"Blinkit": 42,  "BigBasket": 38,  "Zepto": 44,  "Swiggy Instamart": 45},
    "Atta 5kg":         {"Blinkit": 229, "BigBasket": 219, "Zepto": 235, "Swiggy Instamart": 239},
    "Tomato 1kg":       {"Blinkit": 35,  "BigBasket": 32,  "Zepto": 38,  "Swiggy Instamart": 40},
    "Potato 1kg":       {"Blinkit": 28,  "BigBasket": 25,  "Zepto": 30,  "Swiggy Instamart": 32},
    "Sugar 1kg":        {"Blinkit": 44,  "BigBasket": 42,  "Zepto": 46,  "Swiggy Instamart": 48},
}

PLATFORM_META = {
    "Blinkit":          {"delivery": 10,  "min_order": 10},
    "BigBasket":        {"delivery": 0,   "min_order": 500},
    "Zepto":            {"delivery": 12,  "min_order": 50},
    "Swiggy Instamart": {"delivery": 15,  "min_order": 100},
}


def compare_prices(item_name: str) -> list[dict]:
    """
    Returns a list of price dicts for the given item across all platforms.
    Fuzzy matches the item name against POPULAR_ITEMS keys.
    
    Each dict:
        platform (str), price (int), delivery (int), min_order (int)
    
    In production: replace with real scraping logic per platform.
    """
    # Fuzzy match
    matched_key = None
    query = item_name.lower().strip()
    for key in POPULAR_ITEMS:
        if query in key.lower() or key.lower().split()[0] in query:
            matched_key = key
            break

    if not matched_key:
        return []

    base_prices = POPULAR_ITEMS[matched_key]
    results = []

    for platform, base_price in base_prices.items():
        # Add slight random variation to simulate real-time pricing
        variation = random.randint(-2, 3)
        price = max(1, base_price + variation)
        meta = PLATFORM_META.get(platform, {"delivery": 0, "min_order": 199})
        results.append({
            "platform":  platform,
            "price":     price,
            "delivery":  meta["delivery"],
            "min_order": meta["min_order"],
            "item":      matched_key,
        })

    return sorted(results, key=lambda x: x["price"])


def get_best_price(item_name: str) -> dict | None:
    """Returns the single best (cheapest) price option for an item."""
    results = compare_prices(item_name)
    return results[0] if results else None


# ── PRODUCTION SCRAPING STUB ──────────────────────────────
# Uncomment and implement these for real scraping:
#
# from bs4 import BeautifulSoup
# import requests
#
# def scrape_blinkit(item: str) -> int:
#     """Scrape price from Blinkit (requires login/session handling)."""
#     headers = {"User-Agent": "Mozilla/5.0 ..."}
#     url = f"https://blinkit.com/s/?q={item.replace(' ', '+')}"
#     response = requests.get(url, headers=headers, timeout=10)
#     soup = BeautifulSoup(response.text, "html.parser")
#     # Parse price element — selector varies, update as needed
#     price_tag = soup.select_one(".product-price")
#     return int(price_tag.text.replace("₹", "").strip()) if price_tag else 0
