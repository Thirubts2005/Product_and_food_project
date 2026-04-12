"""
automation.py — Simulates cart automation and order placement.
In production: replace with Selenium/Playwright for real browser automation.
"""
import time
from price_checker import get_best_price


def simulate_add_to_cart(low_items: list, cart: list) -> int:
    """
    Auto-adds low-stock items to cart using best available price.
    Returns count of newly added items.
    """
    added = 0
    for item in low_items:
        name = item[1]
        if add_single_item_to_cart(name, cart):
            added += 1
    return added


def add_single_item_to_cart(item_name: str, cart: list) -> bool:
    """
    Adds a single item to the cart using the best available price.
    Returns True if added, False if already in cart or no price found.
    """
    # Skip if already in cart
    if any(c["name"].lower() == item_name.lower() for c in cart):
        return False

    best = get_best_price(item_name)
    if best:
        cart.append({
            "name":     best["item"],
            "price":    best["price"],
            "platform": best["platform"],
            "qty":      1,
        })
        return True
    return False


def simulate_order(cart: list) -> list[str]:
    """
    Simulates a full order flow and returns log lines.
    In production: use Playwright/Selenium to automate real checkout.
    """
    log = []

    if not cart:
        log.append("[WARN] Cart is empty — nothing to order.")
        return log

    log.append("[INFO] Initializing GroceryMind automation bot…")
    log.append("[INFO] Connecting to platform APIs…")
    log.append("[OK]   Auth token validated ✓")
    log.append("[INFO] Reviewing cart contents…")

    total = 0
    for item in cart:
        subtotal = item["price"] * item["qty"]
        total += subtotal
        log.append(f"[OK]   Added \"{item['name']}\" × {item['qty']}  →  ₹{subtotal:.2f}  ({item['platform']})")

    log.append("[INFO] Applying best price filters…")
    log.append("[INFO] Checking delivery slots…")
    log.append("[OK]   Fastest delivery: 10–20 minutes ✓")
    log.append(f"[OK]   🎉 Order simulated successfully! Total: ₹{total:.2f}")

    return log


# ── PRODUCTION AUTOMATION STUB ────────────────────────────
# Uncomment for real browser automation with Playwright:
#
# from playwright.async_api import async_playwright
#
# async def real_add_to_cart_blinkit(item_name: str, qty: int = 1):
#     async with async_playwright() as p:
#         browser = await p.chromium.launch(headless=False)
#         page = await browser.new_page()
#         await page.goto("https://blinkit.com")
#         await page.fill('[placeholder="Search for items"]', item_name)
#         await page.press('[placeholder="Search for items"]', "Enter")
#         await page.wait_for_selector(".product-card")
#         await page.click(".product-card:first-child .add-to-cart")
#         await browser.close()
