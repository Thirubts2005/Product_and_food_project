"""
telegram_utils.py — Utilities for Telegram notifications.
"""
import os
import requests
import json
from datetime import datetime
from inventory import update_last_notified
from dotenv import load_dotenv

load_dotenv()

# CONFIGURATION (User must fill these or set via .env)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
TELEGRAM_CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID", "YOUR_CHAT_ID_HERE")

def send_telegram_alert(item_id, item_name):
    """
    Sends a Telegram message for a single item with Inline Buttons.
    """
    if TELEGRAM_BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        return False
        
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    text = f"⚠️ *{item_name}* is running low in your GroceryMind inventory!\n\n"
    text += "What would you like to do?"
    
    # Inline keyboard with callback data
    keyboard = {
        "inline_keyboard": [
            [
                {"text": "🛒 Add to Cart", "callback_data": f"add:{item_name}"},
                {"text": "❌ Ignore", "callback_data": "ignore"}
            ]
        ]
    }
    
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
        "reply_markup": keyboard
    }
    
    try:
        r = requests.post(url, json=payload, timeout=10)
        if r.status_code == 200:
            update_last_notified(item_id)
            return True
        else:
            import streamlit as st
            st.error(f"Telegram API Error: {r.status_code} - {r.text}")
    except Exception as e:
        import streamlit as st
        st.error(f"Telegram Connection Error: {e}")
        print(f"Telegram error: {e}")
        
    return False

def automate_telegram_alerts(low_items: list, force=False):
    """
    Checks for low stock items and sends individual Telegram notifications.
    By default sends once per day, but can be forced (e.g., on refresh).
    """
    today = datetime.now().strftime("%Y-%m-%d")
    any_sent = False
    
    for item in low_items:
        # id, name, qty, unit, status, icon, cat, added, last_notified
        iid = item[0]
        iname = item[1]
        last_notified = item[8]
        
        # If force=True, we send anyway. Otherwise only once per day.
        if force or last_notified != today:
            if send_telegram_alert(iid, iname):
                any_sent = True
            
    return any_sent
