"""
ai_logic.py — AI suggestions + inventory intent parser via Ollama (free, local)
"""
import re
import requests
import json

OLLAMA_BASE = "http://localhost:11434"

# ── OLLAMA STATUS ─────────────────────────────────────────
def check_ollama_status(model: str = "mistral") -> tuple[bool, str]:
    try:
        resp = requests.get(f"{OLLAMA_BASE}/api/tags", timeout=3)
        if resp.status_code == 200:
            models = [m["name"].split(":")[0] for m in resp.json().get("models", [])]
            if models:
                return True, model if model in models else models[0]
        return False, "no models"
    except Exception:
        return False, "not running"


# ── INTENT PARSER (rule-based, zero cost, works offline) ──
# Understands: "add 5 apples", "add 2kg rice", "remove milk", "update sugar to 3"
_ADD_PATTERNS = [
    # "add 5 apples"  "add five apples"
    r"(?:add|put|insert|stock|bought|i have|we have|i got|we got|i bought|we bought)\s+(\d+\.?\d*|one|two|three|four|five|six|seven|eight|nine|ten)\s*(?:(kg|g|l|litre|liter|ml|packet|packets|dozen|units?|pcs|pieces?))?\s+(?:of\s+)?(.+)",
    # "5 apples add"  or just "5 apples"
    r"(\d+\.?\d*|one|two|three|four|five|six|seven|eight|nine|ten)\s*(kg|g|l|litre|liter|ml|packet|packets|dozen|units?|pcs|pieces?)?\s+(?:of\s+)?(.+?)(?:\s+(?:to|in|into)(?:\s+(?:inventory|stock|the list))?)?$",
]
_REMOVE_PATTERNS = [
    # "remove 5kg rice" or "remove rice"
    r"(?:remove|delete|take out|i used|i ate|i consumed|finished|used up|consumed|ate)\s+(?:all\s+)?(?:the\s+)?(?:\d+\.?\d*\s*(?:kg|g|l|ml|litre|liter|units?|packets?|pcs?|pieces?)\s+)?(?:of\s+)?(.+?)(?:\s+from\s+(?:inventory|stock))?$",
]
_UPDATE_PATTERNS = [
    r"(?:update|set|change)\s+(.+?)\s+to\s+(\d+\.?\d*)\s*(kg|g|l|ml|units?|packets?)?",
]

WORD_NUMS = {"one":1,"two":2,"three":3,"four":4,"five":5,"six":6,"seven":7,"eight":8,"nine":9,"ten":10}

def _normalize_unit(u: str) -> str:
    if not u: return "units"
    u = u.lower().rstrip("s")
    mapping = {"litre":"L","liter":"L","l":"L","ml":"ml","kg":"kg","g":"g","packet":"packets","piece":"units","pc":"units","dozen":"dozen","unit":"units"}
    return mapping.get(u, u)

def _word_to_num(s: str) -> float:
    s = s.strip().lower()
    if s in WORD_NUMS: return float(WORD_NUMS[s])
    try: return float(s)
    except: return 1.0

def parse_inventory_intent(text: str) -> dict | None:
    """
    Parse a natural-language command into a structured inventory action.
    Returns dict like:
        {"action": "add",    "name": "Apple", "qty": 5.0, "unit": "units"}
        {"action": "remove", "name": "Milk"}
        {"action": "update", "name": "Sugar", "qty": 3.0, "unit": "kg"}
    Returns None if no inventory intent detected.
    """
    t = text.strip().lower()

    # --- REMOVE ---
    for pattern in _REMOVE_PATTERNS:
        m = re.match(pattern, t, re.IGNORECASE)
        if m:
            name = m.group(1).strip().rstrip(".!,").title()
            if len(name) > 1:
                return {"action": "remove", "name": name}

    # --- UPDATE ---
    for pattern in _UPDATE_PATTERNS:
        m = re.match(pattern, t, re.IGNORECASE)
        if m:
            name = m.group(1).strip().title()
            qty  = float(m.group(2))
            unit = _normalize_unit(m.group(3))
            return {"action": "update", "name": name, "qty": qty, "unit": unit}

    # --- ADD ---
    for pattern in _ADD_PATTERNS:
        m = re.match(pattern, t, re.IGNORECASE)
        if m:
            groups = m.groups()
            qty_str = groups[0]
            unit_raw = groups[1] if len(groups) > 2 else None
            name_raw = groups[-1]
            qty  = _word_to_num(qty_str)
            unit = _normalize_unit(unit_raw)
            name = name_raw.strip().rstrip(".!,")
            # clean common filler words
            for filler in ["to inventory","to stock","to the list","in inventory","in stock"]:
                name = name.replace(filler, "").strip()
            if len(name) > 1:
                return {"action": "add", "name": name.title(), "qty": qty, "unit": unit}

    return None


