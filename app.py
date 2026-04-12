import os
import streamlit as st
import cv2
import requests
import base64
import json
import re
import tempfile
from datetime import datetime
from PIL import Image
import numpy as np
from pyzxing import BarCodeReader  # <-- replaced zxingcpp

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="AI Smart Shopping & Food Assistant",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────
# DARK MODE CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    section[data-testid="stSidebar"] { background-color: #1a1d27; }
    .feature-card {
        background: linear-gradient(135deg, #1e2130, #252840);
        border-radius: 16px; padding: 20px; margin: 10px 0;
        border: 1px solid #2e3250; box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    .result-box {
        background: linear-gradient(135deg, #1a2035, #1e2847);
        border-left: 4px solid #6c63ff; border-radius: 12px;
        padding: 20px; margin: 15px 0; font-size: 16px; line-height: 1.8;
    }
    .success-box {
        background: linear-gradient(135deg, #0d2818, #1a3a2a);
        border-left: 4px solid #00c853; border-radius: 12px;
        padding: 20px; margin: 15px 0;
    }
    .warning-box {
        background: linear-gradient(135deg, #2a1a00, #3a2800);
        border-left: 4px solid #ff9800; border-radius: 12px;
        padding: 20px; margin: 15px 0;
    }
    .barcode-card {
        background: linear-gradient(135deg, #0f1f35, #1a2d4a);
        border: 2px solid #4facfe; border-radius: 16px;
        padding: 25px; margin: 10px 0;
        box-shadow: 0 0 20px rgba(79,172,254,0.2);
    }
    .barcode-result {
        background: linear-gradient(135deg, #0a1628, #0f2040);
        border-left: 4px solid #00f2fe; border-radius: 12px;
        padding: 20px; margin: 15px 0; font-family: monospace;
        font-size: 15px; line-height: 1.9;
    }
    .barcode-badge {
        background: linear-gradient(135deg, #4facfe, #00f2fe);
        color: #000; padding: 4px 14px; border-radius: 20px;
        font-size: 12px; font-weight: 800; display: inline-block; margin: 3px;
    }
    .product-info-card {
        background: linear-gradient(135deg, #1a1f35, #1e2545);
        border: 1px solid #4facfe44; border-radius: 14px;
        padding: 20px; margin: 10px 0;
    }
    .main-header {
        background: linear-gradient(135deg, #6c63ff, #4facfe, #00f2fe);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        font-size: 42px; font-weight: 900; text-align: center; padding: 20px 0;
    }
    .sub-header { color: #8892b0; text-align: center; font-size: 16px; margin-bottom: 30px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #1a1d27; color: #8892b0;
        border-radius: 8px; padding: 10px 20px; font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #6c63ff, #4facfe); color: white;
    }
    .stTextInput input, .stTextArea textarea {
        background-color: #1e2130; color: white;
        border: 1px solid #2e3250; border-radius: 8px;
    }
    .stButton button {
        background: linear-gradient(135deg, #6c63ff, #4facfe);
        color: white; border: none; border-radius: 10px;
        padding: 10px 25px; font-weight: 600; font-size: 15px;
        width: 100%; transition: all 0.3s;
    }
    .stButton button:hover {
        transform: translateY(-2px); box-shadow: 0 5px 20px rgba(108, 99, 255, 0.4);
    }
    .badge {
        background: linear-gradient(135deg, #6c63ff, #4facfe);
        color: white; padding: 4px 12px; border-radius: 20px;
        font-size: 12px; font-weight: 600; display: inline-block; margin: 3px;
    }
    .metric-card {
        background: #1e2130; border-radius: 12px; padding: 15px;
        text-align: center; border: 1px solid #2e3250;
    }
    .metric-number {
        font-size: 36px; font-weight: 900;
        background: linear-gradient(135deg, #6c63ff, #4facfe);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# CONSTANTS & HELPERS
# ─────────────────────────────────────────────
OLLAMA_URL = "http://localhost:11434/api/generate"
DATA_FILE  = "shopping_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"history": [], "budget": {"monthly_limit": 0, "spent": 0}, "wishlist": [], "barcode_history": []}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def image_to_base64(image):
    import io
    buf = io.BytesIO()
    image.save(buf, format="JPEG")
    return base64.b64encode(buf.getvalue()).decode()

def ask_llava(image, question):
    try:
        payload = {"model": "llava", "prompt": question, "images": [image_to_base64(image)], "stream": False}
        r = requests.post(OLLAMA_URL, json=payload, timeout=300)
        return r.json().get("response", "No response") if r.status_code == 200 else f"Error {r.status_code}"
    except requests.exceptions.ConnectionError:
        return "⚠️ Ollama not running. Start with: ollama serve"
    except Exception as e:
        return f"Error: {e}"

def ask_llama(prompt):
    try:
        payload = {"model": "llama3", "prompt": prompt, "stream": False}
        r = requests.post(OLLAMA_URL, json=payload, timeout=300)
        return r.json().get("response", "No response") if r.status_code == 200 else f"Error {r.status_code}"
    except requests.exceptions.ConnectionError:
        return "⚠️ Ollama not running. Start with: ollama serve"
    except Exception as e:
        return f"Error: {e}"

# ─────────────────────────────────────────────
# BARCODE SCANNER USING PYZXING (ORIGINAL JAVA ZXING)
# ─────────────────────────────────────────────
def scan_barcode(image):
    """
    Detect and decode barcodes using pyzxing (wrapper for the original Java ZXing library).
    Supports all common 1D and 2D formats.
    Returns a list of dicts: {type, data, rect (x,y,w,h), method}.
    """
    results = []
    reader = BarCodeReader()
    
    # Save PIL image to a temporary file (pyzxing works with file paths)
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        temp_path = tmp.name
        image.save(temp_path, format="PNG")
    
    try:
        barcodes = reader.decode(temp_path)  # returns list of dicts
        for bc in barcodes:
            # Decode byte strings to normal strings
            fmt = bc.get('format', b'').decode('utf-8', errors='ignore')
            data = bc.get('parsed', bc.get('raw', b'')).decode('utf-8', errors='ignore')
            points = bc.get('points', [])
            
            # Compute bounding rectangle from points (if available)
            x, y, w, h = 0, 0, 0, 0
            if points and len(points) >= 2:
                # For linear barcodes, points are often just two endpoints.
                # We'll compute the min/max x and y, and add a small margin for height.
                xs = [p[0] for p in points]
                ys = [p[1] for p in points]
                x = int(min(xs))
                y = int(min(ys))
                w = int(max(xs) - x)
                h = int(max(ys) - y)
                # If height is too small (linear barcode), set a minimum height for visibility
                if h < 10:
                    h = 20
                    y = max(0, y - 5)  # center the box
            else:
                # No points – set zero rect (will be skipped in drawing)
                x, y, w, h = 0, 0, 0, 0
            
            results.append({
                "type": fmt,
                "data": data,
                "rect": (x, y, w, h),
                "method": "pyzxing"
            })
    except Exception as e:
        # If any error occurs (e.g., Java not installed), return empty list
        pass
    finally:
        # Clean up temporary file
        if os.path.exists(temp_path):
            os.unlink(temp_path)
    
    return results

def draw_barcode_boxes(image, barcode_results):
    """Draw bounding boxes and labels on detected barcodes. Skips boxes with zero width/height."""
    img = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    
    for bc in barcode_results:
        x, y, w, h = bc["rect"]
        if w == 0 or h == 0:
            continue  # skip invalid rectangles
        
        # Draw rectangle
        cv2.rectangle(
            img,
            (x, y),
            (x + w, y + h),
            (0, 255, 0),  # Green
            2
        )
        
        # Create label
        label = f"{bc['type']} : {bc['data']}"
        
        # Draw label background
        (label_w, label_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
        cv2.rectangle(
            img,
            (x, y - label_h - 10),
            (x + label_w + 10, y),
            (0, 255, 0),
            -1  # Filled
        )
        
        # Draw label text
        cv2.putText(
            img,
            label,
            (x + 5, y - 5),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 0, 0),  # Black text on green background
            2
        )
    
    return Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))

def lookup_product_by_barcode(barcode_data, barcode_type):
    """
    Look up product info using Open Food Facts API.
    Works for EAN-13, EAN-8, UPC-A, UPC-E and any numeric barcode.
    Returns dict with product info or {} with an 'error' key.
    """
    info = {}
    barcode_data = barcode_data.strip()

    # Accept all numeric barcodes and EAN/UPC types
    is_numeric   = barcode_data.replace("-", "").isdigit()
    valid_types  = {"EAN13", "EAN8", "UPCA", "UPCE", "EAN_13", "EAN_8",
                    "EAN-13", "EAN-8", "UPC-A", "UPC-E", "CODE128", "UNKNOWN", "OTHER"}
    if not (is_numeric or barcode_type in valid_types):
        info["error"] = "Non-numeric barcode — product lookup not applicable."
        return info

    try:
        headers = {"User-Agent": "AIShoppingAssistant/1.0 (educational project)"}
        url     = f"https://world.openfoodfacts.org/api/v0/product/{barcode_data}.json"
        r       = requests.get(url, timeout=12, headers=headers)

        if r.status_code != 200:
            info["error"] = f"API returned status {r.status_code}. Check your internet connection."
            return info

        d = r.json()

        if d.get("status") != 1:
            info["error"] = (
                f"Product barcode **{barcode_data}** not found in Open Food Facts database. "
                "This product may not be listed yet. Try the AI Analysis button for general info."
            )
            return info

        p  = d["product"]
        nm = p.get("nutriments", {})

        # Helper to get nutriment values
        def _get_nutriment(nm, *keys, default="N/A"):
            """Try multiple key variants for nutriment fields"""
            for k in keys:
                v = nm.get(k)
                if v is not None and v != "":
                    try:
                        return round(float(v), 1)
                    except Exception:
                        if str(v).strip():
                            return str(v)
            return default

        # Product name — try multiple fields
        name = (p.get("product_name_en") or p.get("product_name") or
                p.get("abbreviated_product_name") or "Unknown Product")

        # Allergens — combine all sources
        allergen_parts = []
        if p.get("allergens"):
            raw = p["allergens"].replace("en:", "").replace(",", ", ").strip(", ")
            if raw: allergen_parts.append(raw)
        if p.get("allergens_from_ingredients"):
            allergen_parts.append(p["allergens_from_ingredients"])
        allergens = "; ".join(allergen_parts) if allergen_parts else "None listed"

        info = {
            "name"          : name.strip(),
            "brand"         : p.get("brands", "Unknown"),
            "quantity"      : p.get("quantity", "N/A"),
            "categories"    : (p.get("categories", "") or "")[:120],
            "ingredients"   : (p.get("ingredients_text_en") or
                               p.get("ingredients_text") or "Not available")[:500],
            "nutriscore"    : (p.get("nutriscore_grade") or p.get("nutrition_grade_fr") or "?").upper(),
            "nova_group"    : p.get("nova_group", "N/A"),
            # Nutrition
            "energy_kcal"   : _get_nutriment(nm,
                                "energy-kcal_100g", "energy-kcal",
                                "energy_kcal_100g", "energy_kcal"),
            "fat"           : _get_nutriment(nm, "fat_100g",  "fat"),
            "saturated_fat" : _get_nutriment(nm, "saturated-fat_100g", "saturated_fat_100g"),
            "sugar"         : _get_nutriment(nm, "sugars_100g", "sugars"),
            "carbs"         : _get_nutriment(nm, "carbohydrates_100g", "carbohydrates"),
            "protein"       : _get_nutriment(nm, "proteins_100g", "proteins"),
            "salt"          : _get_nutriment(nm, "salt_100g",  "salt"),
            "fiber"         : _get_nutriment(nm, "fiber_100g", "fiber",
                                "fibers_100g", "fibre_100g"),
            "image_url"     : p.get("image_front_url") or p.get("image_url", ""),
            "countries"     : (p.get("countries") or "")[:80],
            "allergens"     : allergens,
            "labels"        : (p.get("labels") or "")[:100],
            "stores"        : p.get("stores") or "Unknown",
            "barcode"       : barcode_data,
            "source"        : "Open Food Facts",
        }

    except requests.exceptions.ConnectionError:
        info["error"] = (
            "⚠️ **No internet connection.** Cannot reach Open Food Facts database. "
            "Please check your network and try again. "
            "You can still use **AI Analysis** which works offline via Ollama."
        )
    except requests.exceptions.Timeout:
        info["error"] = "⚠️ Request timed out. The server is slow — please try again."
    except Exception as e:
        info["error"] = f"⚠️ Unexpected error: {str(e)}"

    return info

def nutriscore_color(score):
    colors = {"A": "#1db954", "B": "#85bb2f", "C": "#f5c518",
              "D": "#ef8c00", "E": "#e63e11"}
    return colors.get(score.upper(), "#8892b0")

def speak_text(text):
    try:
        from gtts import gTTS
        tts = gTTS(text=text[:500], lang='en', slow=False)
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as f:
            tts.save(f.name)
            return f.name
    except Exception:
        return None

@st.cache_resource
def load_whisper_model():
    try:
        import whisper
        return whisper.load_model("base")
    except Exception as e:
        st.error(f"Failed to load Whisper model: {e}")
        return None

def transcribe_voice(audio_file):
    try:
        # Try Google Web Speech API first (fast, requires no local ffmpeg/model loading)
        import speech_recognition as sr
        r = sr.Recognizer()
        with sr.AudioFile(audio_file) as source:
            audio_data = r.record(source)
            return r.recognize_google(audio_data)
    except Exception as e:
        # Fallback to local offline Whisper
        try:
            model = load_whisper_model()
            if model is None:
                return "Error: Whisper model not loaded."
            result = model.transcribe(audio_file)
            return result["text"]
        except Exception as we:
            if "WinError 2" in str(we):
                return "⚠️ FFmpeg is missing on your computer. Please install FFmpeg to use offline voice recognition, or ensure you have internet access for the cloud fallback."
            return f"Error: {we}"

# ─────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────
if "chat_history"            not in st.session_state: st.session_state.chat_history            = []
if "current_product_context" not in st.session_state: st.session_state.current_product_context = ""
if "current_food_context"    not in st.session_state: st.session_state.current_food_context    = ""
if "data"                    not in st.session_state: st.session_state.data                    = load_data()
if "barcode_results"         not in st.session_state: st.session_state.barcode_results         = []
if "barcode_product_info"    not in st.session_state: st.session_state.barcode_product_info    = {}
if "barcode_ai_analysis"     not in st.session_state: st.session_state.barcode_ai_analysis     = ""
if "voice_key"               not in st.session_state: st.session_state.voice_key               = 0
if "voice_last_tr"           not in st.session_state: st.session_state.voice_last_tr           = None
if "voice_last_ans"          not in st.session_state: st.session_state.voice_last_ans          = None
if "voice_last_audio"        not in st.session_state: st.session_state.voice_last_audio        = None

# Ensure barcode_history key exists
if "barcode_history" not in st.session_state.data:
    st.session_state.data["barcode_history"] = []

# ─────────────────────────────────────────────
# AUTO BARCODE FROM LIVE CAMERA (via query params)
# ─────────────────────────────────────────────
if "auto_bc" in st.query_params and "auto_fmt" in st.query_params:
    bc_val = st.query_params["auto_bc"]
    bc_fmt = st.query_params["auto_fmt"]
    # Map ZXing.js format names to selectbox options
    fmt_map = {
        "UPC_A": "UPCA",
        "EAN_13": "EAN13",
        "EAN_8": "EAN8",
        "CODE_128": "CODE128",
        "CODE_39": "CODE39",
        "QR_CODE": "QR_CODE",
        "DATA_MATRIX": "DATA_MATRIX",
        "PDF_417": "PDF417",
    }
    bc_fmt = fmt_map.get(bc_fmt, bc_fmt)
    st.session_state.bc_prefill = bc_val
    st.session_state.bc_prefill_type = bc_fmt
    st.session_state.bc_lookup_input = bc_val
    st.session_state.bc_lookup_type = bc_fmt
    st.session_state.auto_lookup = True # Auto trigger the lookup
    # Clear query params to avoid reuse on refresh
    st.query_params.clear()
    st.rerun()

# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
st.markdown('<div class="main-header">🛒 AI Smart Shopping & Food Assistant</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Your Complete Food Intelligence Companion — Supermarket + Street Food + Barcode Scanner</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🎯 Navigation")
    st.markdown("---")
    st.markdown("### 📊 Quick Stats")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-number">{len(st.session_state.data['history'])}</div>
            <div style="color:#8892b0;font-size:12px">Scans Done</div>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-number">{len(st.session_state.data.get('barcode_history', []))}</div>
            <div style="color:#8892b0;font-size:12px">Barcodes</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 💰 Monthly Budget")
    budget_limit = st.number_input("Set Budget (₹)", min_value=0,
                                   value=int(st.session_state.data["budget"]["monthly_limit"]), step=500)
    if budget_limit != st.session_state.data["budget"]["monthly_limit"]:
        st.session_state.data["budget"]["monthly_limit"] = budget_limit
        save_data(st.session_state.data)
    spent = st.session_state.data["budget"]["spent"]
    if budget_limit > 0:
        st.progress(min(spent / budget_limit, 1.0))
        remaining = budget_limit - spent
        color = "🟢" if remaining > budget_limit * 0.3 else "🔴"
        st.markdown(f"{color} Spent: ₹{spent} / ₹{budget_limit}")
        st.markdown(f"Remaining: ₹{remaining}")

    st.markdown("---")
    st.markdown("### ⚙️ Settings")
    voice_enabled = st.toggle("🔊 Voice Output", value=True)
    st.markdown("---")
    st.markdown("### 🏷️ Features")
    features = ["📷 Label Scanner", "📦 Barcode Reader", "✍️ List Scanner",
                "🎤 Voice Search", "🔊 Voice Verdict", "🤝 Hands-Free",
                "💡 Worth Buying?", "❤️ Health Score", "⚖️ Compare",
                "🌿 Allergens", "📅 Expiry Check", "💰 Price/Unit",
                "🍜 Dish ID", "🛡️ Food Safety", "💵 Price Guide",
                "🌾 Allergen Q&A", "🍷 Food Pairing", "📖 Dish Story",
                "🔢 Multi-Barcode", "🌐 Product Lookup", "📊 Nutri-Score"]
    for f in features:
        st.markdown(f'<span class="badge">{f}</span>', unsafe_allow_html=True)

# ─────────────────────────────────────────────
# MAIN TABS
# ─────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🛒 Shopping Mode",
    "🍜 Street Food Mode",
    "📦 Barcode Scanner",
    "🎤 Voice Assistant",
    "📊 My Tracker",
    "📋 Shopping History"
])

# ═══════════════════════════════════════════════
# TAB 1 — SHOPPING MODE
# ═══════════════════════════════════════════════
with tab1:
    st.markdown("## 🛒 Shopping Assistant")
    st.markdown("Point your camera at any product — ask anything!")
    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown("### 📷 Scan Product")
        scan_method = st.radio("Input Method", ["📸 Camera", "🖼️ Upload Image"], horizontal=True)
        image = None
        if scan_method == "📸 Camera":
            camera_image = st.camera_input("Point at product")
            if camera_image: image = Image.open(camera_image)
        else:
            uploaded = st.file_uploader("Upload product image", type=["jpg","jpeg","png"])
            if uploaded: image = Image.open(uploaded)
        if image:
            st.image(image, caption="Scanned Product", use_container_width=True)
            st.markdown("#### 📦 Quick Barcode Scan")
            if st.button("🔍 Scan Barcode", key="tab1_barcode"):
                with st.spinner("Scanning..."):
                    bc_list = scan_barcode(image)
                    if bc_list:
                        for bc in bc_list:
                            st.markdown(f'<div class="result-box">📦 <b>{bc["type"]}</b>: {bc["data"]}</div>', unsafe_allow_html=True)
                        st.info("💡 Go to the **📦 Barcode Scanner** tab for full product lookup & AI analysis!")
                    else:
                        st.warning("No barcode detected. Try the dedicated Barcode Scanner tab for enhanced scanning.")

    with col2:
        st.markdown("### 🤖 Ask About This Product")
        if image:
            st.markdown("#### ⚡ Quick Actions")
            qc1, qc2 = st.columns(2)
            with qc1:
                if st.button("💡 Worth Buying?"):
                    with st.spinner("Analysing..."):
                        vision = ask_llava(image, "Describe this product in detail including name, brand, price if visible, ingredients.")
                        st.session_state.current_product_context = vision
                        result = ask_llama(f"Based on: {vision}\n\n1. What is this?\n2. Worth buying?\n3. Pros and cons\n4. Verdict (Buy/Skip/Maybe)")
                        st.markdown(f'<div class="result-box">{result}</div>', unsafe_allow_html=True)
                if st.button("❤️ Health Score"):
                    with st.spinner("..."):
                        vision = ask_llava(image, "Read all ingredients, nutritional info from this label.")
                        result = ask_llama(f"Based on: {vision}\n\n1. Health score /10\n2. Main concerns\n3. Who to avoid\n4. Healthier alternatives")
                        st.markdown(f'<div class="result-box">{result}</div>', unsafe_allow_html=True)
                if st.button("📅 Expiry Check"):
                    with st.spinner("..."):
                        vision = ask_llava(image, "Find expiry/best before/manufacturing date.")
                        result = ask_llama(f"Based on: {vision}\n\n1. Expiry date\n2. Safe now?\n3. Time until expiry\n4. Storage advice\n\nToday: {datetime.now().strftime('%d %B %Y')}")
                        st.markdown(f'<div class="result-box">{result}</div>', unsafe_allow_html=True)
            with qc2:
                if st.button("🌿 Allergens"):
                    with st.spinner("..."):
                        vision = ask_llava(image, "Read all ingredients and allergen warnings.")
                        result = ask_llama(f"Based on: {vision}\n\n1. Allergens\n2. May contain\n3. Safe for veg/vegan/GF/diabetics\n4. Hidden allergens")
                        st.markdown(f'<div class="result-box">{result}</div>', unsafe_allow_html=True)
                if st.button("💰 Price Per Unit"):
                    with st.spinner("..."):
                        vision = ask_llava(image, "Read price, weight/volume/quantity.")
                        result = ask_llama(f"Based on: {vision}\n\n1. Price per gram/ml\n2. Good value?\n3. Better value alternatives")
                        st.markdown(f'<div class="result-box">{result}</div>', unsafe_allow_html=True)
                if st.button("🔄 Alternatives"):
                    with st.spinner("..."):
                        vision = ask_llava(image, "What product is this? Brand, type, price.")
                        result = ask_llama(f"Based on: {vision}\n\n1. 3 cheaper alternatives\n2. 3 healthier alternatives\n3. Best overall and why")
                        st.markdown(f'<div class="result-box">{result}</div>', unsafe_allow_html=True)

            st.markdown("---")
            st.markdown("#### 💬 Ask Anything")
            uq = st.text_input("Type your question...", placeholder="Is this safe for diabetics?")
            if st.button("🚀 Ask") and uq:
                with st.spinner("Thinking..."):
                    if not st.session_state.current_product_context:
                        st.session_state.current_product_context = ask_llava(image, "Describe this product completely.")
                    result = ask_llama(f"Product: {st.session_state.current_product_context}\n\nQuestion: {uq}\n\nAnswer helpfully.")
                    st.markdown(f'<div class="result-box"><b>Q: {uq}</b><br><br>{result}</div>', unsafe_allow_html=True)
                    st.session_state.data["history"].append({"timestamp": datetime.now().strftime("%d/%m/%Y %H:%M"), "type": "Shopping", "question": uq, "answer": result[:200]+"..."})
                    save_data(st.session_state.data)

            st.markdown("---")
            wn = st.text_input("Product name for wishlist")
            if st.button("❤️ Add to Wishlist") and wn:
                st.session_state.data["wishlist"].append({"name": wn, "added": datetime.now().strftime("%d/%m/%Y")})
                save_data(st.session_state.data)
                st.success(f"✅ {wn} added!")
        else:
            st.markdown("""
            <div class="feature-card">
            <h3>👆 How to use Shopping Mode</h3>
            <ol><li>Camera or upload a product image</li><li>Click Quick Actions</li><li>Or type any question</li></ol>
            </div>""", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### ✍️ Handwritten Shopping List Scanner")
    lc1, lc2 = st.columns([1,1])
    with lc1:
        list_image = st.file_uploader("Upload handwritten list", type=["jpg","jpeg","png"], key="list_upload")
        if list_image:
            list_img = Image.open(list_image)
            st.image(list_img, caption="Your List", use_container_width=True)
    with lc2:
        if list_image and st.button("📋 Read My List"):
            with st.spinner("Reading..."):
                result  = ask_llava(list_img, "Read this handwritten shopping list carefully.")
                final   = ask_llama(f"Items: {result}\n\nFor each item: name, buying tips, price range in India (₹).")
                st.markdown(f'<div class="result-box">{final}</div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════
# TAB 2 — STREET FOOD MODE
# ═══════════════════════════════════════════════
with tab2:
    st.markdown("## 🍜 Street Food Judge")
    col1, col2 = st.columns([1,1])
    with col1:
        st.markdown("### 📷 Capture Street Food")
        food_method = st.radio("Input Method", ["📸 Camera","🖼️ Upload Image"], horizontal=True, key="food_radio")
        food_image  = None
        if food_method == "📸 Camera":
            fc = st.camera_input("Point at food", key="food_camera")
            if fc: food_image = Image.open(fc)
        else:
            fu = st.file_uploader("Upload food image", type=["jpg","jpeg","png"], key="food_upload")
            if fu: food_image = Image.open(fu)
        if food_image:
            st.image(food_image, caption="Street Food", use_container_width=True)
    with col2:
        st.markdown("### 🤖 Food Intelligence")
        if food_image:
            fq1, fq2 = st.columns(2)
            with fq1:
                if st.button("🍽️ What Is This?"):
                    with st.spinner("Identifying..."):
                        vision = ask_llava(food_image, "What street food dish is this? Describe in detail.")
                        st.session_state.current_food_context = vision
                        result = ask_llama(f"Based on: {vision}\n\n1. Dish name\n2. Region\n3. Ingredients\n4. How made\n5. Best time to eat")
                        st.markdown(f'<div class="result-box">{result}</div>', unsafe_allow_html=True)
                if st.button("📖 Dish Story"):
                    with st.spinner("..."):
                        if not st.session_state.current_food_context:
                            st.session_state.current_food_context = ask_llava(food_image, "What dish is this?")
                        result = ask_llama(f"For: {st.session_state.current_food_context}\n\n1. Historical origin\n2. Cultural significance\n3. Evolution\n4. Interesting facts\n5. Famous places to eat it")
                        st.markdown(f'<div class="result-box">{result}</div>', unsafe_allow_html=True)
                if st.button("🛡️ Safety Tips"):
                    with st.spinner("..."):
                        vision = ask_llava(food_image, "Describe the food stall/preparation environment.")
                        result = ask_llama(f"Observation: {vision}\n\n1. Safety assessment\n2. Good signs\n3. Caution points\n4. Eat here?\n5. Street food safety tips")
                        st.markdown(f'<div class="result-box">{result}</div>', unsafe_allow_html=True)
            with fq2:
                if st.button("🌾 Allergens Q&A"):
                    with st.spinner("..."):
                        if not st.session_state.current_food_context:
                            st.session_state.current_food_context = ask_llava(food_image, "What dish is this?")
                        result = ask_llama(f"For: {st.session_state.current_food_context}\n\n1. Common allergens\n2. Veg/vegan?\n3. Gluten?\n4. Dairy?\n5. Nuts?\n6. Ask vendor tips")
                        st.markdown(f'<div class="result-box">{result}</div>', unsafe_allow_html=True)
                if st.button("🍷 Best Pairings"):
                    with st.spinner("..."):
                        if not st.session_state.current_food_context:
                            st.session_state.current_food_context = ask_llava(food_image, "What dish is this?")
                        result = ask_llama(f"For: {st.session_state.current_food_context}\n\n1. Best drink\n2. Side dish\n3. Before/after foods\n4. What NOT to pair\n5. Best time of day")
                        st.markdown(f'<div class="result-box">{result}</div>', unsafe_allow_html=True)
                if st.button("💵 Fair Price?"):
                    with st.spinner("..."):
                        if not st.session_state.current_food_context:
                            st.session_state.current_food_context = ask_llava(food_image, "What dish is this?")
                        pp = st.session_state.get("price_paid", 0)
                        result = ask_llama(f"For: {st.session_state.current_food_context}\n\n1. Typical price in Tamil Nadu (₹)\n2. What affects price\n3. Is ₹{pp} fair?\n4. Value tips")
                        st.markdown(f'<div class="result-box">{result}</div>', unsafe_allow_html=True)

            st.session_state.price_paid = st.number_input("I paid (₹)", min_value=0, step=5, key="price_input")
            st.markdown("---")
            fq = st.text_input("Ask anything about this food", placeholder="Is this spicy?", key="food_q")
            if st.button("🚀 Ask Chef AI") and fq:
                with st.spinner("..."):
                    if not st.session_state.current_food_context:
                        st.session_state.current_food_context = ask_llava(food_image, "Describe this food completely.")
                    result = ask_llama(f"Food: {st.session_state.current_food_context}\n\nQuestion: {fq}\n\nAnswer like a local food expert.")
                    st.markdown(f'<div class="result-box"><b>Q: {fq}</b><br><br>{result}</div>', unsafe_allow_html=True)
                    st.session_state.data["history"].append({"timestamp": datetime.now().strftime("%d/%m/%Y %H:%M"), "type": "Street Food", "question": fq, "answer": result[:200]+"..."})
                    save_data(st.session_state.data)
        else:
            st.markdown("""
            <div class="feature-card">
            <h3>👆 How to use Street Food Mode</h3>
            <ol><li>Camera or upload a food image</li><li>Click Quick Actions</li><li>Ask anything!</li></ol>
            </div>""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════
# TAB 3 — BARCODE SCANNER
# ═══════════════════════════════════════════════════════════════════
with tab3:
    st.markdown("## 📦 Universal Barcode Scanner (Powered by Original ZXing)")

    # Choose scanning mode
    scan_mode = st.radio(
        "Choose scanning method:",
        ["📷 Upload / Camera Snap  (pyzxing — most compatible)",
         "🎥 Live Camera  (ZXing.js — continuous)"],
        horizontal=True, key="bc_scan_mode"
    )

    detected_barcode = ""
    detected_type    = "EAN13"

    # MODE 1 — Python pyzxing backend
    if "Upload" in scan_mode:
        st.markdown("""
        <div style="background:#0f1f35;border:1px solid #4facfe44;border-radius:10px;
                    padding:12px;margin-bottom:12px;font-size:13px;color:#8892b0">
        ✅ <b>Most compatible method.</b> Uses the original Java ZXing library via pyzxing.
        Works with virtually all barcode formats, including those that other libraries miss.
        </div>""", unsafe_allow_html=True)

        up_col1, up_col2 = st.columns([1, 1])

        with up_col1:
            bc_input_method = st.radio("Input", ["📁 Upload Image", "📸 Camera Snap"],
                                       horizontal=True, key="bc_input_method")
            bc_image = None
            if bc_input_method == "📁 Upload Image":
                bc_file = st.file_uploader(
                    "Upload barcode image (JPG, PNG, any quality)",
                    type=["jpg","jpeg","png","gif","bmp","webp"], key="bc_file_up"
                )
                if bc_file:
                    bc_image = Image.open(bc_file)
            else:
                bc_snap = st.camera_input("Snap the barcode", key="bc_snap")
                if bc_snap:
                    bc_image = Image.open(bc_snap)

            if bc_image:
                st.image(bc_image, caption="Image to scan", use_container_width=True)

        with up_col2:
            if bc_image:
                if st.button("🔍 Scan with pyzxing", key="bc_opencv_scan",
                             use_container_width=True):
                    with st.spinner("🔍 Scanning..."):
                        results = scan_barcode(bc_image)

                    if results:
                        # Store results in session state
                        st.session_state.barcode_results = results
                        
                        # Auto-fill the lookup field with first result
                        st.session_state.bc_prefill = results[0]['data']
                        st.session_state.bc_prefill_type = results[0]['type']
                        st.session_state.bc_lookup_input = results[0]['data']
                        st.session_state.bc_lookup_type = results[0]['type']
                        st.session_state.auto_lookup = True # Auto trigger the lookup
                        
                        # Show annotated image (boxes may be approximate for linear codes)
                        annotated = draw_barcode_boxes(bc_image, results)
                        st.image(annotated, caption="Detected Barcode", use_container_width=True)
                        
                        # Show results
                        for bc in results:
                            st.markdown(f"""
                            <div class="barcode-result">
                            <span class="barcode-badge">{bc['type']}</span>
                            <span class="barcode-badge" style="background:#667eea">{bc.get('method','pyzxing')}</span>
                            <br><br>
                            <b style="color:#4facfe">Barcode:</b><br>
                            <span style="font-size:24px;font-weight:700;letter-spacing:3px;
                                         color:#00f2fe">{bc['data']}</span>
                            </div>""", unsafe_allow_html=True)

                        if len(results) > 1:
                            st.info(f"Also found: {', '.join(r['data'] for r in results[1:])}")
                    else:
                        st.error("""❌ No barcode detected.
**Try:**
- Upload a clearer / closer image
- Use Camera Snap for a fresh photo
- Use Manual Entry below""")
            else:
                st.markdown("""
                <div class="feature-card">
                <h4>📦 Supported barcode types</h4>
                <p style="color:#8892b0">EAN-13, EAN-8, UPC-A, UPC-E,
                Code128, Code39, QR Code, DataMatrix, PDF417 and more</p>
                <br>
                <h4>💡 Works great with:</h4>
                <ul style="color:#8892b0">
                  <li>Product photos from any angle</li>
                  <li>Screen screenshots</li>
                  <li>Low resolution images</li>
                  <li>Printed barcode stickers</li>
                </ul>
                </div>""", unsafe_allow_html=True)

    # MODE 2 — ZXing.js live camera
    else:
        ZXING_CAM_HTML = """
<!DOCTYPE html><html><head><meta charset="UTF-8">
<style>
* { box-sizing:border-box; margin:0; padding:0; }
body { background:#0e1117; color:#fff; font-family:'Segoe UI',sans-serif; padding:10px; }
#video-wrap {
  position:relative; width:100%; border-radius:12px; overflow:hidden;
  border:2px solid #2e3250; background:#000; max-width:500px;
}
video { width:100%; display:block; }
#scan-line {
  position:absolute; left:0; right:0; height:2px;
  background:linear-gradient(90deg,transparent,#4facfe,transparent);
  animation:scan 2s linear infinite;
}
@keyframes scan{0%{top:10%}50%{top:88%}100%{top:10%}}
#corner-tl,#corner-tr,#corner-bl,#corner-br{position:absolute;width:22px;height:22px;border-color:#4facfe;border-style:solid}
#corner-tl{top:8px;left:8px;border-width:3px 0 0 3px}
#corner-tr{top:8px;right:8px;border-width:3px 3px 0 0}
#corner-bl{bottom:8px;left:8px;border-width:0 0 3px 3px}
#corner-br{bottom:8px;right:8px;border-width:0 3px 3px 0}
.controls{display:flex;gap:8px;margin-top:10px;flex-wrap:wrap}
.btn{padding:9px 18px;border-radius:8px;border:none;cursor:pointer;font-weight:600;font-size:13px;transition:all .2s}
.btn-primary{background:linear-gradient(135deg,#6c63ff,#4facfe);color:#fff}
.btn-secondary{background:#1e2130;color:#8892b0;border:1px solid #2e3250}
.btn:disabled{opacity:.4;cursor:not-allowed}
.status{padding:9px 14px;border-radius:8px;font-size:13px;margin-top:8px}
.scanning{background:#0f2040;border:1px solid #4facfe;color:#4facfe}
.success {background:#0d2818;border:1px solid #00c853;color:#00c853}
.error   {background:#2a1a00;border:1px solid #ff9800;color:#ff9800}
.idle    {background:#1a1d27;border:1px solid #2e3250;color:#8892b0}
.result-box{background:linear-gradient(135deg,#0a1628,#0f2040);border-left:4px solid #00f2fe;
  border-radius:10px;padding:16px;margin-top:12px;display:none}
.result-box.show{display:block}
.result-num{font-size:22px;font-weight:700;color:#00f2fe;letter-spacing:3px;word-break:break-all;cursor:pointer}
.badge{background:linear-gradient(135deg,#4facfe,#00f2fe);color:#000;padding:3px 12px;
  border-radius:20px;font-size:11px;font-weight:800;margin-top:6px;display:inline-block}
#copy-hint{color:#00c853;font-size:12px;margin-top:4px;min-height:16px}
</style>
</head>
<body>
<div id="video-wrap">
  <video id="video" autoplay playsinline muted></video>
  <div id="scan-line"></div>
  <div id="corner-tl"></div><div id="corner-tr"></div>
  <div id="corner-bl"></div><div id="corner-br"></div>
</div>
<div class="controls">
  <button class="btn btn-primary"  id="start-btn" onclick="startCam()">▶ Start Camera</button>
  <button class="btn btn-secondary" id="stop-btn"  onclick="stopCam()" disabled>⏹ Stop</button>
  <button class="btn btn-secondary" id="flip-btn"  onclick="flipCam()" disabled>🔄 Flip</button>
</div>
<div class="status idle" id="status">Click "Start Camera" to begin</div>

<div class="result-box" id="result-box">
  <div style="font-size:11px;color:#8892b0;letter-spacing:1px">✅ BARCODE DETECTED</div>
  <div class="result-num" id="result-num" onclick="copyIt()" title="Click to copy">—</div>
  <div class="badge" id="result-fmt">—</div>
  <div id="copy-hint"></div>
  <button class="btn btn-primary" onclick="copyIt()" style="margin-top:10px;width:100%">
    📋 Copy Barcode Number
  </button>
  <button class="btn btn-primary" onclick="useBarcode()" style="margin-top:10px;width:100%">
    🔍 Use This Barcode
  </button>
  <div style="background:#0a1628;border-radius:6px;padding:8px;margin-top:8px;font-size:12px;color:#8892b0">
    👇 After clicking "Use This Barcode", the number will appear in the lookup field below.
  </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/@zxing/library@0.18.6/umd/index.min.js"></script>
<script>
const reader = new ZXing.BrowserMultiFormatReader();
let stream = null, scanning = false, cameras = [], camIdx = 0, lastVal = null;
let lastBarcode = '';
let lastFormat = '';

async function startCam() {
  setStatus('scanning','🔍 Starting camera...');
  try {
    // Permission first
    const tmp = await navigator.mediaDevices.getUserMedia({video:true});
    tmp.getTracks().forEach(t=>t.stop());
    // Enumerate
    const all = await navigator.mediaDevices.enumerateDevices();
    cameras = all.filter(d=>d.kind==='videoinput');
    if (!cameras.length){setStatus('error','⚠️ No camera found');return;}
    // Prefer back camera
    const backIdx = cameras.findIndex(c=>
      /back|rear|environment/i.test(c.label));
    if(backIdx>=0) camIdx=backIdx;
    document.getElementById('stop-btn').disabled=false;
    document.getElementById('flip-btn').disabled=cameras.length<2;
    document.getElementById('start-btn').disabled=true;
    await openStream(cameras[camIdx].deviceId);
  } catch(e) {
    if(e.name==='NotAllowedError')
      setStatus('error','⚠️ Camera permission denied. Allow in browser settings.');
    else setStatus('error','⚠️ '+e.message);
  }
}

async function openStream(deviceId){
  if(stream) stream.getTracks().forEach(t=>t.stop());
  stream = await navigator.mediaDevices.getUserMedia({
    video:{deviceId:{exact:deviceId},width:{ideal:1280},height:{ideal:720}}
  });
  const v=document.getElementById('video');
  v.srcObject=stream; await v.play();
  scanning=true;
  setStatus('scanning','🔍 Scanning… hold barcode steady in frame');
  scanLoop();
}

async function scanLoop(){
  const v=document.getElementById('video');
  const c=document.createElement('canvas'); const ctx=c.getContext('2d');
  const tick=async()=>{
    if(!scanning||v.readyState<2){if(scanning)requestAnimationFrame(tick);return;}
    c.width=v.videoWidth; c.height=v.videoHeight;
    ctx.drawImage(v,0,0);
    try{
      const r=await reader.decodeFromCanvas(c);
      if(r&&r.getText()!==lastVal){
        lastVal=r.getText();
        showResult(r.getText(), r.getBarcodeFormat());
        setStatus('success','✅ Barcode detected! Automatically looking up product...');
        document.getElementById('video-wrap').style.borderColor='#00c853';
        setTimeout(()=>document.getElementById('video-wrap').style.borderColor='#2e3250',1000);
        setTimeout(() => useBarcode(), 800); // Auto-redirect after a brief moment
      }
    }catch(e){}
    if(scanning)requestAnimationFrame(tick);
  };
  requestAnimationFrame(tick);
}

function stopCam(){
  scanning=false;
  if(stream){stream.getTracks().forEach(t=>t.stop());stream=null;}
  document.getElementById('video').srcObject=null;
  document.getElementById('start-btn').disabled=false;
  document.getElementById('stop-btn').disabled=true;
  document.getElementById('flip-btn').disabled=true;
  setStatus('idle','Camera stopped.');
}

function flipCam(){
  camIdx=(camIdx+1)%cameras.length;
  openStream(cameras[camIdx].deviceId);
}

function showResult(val,fmt){
  lastBarcode = val;
  lastFormat = fmt;
  document.getElementById('result-num').textContent = val;
  document.getElementById('result-fmt').textContent = String(fmt).replace('_',' ');
  document.getElementById('result-box').classList.add('show');
}

function copyIt(){
  const val=document.getElementById('result-num').textContent;
  navigator.clipboard.writeText(val).then(()=>{
    document.getElementById('copy-hint').textContent='✅ Copied to clipboard!';
    setTimeout(()=>document.getElementById('copy-hint').textContent='',2500);
  }).catch(()=>{
    const r=document.createRange();
    r.selectNode(document.getElementById('result-num'));
    window.getSelection().removeAllRanges();
    window.getSelection().addRange(r);
    document.execCommand('copy');
    document.getElementById('copy-hint').textContent='✅ Copied!';
  });
}

function useBarcode() {
  if (lastBarcode) {
    window.location.search = `?auto_bc=${encodeURIComponent(lastBarcode)}&auto_fmt=${encodeURIComponent(lastFormat)}`;
  }
}

function setStatus(cls,msg){
  const el=document.getElementById('status');
  el.className='status '+cls; el.textContent=msg;
}
</script>
</body></html>"""
        st.components.v1.html(ZXING_CAM_HTML, height=600, scrolling=False)

    # COMMON — Manual entry + Lookup
    st.markdown("---")
    st.markdown("### 🔍 Step 2 — Barcode Lookup & AI Analysis")

    # Pre-fill from detection
    prefill_val  = st.session_state.get("bc_prefill", "")
    prefill_type = st.session_state.get("bc_prefill_type", "EAN13")

    lk_col1, lk_col2 = st.columns([3, 1])
    with lk_col1:
        bc_lookup_val = st.text_input(
            "Barcode number (auto-filled after pyzxing scan, or paste from camera)",
            value=prefill_val,
            placeholder="e.g. 8901063025332",
            key="bc_lookup_input"
        )
    with lk_col2:
        type_options = ["EAN13","EAN8","UPCA","UPCE","QR_CODE","CODE128","CODE39","OTHER"]
        default_idx  = type_options.index(prefill_type) if prefill_type in type_options else 0
        bc_lookup_type = st.selectbox("Format", type_options,
                                      index=default_idx, key="bc_lookup_type")

    # Manual entry
    with st.expander("⌨️ Or enter barcode manually"):
        manual_val = st.text_input("Type barcode number", placeholder="e.g. 8901063025332",
                                   key="bc_manual_val")
        if st.button("Use this barcode", key="bc_use_manual"):
            if manual_val.strip():
                st.session_state.bc_prefill = manual_val.strip()
                st.rerun()

    do_lookup = st.button("🚀 Lookup Product + AI Analysis", key="bc_lookup_btn", use_container_width=True)
    if st.session_state.get("auto_lookup", False):
        do_lookup = True
        st.session_state.auto_lookup = False

    if do_lookup:

        final_bc = (bc_lookup_val or "").strip().replace(" ", "")
        if not final_bc:
            st.warning("⚠️ Please enter or scan a barcode first.")
        else:
            st.session_state.barcode_results      = [{"type": bc_lookup_type,
                                                       "data": final_bc,
                                                       "rect": None,
                                                       "method": "lookup"}]
            st.session_state.barcode_product_info = {}
            st.session_state.barcode_ai_analysis  = ""

            # Product DB lookup
            with st.spinner("🌐 Looking up product database..."):
                info = lookup_product_by_barcode(final_bc, bc_lookup_type)
                st.session_state.barcode_product_info = info

            if info.get("error"):
                st.warning(info["error"])
            elif info:
                nfields      = ["energy_kcal","fat","sugar","protein","salt","carbs"]
                has_nutrition = any(info.get(f) not in ["N/A", None] for f in nfields)
                suffix = " ✅ with nutrition" if has_nutrition else " (nutrition estimated by AI)"
                st.success(f"✅ Found: **{info.get('name')}** by {info.get('brand')}{suffix}")
            else:
                st.info("Product not found in database — AI will analyse from barcode prefix.")

            # AI Analysis
            with st.spinner("🤖 AI analysing..."):
                info2 = {k: v for k, v in info.items() if k != "error"} if info else {}
                nfields      = ["energy_kcal","fat","sugar","protein","salt","carbs"]
                has_nutrition = any(info2.get(f) not in ["N/A", None] for f in nfields)
                nutrition_note = ("\n⚠️ Nutrition values are missing from the database — "
                                  "ESTIMATE typical values for this product type based on "
                                  "its ingredients and category.") if not has_nutrition else ""

                if info2:
                    prompt = f"""Product: {info2.get('name')} by {info2.get('brand')} ({info2.get('quantity','')})
Category: {info2.get('categories','')}
Ingredients: {info2.get('ingredients','Not available')}
Nutri-Score: {info2.get('nutriscore','?')} | NOVA: {info2.get('nova_group','?')}
Allergens: {info2.get('allergens','?')}
Nutrition/100g — Energy:{info2.get('energy_kcal','?')}kcal Fat:{info2.get('fat','?')}g Sugar:{info2.get('sugar','?')}g Protein:{info2.get('protein','?')}g Salt:{info2.get('salt','?')}g{nutrition_note}

Provide:
1. 🏥 Health Score /10 with clear reasoning
2. ⚠️ Top 3 ingredient/nutrition concerns
3. 📊 Estimated nutrition per 100g (if missing above)
4. 👶 Safe for children / diabetics / pregnant women?
5. 💰 Worth buying? Value for money?
6. 🥗 3 healthier Indian alternatives
7. ✅ One-line verdict"""
                else:
                    pfx = final_bc[:3]
                    prompt = f"""Barcode: {final_bc} (EAN-13 prefix: {pfx})
1. 🌍 Country/company from prefix {pfx}
2. 📦 Likely product type
3. 💡 General buying advice
4. 🔍 What to check on the label"""

                result = ask_llama(prompt)
                st.session_state.barcode_ai_analysis = result

            # Save history
            st.session_state.data["barcode_history"].append({
                "timestamp"   : datetime.now().strftime("%d/%m/%Y %H:%M"),
                "barcode"     : final_bc,
                "type"        : bc_lookup_type,
                "product_name": info2.get("name","Unknown") if info2 else "Unknown",
                "brand"       : info2.get("brand","") if info2 else ""
            })
            save_data(st.session_state.data)
            # Clear prefill
            st.session_state.bc_prefill = ""

    # Product Info Display
    info = st.session_state.barcode_product_info
    if info and not info.get("error"):
        st.markdown("---")
        st.markdown("## 🌐 Product Information")
        pi1, pi2, pi3 = st.columns([1.5, 1, 1])

        with pi1:
            st.markdown(f"""
            <div class="product-info-card">
            <h3 style="color:#4facfe">{info.get('name','Unknown')}</h3>
            <p><b>Brand:</b> {info.get('brand','N/A')}</p>
            <p><b>Quantity:</b> {info.get('quantity','N/A')}</p>
            <p><b>Categories:</b> {info.get('categories','N/A')}</p>
            <p><b>Countries:</b> {info.get('countries','N/A')}</p>
            <p><b>Labels:</b> {info.get('labels','N/A')}</p>
            <p><b>Barcode:</b> <code>{info.get('barcode','N/A')}</code></p>
            <small style="color:#8892b0">Source: Open Food Facts</small>
            </div>""", unsafe_allow_html=True)

        with pi2:
            ns  = info.get('nutriscore','?')
            nv  = info.get('nova_group','N/A')
            nc  = nutriscore_color(ns)
            nvc = {"1":"#1db954","2":"#85bb2f","3":"#ef8c00","4":"#e63e11"}.get(str(nv),"#8892b0")
            st.markdown(f"""
            <div class="product-info-card" style="text-align:center">
            <h4 style="color:#8892b0">Nutri-Score</h4>
            <div style="font-size:64px;font-weight:900;color:{nc}">{ns}</div>
            <small style="color:#8892b0">A=Best · E=Worst</small><br><br>
            <h4 style="color:#8892b0">NOVA Group</h4>
            <div style="font-size:48px;font-weight:900;color:{nvc}">{nv}</div>
            <small style="color:#8892b0">1=Unprocessed · 4=Ultra-processed</small>
            </div>""", unsafe_allow_html=True)

        with pi3:
            nfields   = ["energy_kcal","fat","sugar","protein","salt","carbs"]
            all_na    = all(info.get(f) in ["N/A", None] for f in nfields)
            na_badge  = '<p style="color:#ff9800;font-size:11px;margin-top:6px">⚠️ Not in database — see AI Analysis for estimates</p>' if all_na else ""
            st.markdown(f"""
            <div class="product-info-card">
            <h4 style="color:#4facfe">📊 Nutrition per 100g</h4>
            <table width="100%" style="border-collapse:collapse">
            <tr style="border-bottom:1px solid #2e3250"><td style="padding:4px">🔥 Energy</td><td><b>{info.get('energy_kcal','—')} kcal</b></td></tr>
            <tr style="border-bottom:1px solid #2e3250"><td style="padding:4px">🧈 Fat</td><td><b>{info.get('fat','—')}g</b></td></tr>
            <tr style="border-bottom:1px solid #2e3250"><td style="padding:4px">&nbsp;↳ Sat.</td><td><b>{info.get('saturated_fat','—')}g</b></td></tr>
            <tr style="border-bottom:1px solid #2e3250"><td style="padding:4px">🌾 Carbs</td><td><b>{info.get('carbs','—')}g</b></td></tr>
            <tr style="border-bottom:1px solid #2e3250"><td style="padding:4px">🍬 Sugar</td><td><b>{info.get('sugar','—')}g</b></td></tr>
            <tr style="border-bottom:1px solid #2e3250"><td style="padding:4px">💪 Protein</td><td><b>{info.get('protein','—')}g</b></td></tr>
            <tr style="border-bottom:1px solid #2e3250"><td style="padding:4px">🌿 Fiber</td><td><b>{info.get('fiber','—')}g</b></td></tr>
            <tr><td style="padding:4px">🧂 Salt</td><td><b>{info.get('salt','—')}g</b></td></tr>
            </table>
            {na_badge}
            <br><h4 style="color:#ff6b6b">⚠️ Allergens</h4>
            <p style="color:#ff9999">{info.get('allergens','None listed')}</p>
            </div>""", unsafe_allow_html=True)

        if info.get("ingredients"):
            with st.expander("🧪 Full Ingredients List"):
                st.markdown(f'<div class="barcode-result">{info["ingredients"]}</div>',
                            unsafe_allow_html=True)

    # AI Analysis Display
    if st.session_state.barcode_ai_analysis:
        st.markdown("---")
        st.markdown("## 🤖 AI Health Analysis")
        st.markdown(f'<div class="result-box">{st.session_state.barcode_ai_analysis}</div>',
                    unsafe_allow_html=True)

    # Q&A Section
    if st.session_state.barcode_results or st.session_state.barcode_product_info:
        st.markdown("---")
        st.markdown("### 💬 Ask Anything About This Product")
        bc_q = st.text_input("Your question...",
                             placeholder="Is this safe for children? Is it vegan?",
                             key="bc_question")
        if st.button("🚀 Ask AI", key="bc_ask"):
            if bc_q:
                with st.spinner("Thinking..."):
                    i2  = st.session_state.barcode_product_info
                    ctx = (f"Product: {i2.get('name')} by {i2.get('brand')}. "
                           f"Ingredients: {i2.get('ingredients')}. "
                           f"Allergens: {i2.get('allergens')}.")  \
                          if i2 and not i2.get("error") \
                          else f"Barcode: {st.session_state.barcode_results[0]['data']}"
                    res = ask_llama(f"Product: {ctx}\n\nQuestion: {bc_q}\n\nAnswer clearly.")
                    st.markdown(f'<div class="result-box"><b>Q: {bc_q}</b><br><br>{res}</div>',
                                unsafe_allow_html=True)

    # Scan History
    if st.session_state.data.get("barcode_history"):
        st.markdown("---")
        st.markdown("### 📋 Recent Scans")
        h1, h2 = st.columns([3,1])
        with h2:
            if st.button("🗑️ Clear", key="clr_bc_hist"):
                st.session_state.data["barcode_history"] = []
                save_data(st.session_state.data); st.rerun()
        for entry in reversed(st.session_state.data["barcode_history"][-10:]):
            st.markdown(f"""
            <div class="feature-card" style="padding:10px">
            <small style="color:#8892b0">📦 {entry['timestamp']} — {entry['type']}</small><br>
            <b>{entry.get('product_name','Unknown')}</b> — {entry.get('brand','')}<br>
            <code style="color:#4facfe">{entry['barcode']}</code>
            </div>""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════
# TAB 4 — VOICE ASSISTANT
# ═══════════════════════════════════════════════
with tab4:
    st.markdown("## 🎤 Voice Assistant")
    col1, col2 = st.columns([1,1])
    with col1:
        st.markdown("### 🎙️ Live Speech & Upload")
        st.markdown("""
        <div class="feature-card">
        <h4>How Voice Works:</h4>
        <ol><li>Click <b>'Record'</b> or upload audio</li><li>AI transcribes it automatically</li><li>Get instant food/shopping intelligence</li></ol>
        </div>""", unsafe_allow_html=True)
        
        # Live Recording Widget
        live_audio = st.audio_input("Record your question live", key=f"audio_input_{st.session_state.voice_key}")
        
        # File Upload Widget (as fallback)
        uploaded_audio = st.file_uploader("Or upload audio (WAV/MP3)", type=["wav","mp3","m4a"], key=f"audio_upload_{st.session_state.voice_key}")
        
        audio_to_process = live_audio if live_audio else uploaded_audio
        
        if audio_to_process:
            if st.button("🎤 Transcribe & Answer", key="voice_transcribe_btn", use_container_width=True):
                with st.spinner("🧠 Processing your voice..."):
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
                        f.write(audio_to_process.read())
                        temp_path = f.name
                    
                    transcribed = transcribe_voice(temp_path)
                    
                    # Clean up temp file
                    if os.path.exists(temp_path): os.unlink(temp_path)
                    
                    if transcribed:
                        answer = ask_llama(f"Answer this shopping/food question: {transcribed}")
                        
                        st.session_state.voice_last_tr = transcribed
                        st.session_state.voice_last_ans = answer
                        
                        if voice_enabled:
                            ap = speak_text(answer)
                            st.session_state.voice_last_audio = ap
                        else:
                            st.session_state.voice_last_audio = None
                            
                        # Reset the widget keys to clear the audio player and show the record button again
                        st.session_state.voice_key += 1
                        st.rerun()

        # Render the last result
        if st.session_state.voice_last_tr:
            st.markdown(f'<div class="success-box"><b>🎤 You said:</b><br>{st.session_state.voice_last_tr}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="result-box">{st.session_state.voice_last_ans}</div>', unsafe_allow_html=True)
            if st.session_state.voice_last_audio:
                st.audio(st.session_state.voice_last_audio)
                st.success("🔊 Press play to hear the answer!")

    with col2:
        st.markdown("### 💬 Hands-Free Text Mode")
        hq = st.text_area("Your question", placeholder="Is Maggi healthy? What is dosa?", height=100)
        if st.button("🚀 Get Answer + Speak"):
            if hq:
                with st.spinner("..."):
                    answer = ask_llama(f"Answer helpfully: {hq}")
                    st.markdown(f'<div class="result-box">{answer}</div>', unsafe_allow_html=True)
                    if voice_enabled:
                        ap = speak_text(answer)
                        if ap: st.audio(ap); st.success("🔊 Press play!")
        st.markdown("---")
        st.markdown("### 💡 Try These")
        for q in ["What to look for buying olive oil?","Is biryani healthy daily?",
                  "How to check if an egg is fresh?","Is Maggi safe for children?"]:
            if st.button(f"💬 {q}", key=f"samp_{q}"):
                with st.spinner("..."):
                    answer = ask_llama(f"Answer: {q}")
                    st.markdown(f'<div class="result-box">{answer}</div>', unsafe_allow_html=True)
                    if voice_enabled:
                        ap = speak_text(answer)
                        if ap: st.audio(ap)

# ═══════════════════════════════════════════════
# TAB 5 — TRACKER
# ═══════════════════════════════════════════════
with tab5:
    st.markdown("## 📊 My Shopping Tracker")
    col1, col2 = st.columns([1,1])
    with col1:
        st.markdown("### 💰 Budget Tracker")
        add_expense   = st.number_input("Add expense (₹)", min_value=0, step=10)
        expense_note  = st.text_input("Note (e.g. Groceries)")
        if st.button("➕ Add Expense"):
            if add_expense > 0:
                st.session_state.data["budget"]["spent"] += add_expense
                st.session_state.data["history"].append({"timestamp": datetime.now().strftime("%d/%m/%Y %H:%M"), "type": "Expense", "question": expense_note or "Expense", "answer": f"₹{add_expense}"})
                save_data(st.session_state.data)
                limit = st.session_state.data["budget"]["monthly_limit"]
                spent = st.session_state.data["budget"]["spent"]
                if limit > 0 and spent > limit * 0.9:
                    st.warning(f"⚠️ Alert! ₹{spent} of ₹{limit} spent!")
                else:
                    st.success(f"✅ ₹{add_expense} added. Total: ₹{spent}")
        if st.button("🔄 Reset Budget"):
            st.session_state.data["budget"]["spent"] = 0
            save_data(st.session_state.data)
            st.success("Budget reset!")
    with col2:
        st.markdown("### ❤️ My Wishlist")
        if st.session_state.data["wishlist"]:
            for i, item in enumerate(st.session_state.data["wishlist"]):
                wc1, wc2 = st.columns([3,1])
                with wc1: st.markdown(f"• **{item['name']}** — {item['added']}")
                with wc2:
                    if st.button("✅", key=f"wish_{i}"):
                        st.session_state.data["wishlist"].pop(i); save_data(st.session_state.data); st.rerun()
        else:
            st.markdown('<div class="feature-card"><p style="color:#8892b0">Wishlist empty. Add from Shopping Mode!</p></div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════
# TAB 6 — HISTORY
# ═══════════════════════════════════════════════
with tab6:
    st.markdown("## 📋 Shopping & Food History")
    if st.session_state.data["history"]:
        if st.button("🗑️ Clear History"):
            st.session_state.data["history"] = []; save_data(st.session_state.data); st.rerun()
        for item in reversed(st.session_state.data["history"][-20:]):
            emoji = "🛒" if item["type"]=="Shopping" else "🍜" if item["type"]=="Street Food" else "💰"
            st.markdown(f"""
            <div class="feature-card">
            <small style="color:#8892b0">{emoji} {item['type']} — {item['timestamp']}</small><br>
            <b>{item['question']}</b><br>
            <small style="color:#a0aec0">{item['answer']}</small>
            </div>""", unsafe_allow_html=True)
    else:
        st.markdown('<div class="feature-card"><p style="color:#8892b0;text-align:center">No history yet. Start scanning!</p></div>', unsafe_allow_html=True)