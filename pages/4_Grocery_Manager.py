import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
from datetime import datetime
from collections import Counter

from inventory import (
    init_db, add_item, get_all_items, delete_item,
    get_low_items, get_frequent_items, ai_add_to_inventory,
    get_item_by_name, update_item_qty, guess_category, CAT_ICONS,
    get_db_cart, delete_from_db_cart, clear_db_cart
)
from ai_logic import get_ai_suggestion, check_ollama_status, parse_inventory_intent
from price_checker import compare_prices, POPULAR_ITEMS
from automation import simulate_add_to_cart, simulate_order, add_single_item_to_cart
from telegram_utils import automate_telegram_alerts

# ── PAGE CONFIG (Handled by app.py) ───────────────────────────────────────────
# st.set_page_config(page_title="GroceryMind AI", page_icon="🛒", layout="wide", initial_sidebar_state="collapsed")

# ── CSS ───────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=Outfit:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap');
html,body,[class*="css"]{font-family:'Outfit',sans-serif;}
#MainMenu,footer,header{visibility:hidden;}
.block-container{padding-top:1rem!important;}
.stApp{background:#0d1117;color:#e6edf3;}
.hero-title{font-family:'DM Serif Display',serif;font-size:3.2rem;line-height:1.1;letter-spacing:-1.5px;color:#e6edf3;}
.hero-title em{color:#00e5a0;font-style:italic;}
.hero-badge{display:inline-block;background:rgba(0,229,160,0.08);border:1px solid rgba(0,229,160,0.25);border-radius:100px;padding:0.3rem 1rem;font-size:0.72rem;color:#00e5a0;letter-spacing:1.5px;text-transform:uppercase;font-weight:600;margin-bottom:1.2rem;}
.gm-card{background:#1e2733;border:1px solid #2a3441;border-radius:12px;padding:1.2rem;margin-bottom:0.75rem;}
.gm-card-accent{border-left:3px solid #00e5a0;}
.gm-card-warn{border-left:3px solid #ff6b6b;}
.gm-card-info{border-left:3px solid #ffd166;}
.gm-card-voice{border:2px solid #00e5a0;background:rgba(0,229,160,0.04);}
.section-title{font-family:'DM Serif Display',serif;font-size:1.8rem;letter-spacing:-0.5px;color:#e6edf3;margin-bottom:0.2rem;}
.section-sub{color:#7d8590;font-size:0.85rem;margin-bottom:1.2rem;}
.badge-ok {background:#00e5a010;color:#00e5a0;border:1px solid #00e5a030;border-radius:100px;padding:0.2rem 0.6rem;font-size:0.7rem;font-weight:700;}
.badge-med{background:#ffd16610;color:#ffd166;border:1px solid #ffd16630;border-radius:100px;padding:0.2rem 0.6rem;font-size:0.7rem;font-weight:700;}
.badge-low{background:#ff6b6b10;color:#ff6b6b;border:1px solid #ff6b6b30;border-radius:100px;padding:0.2rem 0.6rem;font-size:0.7rem;font-weight:700;}
.badge-best{background:#00e5a015;color:#00e5a0;border-radius:4px;padding:0.15rem 0.45rem;font-size:0.68rem;font-weight:700;margin-left:0.4rem;}
.inv-row{display:flex;align-items:center;gap:1rem;background:#1c2330;border:1px solid #2a3441;border-radius:10px;padding:0.9rem 1.1rem;margin-bottom:0.5rem;}
.ai-box{background:#1e2733;border:1px solid #2a3441;border-radius:12px;padding:1.5rem;line-height:1.75;font-size:0.92rem;color:#e6edf3;white-space:pre-wrap;}
.action-toast{background:rgba(0,229,160,0.08);border:1px solid rgba(0,229,160,0.3);border-radius:10px;padding:1rem 1.2rem;margin-bottom:1rem;color:#e6edf3;}
.action-toast .at-title{color:#00e5a0;font-weight:700;font-size:0.95rem;margin-bottom:0.3rem;}
.action-toast .at-body{font-size:0.84rem;color:#b0bec5;}
.sim-log{background:#0d1117;border:1px solid #2a3441;border-radius:8px;padding:1rem;font-family:'DM Mono',monospace;font-size:0.78rem;line-height:1.8;}
.log-ok{color:#00e5a0;} .log-info{color:#4ecdc4;} .log-warn{color:#ffd166;}
.ollama-ok  {background:rgba(0,229,160,0.08);border:1px solid rgba(0,229,160,0.25);border-radius:8px;padding:0.5rem 1rem;color:#00e5a0;font-size:0.82rem;}
.ollama-fail{background:rgba(255,107,107,0.08);border:1px solid rgba(255,107,107,0.25);border-radius:8px;padding:0.5rem 1rem;color:#ff6b6b;font-size:0.82rem;}
.freq-chip{display:inline-flex;align-items:center;gap:0.4rem;background:#1c2330;border:1px solid #2a3441;border-radius:8px;padding:0.5rem 0.9rem;cursor:pointer;transition:border-color 0.2s;font-size:0.83rem;margin:0.25rem;}
.freq-chip:hover{border-color:#00e5a0;color:#00e5a0;}
.voice-pulse{display:inline-block;width:10px;height:10px;background:#ff6b6b;border-radius:50%;animation:vpulse 0.8s ease-in-out infinite;}
@keyframes vpulse{0%,100%{transform:scale(1);opacity:1;}50%{transform:scale(1.5);opacity:0.6;}}
.stTextInput>div>div>input,.stNumberInput>div>div>input,.stSelectbox>div>div{background:#1c2330!important;border:1px solid #2a3441!important;border-radius:8px!important;color:#e6edf3!important;}
.stTextArea textarea{background:#1c2330!important;border:1px solid #2a3441!important;border-radius:8px!important;color:#e6edf3!important;font-family:'Outfit',sans-serif!important;}
.stButton>button{background:#00e5a0!important;color:#0d1117!important;border:none!important;border-radius:8px!important;font-weight:700!important;font-family:'Outfit',sans-serif!important;}
.stButton>button:hover{background:#00ffb3!important;}
div[data-testid="metric-container"]{background:#1e2733;border:1px solid #2a3441;border-radius:12px;padding:1rem;}
div[data-testid="metric-container"] label{color:#7d8590!important;}
div[data-testid="metric-container"] div[data-testid="metric-value"]{color:#00e5a0!important;font-family:'DM Serif Display',serif!important;}
</style>
""", unsafe_allow_html=True)

# ── VOICE INPUT COMPONENT ─────────────────────────────────
# Uses browser's built-in Web Speech API — works in Chrome/Edge, no install needed
VOICE_JS = """
<div id="voice-widget" style="margin:0;">
  <button id="voiceBtn" onclick="toggleVoice()" style="
    background:#1e2733;border:1px solid #2a3441;border-radius:8px;
    padding:0.6rem 1.1rem;color:#e6edf3;cursor:pointer;font-size:0.88rem;
    font-family:Outfit,sans-serif;display:flex;align-items:center;gap:0.5rem;
    transition:all 0.2s;width:100%;">
    <span id="voiceIcon">🎤</span>
    <span id="voiceLabel">Click to Speak</span>
  </button>
  <div id="voiceStatus" style="margin-top:0.5rem;font-size:0.75rem;color:#7d8590;min-height:1.2rem;"></div>
</div>

<script>
let recognition = null;
let isListening = false;

function toggleVoice() {
  if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
    document.getElementById('voiceStatus').textContent = '⚠️ Voice not supported in this browser. Use Chrome or Edge.';
    document.getElementById('voiceStatus').style.color = '#ff6b6b';
    return;
  }
  isListening ? stopVoice() : startVoice();
}

function startVoice() {
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  recognition = new SR();
  recognition.lang = 'en-IN';
  recognition.interimResults = true;
  recognition.continuous = false;

  const btn = document.getElementById('voiceBtn');
  const icon = document.getElementById('voiceIcon');
  const label = document.getElementById('voiceLabel');
  const status = document.getElementById('voiceStatus');

  btn.style.borderColor = '#ff6b6b';
  btn.style.background = 'rgba(255,107,107,0.08)';
  icon.innerHTML = '<span style="display:inline-block;width:10px;height:10px;background:#ff6b6b;border-radius:50%;animation:vpulse 0.8s ease-in-out infinite;"></span>';
  label.textContent = 'Listening… speak now';
  status.textContent = '';
  isListening = true;

  recognition.onresult = (e) => {
    let transcript = '';
    for (let i = e.resultIndex; i < e.results.length; i++) {
      transcript += e.results[i][0].transcript;
    }
    // Put the text into the Streamlit text area
    const textareas = window.parent.document.querySelectorAll('textarea');
    if (textareas.length > 0) {
      const ta = textareas[textareas.length - 1];
      const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.parent.HTMLTextAreaElement.prototype, 'value').set;
      nativeInputValueSetter.call(ta, transcript);
      ta.dispatchEvent(new Event('input', { bubbles: true }));
    }
    status.textContent = '🗣️ Heard: "' + transcript + '"';
    status.style.color = '#00e5a0';
  };

  recognition.onerror = (e) => {
    status.textContent = '⚠️ ' + e.error + '. Try again.';
    status.style.color = '#ff6b6b';
    resetBtn();
  };

  recognition.onend = () => { resetBtn(); };
  recognition.start();
}

function stopVoice() {
  if (recognition) recognition.stop();
  resetBtn();
}

function resetBtn() {
  isListening = false;
  const btn = document.getElementById('voiceBtn');
  document.getElementById('voiceIcon').textContent = '🎤';
  document.getElementById('voiceLabel').textContent = 'Click to Speak';
  btn.style.borderColor = '#2a3441';
  btn.style.background = '#1e2733';
}
</script>
"""

# ── INIT ──────────────────────────────────────────────────
init_db()
if "cart"           not in st.session_state: st.session_state.cart = []
if "activity"       not in st.session_state: st.session_state.activity = []
if "ai_response"    not in st.session_state: st.session_state.ai_response = ""
if "sim_log"        not in st.session_state: st.session_state.sim_log = []
if "ollama_model"   not in st.session_state: st.session_state.ollama_model = "llama3"
if "last_action"    not in st.session_state: st.session_state.last_action = None
if "ai_input_text"  not in st.session_state: st.session_state.ai_input_text = ""
if "pc_results"     not in st.session_state: st.session_state.pc_results = []
if "pc_last_query"  not in st.session_state: st.session_state.pc_last_query = ""
if "pc_search_val"  not in st.session_state: st.session_state.pc_search_val = ""
if "nav_menu"       not in st.session_state: st.session_state.nav_menu = "Home"

def select_pop_item(name):
    st.session_state.pc_search_val = name
    st.session_state.pc_force_search = True

# ── PERSISTENT CART SYNC (Double-Lock System) ───────────
db_cart_items = get_db_cart()
if db_cart_items:
    clean_name = lambda n: n.strip().lower()
    for db_item in db_cart_items:
        item_to_add = {
            "name":     db_item.get("name", "Unknown"),
            "price":    db_item.get("price", 0.0),
            "platform": db_item.get("platform", "Unknown"),
            "qty":      db_item.get("qty", 1),
            "unit":     "unit",  
            "icon":     "🛒"     
        }
        # Check if already in session cart
        exists = any(clean_name(c["name"]) == clean_name(item_to_add["name"]) for c in st.session_state.cart)
        if not exists:
            st.session_state.cart.append(item_to_add)
            st.toast(f"🛒 **{item_to_add['name']}** restored from database!", icon="⚡")
            
        # Delete only this specific item from DB since it's now in the browser session
        delete_from_db_cart(db_item["id"])

# ── AUTOMATIC TELEGRAM ALERTS ──────────────────────────────
low_items = get_low_items()
if low_items:
    # Use session state to ensure we only notify ONCE per browser refresh/session
    if "alert_sent_this_session" not in st.session_state:
        if automate_telegram_alerts(low_items, force=True):
            st.toast("📱 Telegram Alert sent for low stock items!", icon="🚀")
            st.session_state.alert_sent_this_session = True
    
    with st.sidebar:
        if st.button("📢 Force Telegram Alert", help="Send low stock notification to Telegram now"):
            from telegram_utils import send_telegram_alert
            for item in low_items:
                send_telegram_alert(item[0], item[1])
            st.success("Alerts sent!")

# ── QUERY PARAM HANDLING (Legacy WhatsApp support) ──────
if "add_to_cart" in st.query_params:
    item_to_add = st.query_params["add_to_cart"]
    if add_single_item_to_cart(item_to_add, st.session_state.cart):
        st.success(f"✅ **{item_to_add}** added to cart via WhatsApp link!")
        st.session_state.activity.insert(0, {"desc": f"Added {item_to_add} via WhatsApp", "icon": "📱", "price": 0, "date": datetime.now().strftime("%d %b")})
    # Clear query params to prevent re-adding on refresh (Streamlit 1.30+)
    st.query_params.clear()

# ── HEADER ────────────────────────────────────────────────
c_logo, c_status = st.columns([3,1])
with c_logo:
    st.markdown("""<div style='padding:0.3rem 0 0.5rem;'>
      <span style='font-family:DM Serif Display,serif;font-size:1.6rem;color:#00e5a0;'>Grocery<span style='color:#e6edf3;font-style:italic;'>Mind</span></span>
      <span style='color:#7d8590;font-size:0.75rem;margin-left:0.75rem;'>Free · Offline · Ollama 🦙 + Voice 🎤</span>
    </div>""", unsafe_allow_html=True)
with c_status:
    ollama_ok, ollama_active = check_ollama_status(st.session_state.ollama_model)
    if ollama_ok:
        st.markdown(f"<div class='ollama-ok'>🟢 Ollama · <b>{ollama_active}</b></div>", unsafe_allow_html=True)
        st.session_state.ollama_model = ollama_active
    else:
        st.markdown("<div class='ollama-fail'>🔴 Ollama offline</div>", unsafe_allow_html=True)

    # --- CART DEBUGGER (Sidebar Bottom) ---
    with st.sidebar:
        st.markdown("---")
        with st.expander("🛠️ Debug Information", expanded=False):
            st.write(f"Cart Items: {len(st.session_state.cart)}")
            if st.session_state.cart:
                for c in st.session_state.cart:
                    st.code(f"{c['name']} | {c['platform']}", language="text")
            else:
                st.write("Cart is empty (Session)")

if not ollama_ok:
    with st.expander("🛠️ Setup Ollama (free, one-time)", expanded=True):
        st.markdown("""
**1. Install:** https://ollama.com/download

**2. Pull a model (terminal):**
```bash
ollama pull phi3      # 2 GB  — low-RAM PCs
ollama pull llama3    # 4 GB  — best quality
ollama pull mistral   # 4 GB  — fastest
```

**3. Start:** `ollama serve`  then refresh this page.
        """)

# ── NAV ───────────────────────────────────────────────────
# Map horizontal menu items for easier selection
tabs = ["Home","Inventory","AI Suggest","Prices","Cart","Dashboard"]

selected = option_menu(None, tabs,
    icons=["house-fill","box-seam-fill","robot","currency-rupee","cart-fill","bar-chart-fill"],
    menu_icon="cast", default_index=0, orientation="horizontal", key="nav_menu",
    styles={
        "container":{"padding":"0","background-color":"#161b22","border-radius":"10px","border":"1px solid #2a3441"},
        "icon":{"color":"#7d8590","font-size":"14px"},
        "nav-link":{"font-size":"13px","font-weight":"500","color":"#7d8590","border-radius":"8px","padding":"0.5rem 1rem"},
        "nav-link-selected":{"background-color":"rgba(0,229,160,0.1)","color":"#00e5a0","font-weight":"600"},
    })
st.markdown("---")

# ═══════════════════════════════════════════════════════════
# HOME
# ═══════════════════════════════════════════════════════════
if selected == "Home":
    st.markdown("""<div style='text-align:center;padding:2rem 0 1rem;'>
      <div class='hero-badge'>🦙 Free · Offline · Voice 🎤 · AI→Inventory Connected</div>
      <div class='hero-title'>Your <em>intelligent</em><br/>grocery companion</div>
      <div style='color:#7d8590;font-size:1rem;line-height:1.7;max-width:520px;margin:1rem auto;'>
        Just say <b style='color:#00e5a0;'>"Add 5 apples to inventory"</b> on the AI page — GroceryMind does the rest, instantly.
      </div>
    </div>""", unsafe_allow_html=True)

    c1,c2,c3 = st.columns(3)
    for col, (icon,title,desc) in zip([c1,c2,c3],[
        ("🎤","Voice Commands","Say 'Add 5 apples' or 'Remove milk' — AI understands and updates inventory instantly."),
        ("🤖↔️📦","AI ↔ Inventory","The AI page is fully connected. Inventory commands execute in real-time."),
        ("⭐","Frequent Items","Tracks what you add most often. One-tap restock your regulars."),
    ]):
        with col:
            st.markdown(f"<div class='gm-card'><div style='font-size:2rem;margin-bottom:0.5rem;'>{icon}</div><div style='font-weight:600;margin-bottom:0.3rem;'>{title}</div><div style='color:#7d8590;font-size:0.82rem;line-height:1.5;'>{desc}</div></div>", unsafe_allow_html=True)

    items = get_all_items(); low = [i for i in items if i[4]=="low"]
    cart_val = sum(c["price"]*c["qty"] for c in st.session_state.cart)
    m1,m2,m3,m4 = st.columns(4)
    with m1: st.metric("📦 Items", len(items))
    with m2: st.metric("🔴 Low Stock", len(low))
    with m3: st.metric("🛒 Cart", f"₹{cart_val:.0f}")
    with m4: st.metric("🦙 Model", st.session_state.ollama_model)

    if low:

        st.markdown("<br/><div class='gm-card gm-card-warn'><b>⚠️ Low Stock Alert</b></div>", unsafe_allow_html=True)
        cols = st.columns(min(len(low),4))
        for i,item in enumerate(low[:4]):
            with cols[i]:
                st.markdown(f"<div class='gm-card' style='text-align:center;padding:0.8rem;'><div style='font-size:1.5rem;'>{item[5]}</div><div style='font-weight:600;font-size:0.88rem;'>{item[1]}</div><div style='color:#ff6b6b;font-size:0.75rem;'>{item[2]} {item[3]}</div></div>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════
# INVENTORY
# ═══════════════════════════════════════════════════════════
elif selected == "Inventory":
    st.markdown("<div class='section-title'>📦 Inventory</div>", unsafe_allow_html=True)
    st.markdown("<div class='section-sub'>Manage your household grocery items · Frequently added items below</div>", unsafe_allow_html=True)

    # ── FREQUENT ITEMS ──
    freq = get_frequent_items(8)
    if freq:
        st.markdown("**⭐ Frequently Added — tap to quick-restock:**")
        cols = st.columns(min(len(freq), 4))
        for i, f in enumerate(freq):
            fname, fcount, funit, fcat, ficon = f
            with cols[i % 4]:
                st.markdown(f"""<div class='gm-card' style='padding:0.75rem;text-align:center;cursor:pointer;' title='Added {fcount}x'>
                  <div style='font-size:1.4rem;'>{ficon}</div>
                  <div style='font-weight:600;font-size:0.82rem;margin-top:0.3rem;'>{fname}</div>
                  <div style='color:#7d8590;font-size:0.7rem;'>added {fcount}× · {funit}</div>
                </div>""", unsafe_allow_html=True)
                if st.button(f"+ Add 1", key=f"freq_{i}", use_container_width=True):
                    result = ai_add_to_inventory(fname, 1.0, funit)
                    st.success(f"✅ {result['action'].title()}: **{result['name']}** → {result['qty']} {result['unit']}")
                    st.session_state.activity.insert(0, {"desc":f"Quick-added {fname}","icon":"⭐","price":0,"date":datetime.now().strftime("%d %b")})
                    st.rerun()
        st.markdown("---")

    col_form, col_list = st.columns([1,1.6])

    with col_form:
        st.markdown("**➕ Add New Item**")
        with st.form("add_form", clear_on_submit=True):
            name   = st.text_input("Item Name", placeholder="e.g. Milk, Apple, Rice…")
            c1,c2  = st.columns(2)
            with c1: qty  = st.number_input("Quantity", min_value=0.0, step=0.5)
            with c2: unit = st.selectbox("Unit", ["units","kg","g","L","ml","packets","dozen"])
            c3,c4  = st.columns(2)
            with c3:
                cat = st.selectbox("Category", [
                    "🥛 Dairy","🌾 Grains","🥚 Eggs","🥦 Vegetables",
                    "🍎 Fruits","🛢️ Oils","🧂 Spices","🥤 Beverages","🍫 Snacks","🧹 Household"
                ])
            with c4:
                status = st.selectbox("Status",["ok","med","low"],
                    format_func=lambda x:{"ok":"✅ Good","med":"⚠️ Medium","low":"🔴 Low"}[x])
            if st.form_submit_button("+ Add to Inventory", use_container_width=True):
                if name.strip():
                    add_item(name.strip(), qty, unit, cat, status, cat.split()[0])
                    st.success(f"✅ **{name}** added!")
                    st.session_state.activity.insert(0,{"desc":f"Added {name}","icon":"📦","price":0,"date":datetime.now().strftime("%d %b")})
                    st.rerun()
                else:
                    st.error("Enter an item name.")

        # AI Quick-Add box on inventory page
        st.markdown("<br/>**🤖 AI Quick-Add**", unsafe_allow_html=True)
        st.markdown("<div style='color:#7d8590;font-size:0.78rem;margin-bottom:0.5rem;'>Type like you speak: \"add 3kg potatoes\"</div>", unsafe_allow_html=True)
        quick_cmd = st.text_input("Quick command", placeholder="add 5 apples / remove milk / update sugar to 2kg", label_visibility="collapsed", key="inv_quick_cmd")
        if st.button("⚡ Execute", use_container_width=True, key="inv_exec"):
            if quick_cmd.strip():
                intent = parse_inventory_intent(quick_cmd)
                if intent:
                    if intent["action"] == "add":
                        result = ai_add_to_inventory(intent["name"], intent["qty"], intent["unit"])
                        st.success(f"✅ {result['action'].title()}: **{result['name']}** → {result['qty']} {result['unit']}")
                        st.session_state.activity.insert(0,{"desc":f"AI added {result['name']}","icon":"🤖","price":0,"date":datetime.now().strftime("%d %b")})
                        st.rerun()
                    elif intent["action"] == "remove":
                        ex = get_item_by_name(intent["name"])
                        if ex:
                            delete_item(ex[0])
                            st.success(f"🗑️ Removed **{ex[1]}** from inventory")
                            st.rerun()
                        else:
                            st.warning(f"'{intent['name']}' not found in inventory.")
                    elif intent["action"] == "update":
                        ex = get_item_by_name(intent["name"])
                        if ex:
                            update_item_qty(ex[0], intent["qty"])
                            st.success(f"✏️ Updated **{ex[1]}** to {intent['qty']} {intent['unit']}")
                            st.rerun()
                        else:
                            st.warning(f"'{intent['name']}' not found.")
                else:
                    st.info("Couldn't parse that. Try: 'add 5 apples' or 'remove milk'")

    with col_list:
        items = get_all_items()
        st.markdown(f"**Current Stock** — {len(items)} items")
        filt = st.radio("Filter",["All","🔴 Low","⚠️ Medium","✅ Good"], horizontal=True)
        if filt=="🔴 Low":       items=[i for i in items if i[4]=="low"]
        elif filt=="⚠️ Medium":  items=[i for i in items if i[4]=="med"]
        elif filt=="✅ Good":    items=[i for i in items if i[4]=="ok"]

        if not items:
            st.markdown("<div style='text-align:center;padding:3rem;color:#7d8590;'><div style='font-size:3rem;opacity:0.4;'>📭</div><p>No items found.</p></div>", unsafe_allow_html=True)
        else:
            for item in items:
                iid,iname,iqty,iunit,istatus,iicon,icat,*rest = item
                badge={"ok":"<span class='badge-ok'>GOOD</span>","med":"<span class='badge-med'>MEDIUM</span>","low":"<span class='badge-low'>LOW</span>"}[istatus]
                c1,c2,c3 = st.columns([4.5,0.8,0.8])
                with c1:
                    st.markdown(f"""<div class='inv-row'>
                      <div style='background:#ffffff10;width:38px;height:38px;border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:1.3rem;flex-shrink:0;'>{iicon}</div>
                      <div style='flex:1;'><div style='font-weight:600;font-size:0.92rem;'>{iname}</div>
                      <div style='color:#7d8590;font-size:0.78rem;font-family:DM Mono,monospace;'>{iqty} {iunit} · {icat}</div></div>
                      {badge}
                    </div>""", unsafe_allow_html=True)
                with c2:
                    if st.button("+1", key=f"inc_{iid}", help="Add 1 more"):
                        from inventory import increment_item_qty
                        increment_item_qty(iid, 1)
                        st.rerun()
                with c3:
                    if st.button("✕", key=f"del_{iid}"):
                        delete_item(iid); st.rerun()

# ═══════════════════════════════════════════════════════════
# AI SUGGEST  ←→  INVENTORY (connected)
# ═══════════════════════════════════════════════════════════
elif selected == "AI Suggest":
    st.markdown("<div class='section-title'>🦙 AI Suggest</div>", unsafe_allow_html=True)
    st.markdown("<div class='section-sub'>Talk to AI · It understands inventory commands + gives smart suggestions · Voice enabled 🎤</div>", unsafe_allow_html=True)

    # Show last action result
    if st.session_state.last_action:
        a = st.session_state.last_action
        if a["action"] == "add":
            verb = "Updated" if a.get("was_existing") else "Added"
            st.markdown(f"""<div class='action-toast'>
              <div class='at-title'>✅ {verb} to Inventory</div>
              <div class='at-body'>{a['icon']} <b>{a['name']}</b> — {a['qty']} {a['unit']} · Category: {a['cat']}</div>
            </div>""", unsafe_allow_html=True)
        elif a["action"] == "remove":
            st.markdown(f"""<div class='action-toast' style='border-color:rgba(255,107,107,0.3);background:rgba(255,107,107,0.04);'>
              <div class='at-title' style='color:#ff6b6b;'>🗑️ Removed from Inventory</div>
              <div class='at-body'><b>{a['name']}</b> has been removed.</div>
            </div>""", unsafe_allow_html=True)
        elif a["action"] == "update":
            st.markdown(f"""<div class='action-toast' style='border-color:rgba(255,209,102,0.3);background:rgba(255,209,102,0.04);'>
              <div class='at-title' style='color:#ffd166;'>✏️ Inventory Updated</div>
              <div class='at-body'><b>{a['name']}</b> set to {a['qty']} {a.get('unit','units')}</div>
            </div>""", unsafe_allow_html=True)

    # Model selector
    c1,c2 = st.columns([1,3])
    with c1:
        model_choice = st.selectbox("🦙 Model",["llama3","mistral","phi3","gemma2","llama3.2","qwen2"],
            index=["llama3","mistral","phi3","gemma2","llama3.2","qwen2"].index(st.session_state.ollama_model)
                  if st.session_state.ollama_model in ["llama3","mistral","phi3","gemma2","llama3.2","qwen2"] else 0)
        st.session_state.ollama_model = model_choice
    with c2:
        st.markdown("<div style='padding-top:1.8rem;color:#7d8590;font-size:0.8rem;'>💡 <b>Inventory commands</b> work instantly — no Ollama needed! &nbsp;|&nbsp; AI responses need Ollama running.</div>", unsafe_allow_html=True)

    items = get_all_items()
    inv_summary = ", ".join([f"{i[1]}: {i[2]}{i[3]} ({i[4]} stock)" for i in items]) if items else "No inventory yet"

    # ── QUICK ACTIONS ──
    st.markdown("**⚡ Quick Actions**")
    qcols = st.columns(5)
    quick_prompts = [
        ("🔴 Low Stock",   "What items are running low and what should I buy today?"),
        ("📅 3-Day Plan",  "Which items will finish in 3 days? Indian family of 4."),
        ("🛍️ Weekly List", "Weekly grocery list for Indian family of 4 with quantities and estimated ₹ cost"),
        ("🍽️ Meal Ideas",  "3 healthy Indian meal ideas I can cook with my current stock"),
        ("💡 Save Money",  "5 tips to reduce grocery spending for Indian households"),
    ]
    for i,(label,prompt) in enumerate(quick_prompts):
        with qcols[i]:
            if st.button(label, key=f"q_{i}", use_container_width=True):
                if not ollama_ok:
                    st.error("Start Ollama first.")
                else:
                    with st.spinner(f"🦙 Thinking…"):
                        st.session_state.ai_response = get_ai_suggestion(prompt, inv_summary, st.session_state.ollama_model)
                    st.session_state.last_action = None

    st.markdown("<br/>", unsafe_allow_html=True)

    # ── INPUT BOX + VOICE ──
    st.markdown("<div class='gm-card gm-card-voice'>", unsafe_allow_html=True)
    st.markdown("**🎤 Speak or Type · AI understands both suggestions AND inventory commands**")
    st.markdown("""<div style='color:#7d8590;font-size:0.78rem;margin-bottom:0.75rem;line-height:1.6;'>
    Try: &nbsp;<code>add 5 apples to inventory</code> &nbsp;·&nbsp; <code>remove milk</code> &nbsp;·&nbsp; <code>what should I buy today?</code>
    </div>""", unsafe_allow_html=True)

    # Voice widget (browser Web Speech API)
    col_voice, col_hint = st.columns([1,3])
    with col_voice:
        st.components.v1.html(VOICE_JS, height=80)
    with col_hint:
        st.markdown("""<div style='padding-top:0.3rem;'>
          <div style='color:#7d8590;font-size:0.75rem;line-height:1.6;'>
            🎤 Voice works in <b>Chrome / Edge</b> browser<br/>
            After clicking, speak clearly — text appears in the box below<br/>
            Then click <b>Send</b> to process
          </div>
        </div>""", unsafe_allow_html=True)

    with st.form("ai_main_form", clear_on_submit=False):
        user_q = st.text_area("Your message",
            placeholder="Type or use voice: 'add 5 apples' · 'what's running low?' · 'suggest meals'",
            height=85, key="ai_textarea", label_visibility="collapsed",
            value=st.session_state.ai_input_text)
        c_send, c_inv, c_note = st.columns([1,1,3])
        with c_send: send_btn = st.form_submit_button("🦙 Ask AI", use_container_width=True)
        with c_inv:  inv_btn  = st.form_submit_button("⚡ Execute Command", use_container_width=True)
        with c_note: st.markdown("<div style='color:#7d8590;font-size:0.73rem;padding-top:0.7rem;'>\"Execute Command\" works offline · \"Ask AI\" needs Ollama</div>", unsafe_allow_html=True)

    # ── PROCESS COMMAND (offline, rule-based) ──
    if inv_btn and user_q.strip():
        intent = parse_inventory_intent(user_q)
        st.session_state.last_action = None
        if intent:
            if intent["action"] == "add":
                existing = get_item_by_name(intent["name"])
                result = ai_add_to_inventory(intent["name"], intent["qty"], intent["unit"])
                result["was_existing"] = existing is not None
                st.session_state.last_action = result
                st.session_state.activity.insert(0,{"desc":f"AI {'updated' if existing else 'added'} {result['name']}","icon":"🤖","price":0,"date":datetime.now().strftime("%d %b")})
                st.session_state.ai_response = f"✅ Done! {'Updated' if existing else 'Added'} **{result['name']}** → {result['qty']} {result['unit']} · Category: {result['cat']}"
                st.session_state.ai_input_text = ""
                st.rerun()
            elif intent["action"] == "remove":
                ex = get_item_by_name(intent["name"])
                if ex:
                    delete_item(ex[0])
                    st.session_state.last_action = {"action":"remove","name":ex[1]}
                    st.session_state.ai_response = f"🗑️ Removed **{ex[1]}** from inventory."
                    st.rerun()
                else:
                    st.session_state.ai_response = f"⚠️ '{intent['name']}' not found in inventory."
            elif intent["action"] == "update":
                ex = get_item_by_name(intent["name"])
                if ex:
                    update_item_qty(ex[0], intent["qty"])
                    st.session_state.last_action = {"action":"update","name":ex[1],"qty":intent["qty"],"unit":intent["unit"]}
                    st.session_state.ai_response = f"✏️ Updated **{ex[1]}** to {intent['qty']} {intent['unit']}."
                    st.rerun()
                else:
                    st.session_state.ai_response = f"⚠️ '{intent['name']}' not found in inventory."
        else:
            st.session_state.ai_response = "⚠️ Couldn't detect an inventory command. Try: 'add 5 apples', 'remove milk', 'update sugar to 2kg'\n\nOr click **Ask AI** for a full AI response."

    # ── PROCESS AI QUERY (needs Ollama) ──
    if send_btn and user_q.strip():
        # First check if it's an inventory command — handle without Ollama
        intent = parse_inventory_intent(user_q)
        if intent:
            # It's an inventory command — execute it AND get AI to narrate
            if intent["action"] == "add":
                existing = get_item_by_name(intent["name"])
                result = ai_add_to_inventory(intent["name"], intent["qty"], intent["unit"])
                result["was_existing"] = existing is not None
                st.session_state.last_action = result
                st.session_state.activity.insert(0,{"desc":f"AI added {result['name']}","icon":"🤖","price":0,"date":datetime.now().strftime("%d %b")})
                if ollama_ok:
                    verb = "updated" if existing else "added"
                    confirm_prompt = f"The user said: '{user_q}'. I've {verb} {result['name']} ({result['qty']} {result['unit']}) to their grocery inventory. Please confirm this action in a friendly, brief way and suggest if there's anything else related to {result['name']} they should know."
                    with st.spinner("🦙 Confirming…"):
                        st.session_state.ai_response = get_ai_suggestion(confirm_prompt, inv_summary, st.session_state.ollama_model)
                else:
                    verb = "Updated" if existing else "Added"
                    st.session_state.ai_response = f"✅ {verb} **{result['name']}** → {result['qty']} {result['unit']} to inventory!"
                st.rerun()
        else:
            # Pure AI query
            if not ollama_ok:
                st.session_state.ai_response = "⚠️ Ollama not running. For inventory commands (add/remove/update), use the **Execute Command** button instead — it works offline!"
            else:
                with st.spinner(f"🦙 {st.session_state.ollama_model} thinking…"):
                    st.session_state.ai_response = get_ai_suggestion(user_q, inv_summary, st.session_state.ollama_model)
                st.session_state.activity.insert(0,{"desc":f"AI: {user_q[:40]}…","icon":"🦙","price":0,"date":datetime.now().strftime("%d %b")})

    st.markdown("</div>", unsafe_allow_html=True)

    # ── RESPONSE ──
    if st.session_state.ai_response:
        st.markdown("<br/>**🦙 Response**", unsafe_allow_html=True)
        st.markdown(f"<div class='ai-box'>{st.session_state.ai_response}</div>", unsafe_allow_html=True)
        if st.button("🗑️ Clear"):
            st.session_state.ai_response = ""; st.session_state.last_action = None; st.rerun()
    else:
        st.markdown("""<div class='ai-box' style='color:#7d8590;margin-top:1rem;'>
🦙 GroceryMind AI + Inventory Control<br/><br/>
<b style='color:#00e5a0;'>Inventory commands (work offline):</b><br/>
• "add 5 apples to inventory"<br/>
• "add 2kg rice"<br/>
• "remove milk"<br/>
• "update sugar to 3kg"<br/><br/>
<b style='color:#4ecdc4;'>AI questions (needs Ollama):</b><br/>
• "what should I buy this week?"<br/>
• "suggest 3 Indian meals with my stock"<br/>
• "how can I save money on groceries?"<br/><br/>
<span style='color:#00e5a0;font-size:0.82rem;'>✅ No API key · No subscription · 100% free</span>
        </div>""", unsafe_allow_html=True)

    # Smart alerts
    low_items = [i for i in items if i[4]=="low"]
    if low_items:
        st.markdown("<br/>**📋 Smart Alerts**", unsafe_allow_html=True)
        scols = st.columns(min(len(low_items),3))
        for i,item in enumerate(low_items[:3]):
            with scols[i]:
                st.markdown(f"""<div class='gm-card gm-card-warn'>
                  <div style='font-size:1.2rem;'>{item[5]}</div>
                  <div style='font-weight:600;font-size:0.88rem;margin-top:0.3rem;'>{item[1]}</div>
                  <div style='color:#ff6b6b;font-size:0.78rem;margin-top:0.2rem;'>⚠️ Running low</div>
                  <div style='color:#7d8590;font-size:0.75rem;'>{item[2]} {item[3]} left</div>
                </div>""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════
# PRICES
# ═══════════════════════════════════════════════════════════
elif selected == "Prices":
    st.markdown("<div class='section-title'>💰 Price Comparison</div>", unsafe_allow_html=True)
    st.markdown("<div class='section-sub'>Compare prices across top Indian grocery platforms</div>", unsafe_allow_html=True)
    cs,cb = st.columns([3,1])
    with cs: search_item = st.text_input("Search", key="pc_search_val", placeholder="e.g. Milk, Atta, Dal, Eggs…", label_visibility="collapsed")
    with cb: do_search   = st.button("Compare 🔍", use_container_width=True)
    st.markdown("**🔥 Popular Items**")
    pop_cols = st.columns(6)
    for i,item in enumerate(list(POPULAR_ITEMS.keys())[:6]):
        with pop_cols[i]:
            st.button(item, key=f"pop_{i}", use_container_width=True, on_click=select_pop_item, args=(item,))

    # Check force search from callback
    do_search = st.session_state.get("pc_force_search", False)
    if do_search:
        st.session_state.pc_force_search = False
    
    # Cache management: update results only if query changes or search button clicked
    if search_item:
        should_update = (search_item.lower() != st.session_state.pc_last_query.lower()) or do_search
        if should_update:
            with st.spinner("Comparing Prices..."):
                st.session_state.pc_results = compare_prices(search_item)
                st.session_state.pc_last_query = search_item
        
        results = st.session_state.pc_results
        if results:
            best_price=min(r["price"] for r in results)
            platform_colors={"Blinkit":"#f7c537","BigBasket":"#84c225","Zepto":"#9b59b6","Swiggy Instamart":"#fc8019"}
            st.markdown(f"<br/>**Results for: {results[0]['item']}**",unsafe_allow_html=True)
            hcols=st.columns([2.5,1.2,1.2,1.5,1.2])
            for col,h in zip(hcols,["Platform","Price","Delivery","Min Order","Action"]):
                col.markdown(f"<span style='color:#7d8590;font-size:0.75rem;text-transform:uppercase;letter-spacing:1px;'>{h}</span>",unsafe_allow_html=True)
            st.markdown("<hr style='border-color:#2a3441;margin:0.4rem 0;'/>",unsafe_allow_html=True)
            for r in sorted(results,key=lambda x:x["price"]):
                is_best=r["price"]==best_price
                rc=st.columns([2.5,1.2,1.2,1.5,1.2])
                clr=platform_colors.get(r["platform"],"#7d8590")
                tag="<span class='badge-best'>BEST</span>" if is_best else ""
                with rc[0]: st.markdown(f"<span style='display:inline-block;width:8px;height:8px;background:{clr};border-radius:50%;margin-right:0.4rem;'></span><b>{r['platform']}</b>{tag}",unsafe_allow_html=True)
                with rc[1]: st.markdown(f"<span style='font-family:DM Mono,monospace;font-weight:600;color:{'#00e5a0' if is_best else '#e6edf3'};'>₹{r['price']}</span>",unsafe_allow_html=True)
                with rc[2]: st.markdown(f"<span style='background:#1c2330;padding:0.15rem 0.5rem;border-radius:4px;font-size:0.75rem;color:#7d8590;'>{'Free' if r['delivery']==0 else '₹'+str(r['delivery'])}</span>",unsafe_allow_html=True)
                with rc[3]: st.markdown(f"<span style='color:#7d8590;font-size:0.82rem;'>₹{r['min_order']}</span>",unsafe_allow_html=True)
                with rc[4]:
                    # Unique key combining platform, item name and price to avoid collisions
                    btn_key = f"pc_{r['platform']}_{r['item']}_{r['price']}"
                    if st.button("+ Cart", key=btn_key):
                        # 1. Update Session Cart (for immediate UI update)
                        ex=next((c for c in st.session_state.cart if c["name"]==r["item"]),None)
                        if ex:
                            ex["qty"] += 1
                        else:
                            st.session_state.cart.append({
                                "name": r["item"],
                                "price": r["price"],
                                "platform": r["platform"],
                                "qty": 1,
                                "unit": "unit",
                                "icon": "🛒"
                            })
                        
                        # 2. Update Database Cart (for Telegram Bot sync)
                        from inventory import add_to_db_cart
                        add_to_db_cart(r["item"], r["price"], r["platform"], 1)
                        
                        st.success(f"✅ Added {r['item']} to cart!")
                        st.toast(f"**{r['item']}** added to cart", icon="🛒")
                        if st.button("View in Cart 🛒", key=f"view_{btn_key}"):
                            st.session_state.nav_menu = "Cart"
                            st.rerun()
                        st.session_state.activity.insert(0,{"desc":f"Price compared: {r['item']}","icon":"💰","price":r["price"],"date":datetime.now().strftime("%d %b")})
                        # st.rerun()  <- Removed to ensure success message is visible
                st.markdown("<hr style='border-color:#2a3441;margin:0.2rem 0;'/>",unsafe_allow_html=True)
            savings=max(r["price"] for r in results)-best_price
            if savings>0: st.success(f"💡 Save ₹{savings} by choosing the best option!")
        else:
            st.warning(f"No data for **{search_item}**. Try: Milk, Rice, Dal, Oil, Eggs, Onion, Atta")

# ═══════════════════════════════════════════════════════════
# CART
# ═══════════════════════════════════════════════════════════
elif selected == "Cart":
    st.markdown("<div class='section-title'>🛒 Smart Cart</div>",unsafe_allow_html=True)
    st.markdown("<div class='section-sub'>Auto-add low-stock items and simulate order placement</div>",unsafe_allow_html=True)
    col_cart,col_sum = st.columns([1.6,1])
    with col_cart:
        if st.button("⚡ Auto-Add Low Stock Items",use_container_width=True):
            items_to_add = get_low_items()
            added=simulate_add_to_cart(items_to_add, st.session_state.cart)
            if added: 
                # Sync to Database Cart
                from inventory import add_to_db_cart
                from price_checker import get_best_price
                for item in items_to_add:
                    # Only add if not already in session cart (simulate_add_to_cart handles session)
                    # We'll just add all low items to DB cart to be safe/sync
                    best = get_best_price(item[1])
                    price = best["price"] if best else 50.0
                    platform = best["platform"] if best else "Blinkit"
                    add_to_db_cart(item[1], price, platform, 1)
                
                st.success(f"Added {added} items to cart!"); st.rerun()
            else: st.info("No new low-stock items to add.")
        if not st.session_state.cart:
            st.markdown("<div style='text-align:center;padding:3rem;color:#7d8590;'><div style='font-size:3rem;opacity:0.4;'>🛒</div><p>Cart is empty.</p></div>",unsafe_allow_html=True)
        else:
            for idx,item in enumerate(st.session_state.cart):
                c1,c2,c3,c4,c5=st.columns([3,1.5,0.8,0.8,0.7])
                with c1: st.markdown(f"**{item['name']}**  \n<span style='color:#7d8590;font-size:0.78rem;'>{item['platform']}</span>",unsafe_allow_html=True)
                with c2: st.markdown(f"<span style='color:#00e5a0;font-family:DM Mono,monospace;font-weight:600;'>₹{item['price']*item['qty']:.2f}</span>",unsafe_allow_html=True)
                with c3:
                    if st.button("−",key=f"m_{idx}"):
                        if item["qty"]>1: st.session_state.cart[idx]["qty"]-=1
                        st.rerun()
                with c4: st.markdown(f"<div style='text-align:center;font-family:DM Mono,monospace;padding-top:0.4rem;'>{item['qty']}</div>",unsafe_allow_html=True)
                with c5:
                    if st.button("🗑️",key=f"del_{idx}"):
                        from inventory import delete_from_db_cart, get_db_cart
                        # Find the DB ID for this item (name + platform match)
                        db_items = get_db_cart()
                        for di in db_items:
                            if di["name"] == item["name"] and di["platform"] == item["platform"]:
                                delete_from_db_cart(di["id"])
                                break
                        st.session_state.cart.pop(idx)
                        st.rerun()
                # Slot for '+' removed to make room, but I'll add it back better
                # Wait, I'll just use a smarter layout
                st.markdown("<hr style='border-color:#2a3441;margin:0.2rem 0;'/>",unsafe_allow_html=True)
        if st.session_state.cart and st.button("🗑️ Clear Cart",use_container_width=True):
            from inventory import clear_db_cart
            clear_db_cart()
            st.session_state.cart=[]; st.rerun()
        st.markdown("<br/>**📟 Simulation Log**",unsafe_allow_html=True)
        if st.session_state.sim_log:
            log_html="<div class='sim-log'>"
            for line in st.session_state.sim_log:
                cls="log-ok" if line.startswith("[OK]") else "log-info" if line.startswith("[INFO]") else "log-warn"
                log_html+=f"<div class='{cls}'>{line}</div>"
            st.markdown(log_html+"</div>",unsafe_allow_html=True)
        else:
            st.markdown("<div class='sim-log'><span style='color:#3a4451;'>// Ready…</span></div>",unsafe_allow_html=True)
    with col_sum:
        st.markdown("**📋 Order Summary**")
        total=0
        if st.session_state.cart:
            for item in st.session_state.cart:
                sub=item["price"]*item["qty"]; total+=sub
                c1,c2=st.columns([3,1])
                c1.markdown(f"<span style='font-size:0.82rem;'>{item['name']} ×{item['qty']}</span>",unsafe_allow_html=True)
                c2.markdown(f"<span style='font-size:0.82rem;font-family:DM Mono,monospace;'>₹{sub:.0f}</span>",unsafe_allow_html=True)
            st.markdown("<hr style='border-color:#2a3441;'/>",unsafe_allow_html=True)
            c1,c2=st.columns([3,1])
            c1.markdown("**Total**")
            c2.markdown(f"<span style='color:#00e5a0;font-family:DM Mono,monospace;font-weight:700;font-size:1.1rem;'>₹{total:.2f}</span>",unsafe_allow_html=True)
            st.markdown("<br/>",unsafe_allow_html=True)
            if st.button("🚀 Simulate Order",use_container_width=True):
                st.session_state.sim_log=simulate_order(st.session_state.cart)
                # Success! Clear both session and DB cart
                from inventory import clear_db_cart
                clear_db_cart()
                st.session_state.cart = []
                st.rerun()
                st.session_state.activity.insert(0,{"desc":"Order simulated","icon":"🛒","price":total,"date":datetime.now().strftime("%d %b")})
                st.success(f"🎉 Done! ₹{total:.2f}"); st.rerun()
        else:
            st.markdown("<div style='color:#7d8590;font-size:0.85rem;'>Add items to see summary</div>",unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════
# DASHBOARD
# ═══════════════════════════════════════════════════════════
elif selected == "Dashboard":
    st.markdown("<div class='section-title'>📊 Dashboard</div>",unsafe_allow_html=True)
    st.markdown("<div class='section-sub'>Overview of your grocery intelligence</div>",unsafe_allow_html=True)
    items=get_all_items(); low=[i for i in items if i[4]=="low"]; med=[i for i in items if i[4]=="med"]
    cart_val=sum(c["price"]*c["qty"] for c in st.session_state.cart)
    m1,m2,m3,m4=st.columns(4)
    with m1: st.metric("📦 Total Items",len(items))
    with m2: st.metric("🔴 Low Stock",len(low))
    with m3: st.metric("🛒 Cart Value",f"₹{cart_val:.0f}")
    with m4: st.metric("💚 Est. Savings",f"₹{cart_val*0.06:.0f}",delta="vs avg price")
    st.markdown("<br/>",unsafe_allow_html=True)
    col_chart,col_act=st.columns([1.5,1])
    with col_chart:
        st.markdown("**📈 Monthly Spending (₹)**")
        months=["Oct","Nov","Dec","Jan","Feb","Mar"]
        spend=[3200,2800,4100,3600,3900,max(int(cart_val),2400)]
        st.bar_chart(pd.DataFrame({"Spending (₹)":spend},index=months),color="#00e5a0")
        if items:
            st.markdown("<br/>**📊 Stock Status**",unsafe_allow_html=True)
            sc={"✅ Good":len([i for i in items if i[4]=="ok"]),"⚠️ Medium":len(med),"🔴 Low":len(low)}
            st.bar_chart(pd.DataFrame({"Count":list(sc.values())},index=list(sc.keys())),color="#4ecdc4")
        freq=get_frequent_items(5)
        if freq:
            st.markdown("<br/>**⭐ Most Added Items**",unsafe_allow_html=True)
            st.dataframe(pd.DataFrame(freq,columns=["Item","Times Added","Unit","Category","Icon"])[["Item","Times Added","Category"]],use_container_width=True,hide_index=True)
    with col_act:
        st.markdown("**🕐 Recent Activity**")
        default_act=[
            {"desc":"Added Apples via voice","icon":"🎤","price":0,"date":"Today"},
            {"desc":"AI added 5 Apples","icon":"🤖","price":0,"date":"Today"},
            {"desc":"Compared prices for Rice","icon":"💰","price":385,"date":"Today"},
        ]
        acts=st.session_state.activity or default_act
        for act in acts[:8]:
            c1,c2=st.columns([4,1])
            with c1:
                st.markdown(f"""<div class='gm-card' style='padding:0.7rem 0.9rem;margin-bottom:0.4rem;'>
                  <span>{act['icon']}</span>
                  <span style='font-size:0.82rem;font-weight:500;margin-left:0.4rem;'>{act['desc']}</span>
                  <div style='color:#7d8590;font-size:0.72rem;margin-top:0.15rem;margin-left:1.5rem;'>{act['date']}</div>
                </div>""",unsafe_allow_html=True)
            with c2:
                if act["price"]: st.markdown(f"<div style='color:#00e5a0;font-family:DM Mono,monospace;font-size:0.8rem;padding-top:1rem;'>₹{act['price']:.0f}</div>",unsafe_allow_html=True)
        if items:
            st.markdown("<br/>**🗂️ By Category**",unsafe_allow_html=True)
            cats=Counter(i[6] for i in items)
            st.dataframe(pd.DataFrame(list(cats.items()),columns=["Category","Items"]),use_container_width=True,hide_index=True)