# ── AI IMAGE ANALYSIS (LLaVA via Ollama) ──────────────────
def analyze_image_llava(image_path: str, mode: str = "product", model: str = "llava") -> str:
    """
    Analyzes an image using LLaVA model.
    mode: "product" (Name, Usage, Expiry, Alternatives) or "food" (Ingredients, Recipes)
    """
    if mode == "product":
        prompt = """Analyze this grocery product image. Provide:
1. Product Name: [Name]
2. Common Usage: [Usage]
3. Estimated Expiry Info: [Expiry info if visible, else 'Not visible']
4. Healthier Alternatives: [List 2-3 alternatives]"""
    else:
        prompt = """Analyze this food/dish image. Provide:
1. Likely Ingredients: [List ingredients]
2. Possible Recipes: [Brief recipe names or ideas]"""

    try:
        import base64
        with open(image_path, "rb") as image_file:
            img_str = base64.b64encode(image_file.read()).decode('utf-8')

        payload = {
            "model": model,
            "prompt": prompt,
            "images": [img_str],
            "stream": False
        }
        resp = requests.post(f"{OLLAMA_BASE}/api/generate", json=payload, timeout=300)
        if resp.status_code == 200:
            return resp.json().get("response", "No response from vision model.").strip()
        return f"⚠️ LLaVA error {resp.status_code}. Ensure 'llava' model is pulled."
    except Exception as e:
        return f"⚠️ Vision Analysis Error: {e}"

# ── AI SUGGESTION (Ollama) ────────────────────────────────
def get_ai_suggestion(user_prompt: str, inventory_summary: str, model: str = "mistral") -> str:
    system = f"""You are GroceryMind, a smart grocery assistant for Indian households.
    
Current Inventory: {inventory_summary}

Rules:
- Be practical, friendly, and concise (under 250 words)
- Use ₹ for Indian prices
- Mention Indian platforms (Blinkit, BigBasket, Zepto, Swiggy Instamart) where relevant
- Use bullet points for lists
- Focus on Indian grocery context (dal, sabzi, atta, rice, etc.)
- If the user asks a question about an item (image or text), provide nutritional and usage info.
"""
    payload = {
        "model": model,
        "prompt": f"{system}\n\nUser: {user_prompt}\n\nAssistant:",
        "stream": False,
        "options": {"temperature": 0.7, "num_predict": 512}
    }
    try:
        resp = requests.post(f"{OLLAMA_BASE}/api/generate", json=payload, timeout=120)
        if resp.status_code == 200:
            return resp.json().get("response", "No response.").strip()
        return f"⚠️ Ollama error {resp.status_code}. Run: ollama pull {model}"
    except requests.exceptions.ConnectionError:
        return "⚠️ Ollama not running."
    except Exception as e:
        return f"⚠️ Error: {e}"

def get_quick_suggestions(inventory_items: list) -> list[dict]:
    suggestions = []
    for item in inventory_items:
        if item[4] == "low":
            suggestions.append({"title": f"🔴 Buy {item[1]} urgently", "description": f"Only {item[2]} {item[3]} left.", "type": "warn"})
        elif item[4] == "med":
            suggestions.append({"title": f"⚠️ Restock {item[1]} soon", "description": f"{item[2]} {item[3]} remaining.", "type": "info"})
    if not suggestions:
        suggestions.append({"title": "✅ Inventory looks healthy!", "description": "All items well stocked.", "type": "ok"})
    return suggestions
