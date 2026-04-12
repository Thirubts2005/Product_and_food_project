"""
utils/helpers.py — Shared utility functions
"""
from datetime import datetime


def format_inr(amount: float) -> str:
    """Format float as Indian Rupees string."""
    return f"₹{amount:,.2f}"


def status_label(status: str) -> str:
    return {"ok": "✅ Good", "med": "⚠️ Medium", "low": "🔴 Low"}.get(status, status)


def today_str() -> str:
    return datetime.now().strftime("%d %b %Y")


def days_until_empty(qty: float, daily_use: float) -> int:
    """Rough estimate of days until stock runs out."""
    if daily_use <= 0:
        return 999
    return max(0, int(qty / daily_use))
