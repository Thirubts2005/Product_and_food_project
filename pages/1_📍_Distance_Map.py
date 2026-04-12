import streamlit as st
import json
import math
import time
import random
import folium
from streamlit_folium import st_folium
from datetime import datetime, date, timedelta
from datetime import time as dtime

# ── Page config (Handled by app.py) ──────────────────────────────────────────────────
# st.set_page_config(
#     page_title="AI SmartBuy",
#     page_icon="🧠",
#     layout="wide",
#     initial_sidebar_state="collapsed",
# )

# ── CSS ──────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
#MainMenu, footer, header {visibility: hidden;}
html, body, [class*="css"] { font-family: 'Segoe UI', sans-serif; }
.stApp { background: #f0f4f8; }

.main-header {
    background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 60%, #0ea5e9 100%);
    color: white; padding: 1.4rem 1.8rem; border-radius: 16px; margin-bottom: 1.4rem;
}
.main-header h1 { margin: 0; font-size: 1.75rem; font-weight: 700; }
.main-header p  { margin: 0; opacity: 0.7; font-size: 0.85rem; }

.card {
    background: white; border-radius: 14px;
    border: 1px solid #e2e8f0; padding: 1.1rem 1.3rem; margin-bottom: 0.8rem;
}
.must-buy-card {
    background: white; border: 2.5px solid #3b82f6;
    border-radius: 16px; padding: 1.2rem 1.4rem;
    box-shadow: 0 6px 24px rgba(59,130,246,0.13); margin-bottom: 0.8rem;
}
.must-buy-badge {
    display:inline-block; background:#dbeafe; color:#1d4ed8;
    padding:3px 12px; border-radius:20px; font-size:0.72rem; font-weight:700;
}
.shop-big-name { font-size:1.5rem; font-weight:700; color:#0f172a; margin:6px 0 10px; }
.stat-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:8px; margin-bottom:10px; }
.stat-box  { background:#f1f5f9; border-radius:10px; padding:8px 10px; text-align:center; }
.stat-label { font-size:0.68rem; color:#64748b; margin-bottom:2px; text-transform:uppercase; letter-spacing:.04em; }
.stat-value { font-size:1.05rem; font-weight:700; color:#0f172a; }
.stat-value.green { color:#16a34a; }
.stat-value.blue  { color:#2563eb; }
.dist-box {
    background:#eff6ff; border:1px solid #bfdbfe; border-radius:12px;
    padding:10px 14px; margin-bottom:10px; display:flex; align-items:center; gap:10px;
}
.dist-route { font-size:1.05rem; font-weight:700; color:#1d4ed8; }
.dist-sub   { font-size:0.75rem; color:#3b82f6; margin-top:2px; }
.urgency-box {
    background:#fefce8; border:1px solid #fde047; border-radius:10px;
    padding:7px 12px; font-size:0.78rem; color:#854d0e; margin-bottom:10px;
}
.urgency-box.red { background:#fff1f2; border-color:#fca5a5; color:#b91c1c; }
.section-title {
    font-size:0.68rem; font-weight:700; text-transform:uppercase;
    letter-spacing:.08em; color:#94a3b8; margin-bottom:0.5rem;
}
.compare-table { width:100%; border-collapse:collapse; }
.compare-table th {
    background:#f8fafc; padding:9px 12px; text-align:left;
    font-size:0.7rem; color:#64748b; font-weight:700;
    text-transform:uppercase; letter-spacing:.05em;
    border-bottom:1px solid #e2e8f0;
}
.compare-table td { padding:9px 12px; border-bottom:1px solid #f1f5f9; font-size:0.82rem; color:#1e293b; }
.compare-table tr.best-row td { background:#eff6ff; }
.score-green  { background:#dcfce7; color:#15803d; padding:2px 9px; border-radius:20px; font-size:0.72rem; font-weight:700; }
.score-yellow { background:#fef9c3; color:#854d0e; padding:2px 9px; border-radius:20px; font-size:0.72rem; font-weight:700; }
.score-red    { background:#fee2e2; color:#b91c1c; padding:2px 9px; border-radius:20px; font-size:0.72rem; font-weight:700; }
.live-dot {
    display:inline-block; width:7px; height:7px; background:#ef4444;
    border-radius:50%; margin-right:4px; animation:blink 1.2s infinite;
}
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:.2} }
.track-step { display:flex; align-items:center; gap:12px; padding:9px 0; }
.track-circle {
    width:30px; height:30px; border-radius:50%; flex-shrink:0;
    display:flex; align-items:center; justify-content:center;
    font-size:0.82rem; font-weight:700;
}
.t-done    { background:#dcfce7; color:#15803d; }
.t-active  { background:#dbeafe; color:#1d4ed8; }
.t-pending { background:#f1f5f9; color:#94a3b8; }
.track-label { font-size:0.85rem; font-weight:600; color:#1e293b; }
.track-sub   { font-size:0.72rem; color:#64748b; }
.countdown-box {
    background: linear-gradient(135deg, #1e3a5f, #0ea5e9);
    color: white; border-radius: 14px; padding: 1rem 1.3rem;
    text-align: center; margin-bottom: 0.8rem;
}
.countdown-time  { font-size: 2.2rem; font-weight: 800; letter-spacing: 3px; font-variant-numeric: tabular-nums; }
.countdown-label { font-size: 0.75rem; opacity: 0.8; margin-top: 4px; }
.empty-state { text-align:center; padding:4rem 2rem; color:#94a3b8; }
</style>
""", unsafe_allow_html=True)


# ── Load DB ───────────────────────────────────────────────────────────────────────
@st.cache_data
def load_db():
    with open("db.json") as f:
        return json.load(f)

db           = load_db()
SHOPS_MAP    = {s["id"]: s for s in db["shops"]}
PRODUCTS_MAP = {p["id"]: p for p in db["products"]}
PRODUCT_NAME_INDEX = {p["name"].lower(): p for p in db["products"]}

@st.cache_data
def build_stock_index():
    idx = {}
    for entry in db["stock"]:
        pid  = entry["product_id"]
        shop = SHOPS_MAP[entry["shop_id"]]
        idx.setdefault(pid, []).append({
            "shop_id": shop["id"],
            "name":    shop["name"],
            "area":    shop["area"],
            "lat":     shop["lat"],
            "lon":     shop["lon"],
            "price":   entry["price"],
            "stock":   entry["stock"],
        })
    return idx

STOCK_INDEX = build_stock_index()

# ── Fixed location: Coimbatore ───────────────────────────────────────────────────
USER_LAT = 10.9010
USER_LON = 76.9558


# ── Helpers ───────────────────────────────────────────────────────────────────────
def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat/2)**2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
         * math.sin(dlon/2)**2)
    return round(R * 2 * math.asin(math.sqrt(a)), 2)

def travel_min(dist_km):
    return max(2, int((dist_km / 20) * 60))

def normalize(values):
    mn, mx = min(values), max(values)
    if mn == mx:
        return [1.0] * len(values)
    return [(v - mn) / (mx - mn) for v in values]

def ai_score_shops(shops_raw):
    prices    = [s["price"]    for s in shops_raw]
    distances = [s["distance"] for s in shops_raw]
    stocks    = [s["stock"]    for s in shops_raw]
    ps = [1 - p for p in normalize(prices)]
    ds = [1 - d for d in normalize(distances)]
    ss = normalize(stocks)
    scored = []
    for i, s in enumerate(shops_raw):
        raw = 0.50 * ps[i] + 0.30 * ds[i] + 0.20 * ss[i]
        scored.append({**s, "score": round(raw * 100)})
    return sorted(scored, key=lambda x: x["score"], reverse=True)

def search_product(query):
    q = query.strip().lower()
    matched = None
    for name, prod in PRODUCT_NAME_INDEX.items():
        if q in name or name in q:
            matched = prod
            break
    if not matched:
        return None, []
    pid = matched["id"]
    raw = STOCK_INDEX.get(pid, [])
    if not raw:
        return matched, []
    raw_copy = [dict(s) for s in raw]
    for s in raw_copy:
        s["distance"]   = haversine(USER_LAT, USER_LON, s["lat"], s["lon"])
        s["travel_min"] = travel_min(s["distance"])
    return matched, ai_score_shops(raw_copy)


# ── Folium Map ────────────────────────────────────────────────────────────────────
def build_map(shops, top):
    m = folium.Map(
        location=[USER_LAT, USER_LON],
        zoom_start=13,
        tiles="CartoDB positron",
        control_scale=True,
    )
    folium.Marker(
        [USER_LAT, USER_LON],
        popup="📍 Your Location",
        tooltip="You are here",
        icon=folium.Icon(color="blue", icon="home", prefix="fa"),
    ).add_to(m)

    for i, shop in enumerate(shops):
        is_best   = (shop["shop_id"] == top["shop_id"])
        pin_color = "green" if is_best else ("orange" if i == 1 else "red")
        icon_name = "star" if is_best else "shopping-cart"

        popup_html = (
            f"<div style='font-family:Segoe UI,sans-serif;min-width:200px;padding:4px'>"
            f"<b style='font-size:14px;color:#1e3a5f'>{shop['name']}</b>"
            + ("<br><span style='background:#dbeafe;color:#1d4ed8;padding:2px 8px;"
               "border-radius:10px;font-size:11px;font-weight:700'>&#x1F525; Best Deal</span>"
               if is_best else "")
            + "<hr style='margin:6px 0;border-color:#e2e8f0'>"
            f"<table style='font-size:12px;width:100%;border-collapse:collapse'>"
            f"<tr><td style='color:#64748b;padding:3px 0'>&#x1F4CD; Area</td>"
            f"<td style='padding:3px 0'><b>{shop['area']}</b></td></tr>"
            f"<tr><td style='color:#64748b;padding:3px 0'>&#x1F4B0; Price</td>"
            f"<td style='padding:3px 0'><b>&#8377;{shop['price']}</b></td></tr>"
            f"<tr><td style='color:#64748b;padding:3px 0'>&#x1F4E6; Stock</td>"
            f"<td style='padding:3px 0'><b>{shop['stock']} units</b></td></tr>"
            f"<tr><td style='color:#64748b;padding:3px 0'>&#x1F4CF; Distance</td>"
            f"<td style='padding:3px 0'><b>{shop['distance']} km</b></td></tr>"
            f"<tr><td style='color:#64748b;padding:3px 0'>&#x23F1; ETA</td>"
            f"<td style='padding:3px 0'><b>~{shop['travel_min']} min</b></td></tr>"
            f"<tr><td style='color:#64748b;padding:3px 0'>&#x2B50; Score</td>"
            f"<td style='padding:3px 0'><b>{shop['score']}/100</b></td></tr>"
            "</table></div>"
        )

        folium.Marker(
            [shop["lat"], shop["lon"]],
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=f"{shop['name']} – ₹{shop['price']} | {shop['distance']} km | ~{shop['travel_min']} min",
            icon=folium.Icon(color=pin_color, icon=icon_name, prefix="fa"),
        ).add_to(m)

        if is_best:
            folium.PolyLine(
                locations=[[USER_LAT, USER_LON], [shop["lat"], shop["lon"]]],
                color="#2563eb", weight=4, opacity=0.9,
                tooltip=f"Best route: {shop['distance']} km",
            ).add_to(m)
            mid_lat = (USER_LAT + shop["lat"]) / 2
            mid_lon = (USER_LON + shop["lon"]) / 2
            folium.Marker(
                [mid_lat, mid_lon],
                icon=folium.DivIcon(
                    html=(
                        f"<div style='background:#dbeafe;color:#1d4ed8;"
                        f"border:1px solid #93c5fd;padding:2px 8px;"
                        f"border-radius:10px;font-size:11px;font-weight:700;"
                        f"white-space:nowrap;font-family:Segoe UI,sans-serif;"
                        f"box-shadow:0 1px 4px rgba(0,0,0,.15);'>"
                        f"{shop['distance']} km · ~{shop['travel_min']} min</div>"
                    ),
                    icon_size=(140, 22), icon_anchor=(70, 11),
                ),
            ).add_to(m)
        else:
            folium.PolyLine(
                locations=[[USER_LAT, USER_LON], [shop["lat"], shop["lon"]]],
                color="#cbd5e1", weight=1, opacity=0.35, dash_array="6 8",
            ).add_to(m)
    return m


# ── Unit Options ──────────────────────────────────────────────────────────────────
UNIT_OPTIONS = {
    "kg":    ["0.25 kg", "0.5 kg", "1 kg", "2 kg", "5 kg"],
    "ltr":   ["0.25 ltr", "0.5 ltr", "1 ltr", "2 ltr", "5 ltr"],
    "piece": ["1 piece", "2 pieces", "3 pieces", "5 pieces", "10 pieces"],
    "bunch": ["1 bunch", "2 bunches", "3 bunches"],
    "dozen": ["1 dozen", "2 dozens", "3 dozens"],
    "500g":  ["1 pack (500g)", "2 packs", "3 packs"],
    "200g":  ["1 pack (200g)", "2 packs", "3 packs", "5 packs"],
    "250g":  ["1 pack (250g)", "2 packs", "3 packs"],
    "400g":  ["1 pack (400g)", "2 packs"],
    "100g":  ["1 pack (100g)", "2 packs", "5 packs"],
    "50g":   ["1 pack (50g)", "2 packs", "5 packs"],
    "150g":  ["1 pack (150g)", "2 packs"],
    "200ml": ["1 bottle (200ml)", "2 bottles", "3 bottles"],
}


# ── Session State ─────────────────────────────────────────────────────────────────
for k, v in [
    ("ranked_shops", None),
    ("matched_product", None),
    ("order_placed", False),
    ("order_details", {}),
    ("track_step", 0),
    ("searched_query", ""),
    ("sidebar_pick", ""),
]:
    if k not in st.session_state:
        st.session_state[k] = v


# ── Header ────────────────────────────────────────────────────────────────────────
st.markdown(
    '<div class="main-header">'
    '<div style="display:flex;align-items:center;gap:14px;">'
    '<div style="font-size:2rem;">&#x1F9E0;</div>'
    '<div><h1>AI SmartBuy System</h1>'
    '<p>Real-time AI shopping &nbsp;·&nbsp; 20 shops &nbsp;·&nbsp; 100 products &nbsp;·&nbsp; Distance-aware routing</p>'
    '</div></div></div>',
    unsafe_allow_html=True,
)


# ── Sidebar ───────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### &#x1F6D2; Browse Products")
    categories = sorted(set(p["category"] for p in db["products"]))
    sel_cat = st.selectbox("Filter by Category", ["All"] + categories)
    cat_prods = (db["products"] if sel_cat == "All"
                 else [p for p in db["products"] if p["category"] == sel_cat])
    st.markdown(f"**{len(cat_prods)} products**")
    for p in cat_prods:
        if st.button(f"{p['name']}  [{p['unit']}]", key=f"sb_{p['id']}", use_container_width=True):
            st.session_state.sidebar_pick = p["name"]
            st.rerun()
    st.markdown("---")
    st.markdown("&#x1F4CD; **Location:** Coimbatore, Tamil Nadu")
    st.caption(f"`{USER_LAT}°N, {USER_LON}°E`")


# ── Search Bar ────────────────────────────────────────────────────────────────────
prefill = st.session_state.sidebar_pick or st.session_state.searched_query
c1, c2  = st.columns([5, 1])
with c1:
    all_product_names = sorted([p["name"] for p in db["products"]])
    prefill_idx = all_product_names.index(prefill) if prefill in all_product_names else None
    query = st.selectbox(
        "", 
        options=all_product_names,
        index=prefill_idx,
        placeholder="&#x1F50D;  Search any product — tomato, ghee, chicken, milk...",
        label_visibility="collapsed",
    )
with c2:
    go = st.button("Search", use_container_width=True)

if go and query:
    st.session_state.sidebar_pick = ""
    with st.spinner("&#x26A1; AI Engine scoring 20 shops..."):
        time.sleep(0.4)
        prod, shops = search_product(query)
        if prod:
            st.session_state.ranked_shops    = shops
            st.session_state.matched_product = prod
            st.session_state.searched_query  = query.strip()
            st.session_state.order_placed    = False
            st.session_state.track_step      = 0
        else:
            st.error(f"&#x274C;  '{query}' not found. Try sidebar or check spelling.")

st.markdown("---")


# ── Main Results ──────────────────────────────────────────────────────────────────
if st.session_state.ranked_shops and st.session_state.matched_product:
    shops   = st.session_state.ranked_shops
    product = st.session_state.matched_product
    top     = shops[0]

    col_l, col_r = st.columns([1.15, 1], gap="large")

    # ═══ LEFT ════════════════════════════════════════════════════════════════════
    with col_l:

        st.markdown('<div class="section-title">AI Recommendation</div>', unsafe_allow_html=True)

        live_n  = random.randint(3, 12)
        urg_cls = "red" if top["stock"] <= 5 else ""
        urg_msg = (
            f"&#x1F6A8; Critical: Only {top['stock']} {product['unit']} left!"
            if top["stock"] <= 5
            else f"&#x2139;&#xFE0F;  {top['stock']} {product['unit']} available in stock."
        )

        card_html = (
            '<div class="must-buy-card">'
            '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">'
            '<span class="must-buy-badge">&#x1F525; Must Buy</span>'
            '<span style="font-size:.72rem;color:#ef4444;"><span class="live-dot"></span>Live</span>'
            '</div>'
            f'<div class="shop-big-name">{top["name"]}</div>'
            f'<div style="font-size:.78rem;color:#64748b;margin-bottom:10px;">&#x1F4CD; {top["area"]}, Coimbatore</div>'
            '<div class="dist-box">'
            '<div style="font-size:1.6rem;">&#x1F5FA;&#xFE0F;</div>'
            '<div>'
            f'<div class="dist-route">&#x1F4CF; {top["distance"]} km away from you</div>'
            f'<div class="dist-sub">&#x23F1; ~{top["travel_min"]} min travel time</div>'
            '</div></div>'
            '<div class="stat-grid">'
            f'<div class="stat-box"><div class="stat-label">Price / {product["unit"]}</div>'
            f'<div class="stat-value green">&#8377;{top["price"]}</div></div>'
            f'<div class="stat-box"><div class="stat-label">Distance</div>'
            f'<div class="stat-value blue">{top["distance"]} km</div></div>'
            f'<div class="stat-box"><div class="stat-label">Stock</div>'
            f'<div class="stat-value">{top["stock"]} {product["unit"]}</div></div>'
            '</div>'
            f'<div class="urgency-box {urg_cls}">{urg_msg}</div>'
            '<div style="display:flex;justify-content:space-between;font-size:.78rem;margin-bottom:4px;">'
            '<span style="color:#64748b;">AI Confidence Score</span>'
            f'<span style="font-weight:700;color:#2563eb;">{top["score"]}%</span>'
            '</div>'
            '<div style="background:#e2e8f0;border-radius:4px;height:7px;overflow:hidden;">'
            f'<div style="background:#2563eb;width:{top["score"]}%;height:100%;border-radius:4px;"></div>'
            '</div>'
            f'<div style="margin-top:9px;font-size:.73rem;color:#f97316;">'
            f'&#x1F525; {live_n} people bought <b>{product["name"]}</b> here in the last 10 mins'
            '</div></div>'
        )
        st.markdown(card_html, unsafe_allow_html=True)

        # Map
        st.markdown('<div class="section-title">Live Map — Your Location &#x2192; All Shops</div>', unsafe_allow_html=True)
        fmap = build_map(shops, top)
        st_folium(fmap, width="100%", height=430, returned_objects=[])
        st.caption("&#x1F7E2; Green = Best deal  &#x1F7E0; Orange = 2nd  &#x1F534; Red = Others  · Click any pin for details")

    # ═══ RIGHT ═══════════════════════════════════════════════════════════════════
    with col_r:

        # Comparison Table
        st.markdown('<div class="section-title">All Shops Comparison</div>', unsafe_allow_html=True)
        rows = ""
        for i, s in enumerate(shops):
            sc    = s["score"]
            badge = (f'<span class="score-green">{sc}</span>' if sc >= 75
                     else f'<span class="score-yellow">{sc}</span>' if sc >= 50
                     else f'<span class="score-red">{sc}</span>')
            cls   = "best-row" if i == 0 else ""
            nhtml = f"<strong>{s['name']}</strong>" if i == 0 else s["name"]
            rows += (
                f'<tr class="{cls}">'
                f'<td>{nhtml}<br><span style="font-size:.68rem;color:#94a3b8">{s["area"]}</span></td>'
                f'<td>&#8377;{s["price"]}<br><span style="font-size:.68rem;color:#94a3b8">per {product["unit"]}</span></td>'
                f'<td>{s["distance"]} km<br><span style="font-size:.68rem;color:#64748b">~{s["travel_min"]} min</span></td>'
                f'<td>{s["stock"]}<br><span style="font-size:.68rem;color:#94a3b8">{product["unit"]}</span></td>'
                f'<td>{badge}</td></tr>'
            )
        st.markdown(
            '<div style="background:white;border-radius:14px;border:1px solid #e2e8f0;overflow:hidden;margin-bottom:.8rem;">'
            '<table class="compare-table"><thead><tr>'
            '<th>Shop</th><th>Price</th><th>Distance</th><th>Stock</th><th>Score</th>'
            f'</tr></thead><tbody>{rows}</tbody></table></div>',
            unsafe_allow_html=True,
        )

        # ── Order Section ────────────────────────────────────────────────────────
        st.markdown('<div class="section-title">Place Order</div>', unsafe_allow_html=True)

        unit        = product["unit"]
        qty_options = UNIT_OPTIONS.get(unit, [f"1 {unit}", f"2 {unit}", f"3 {unit}", f"5 {unit}"])

        oc1, oc2 = st.columns(2)
        with oc1:
            qty_label = st.selectbox(f"Quantity ({unit})", qty_options, key="qty_select")
            try:
                qty_num = float(qty_label.split()[0])
            except Exception:
                qty_num = 1.0
        with oc2:
            delivery_date = st.date_input(
                "Delivery Date",
                value=date.today(),
                min_value=date.today(),
                key="del_date",
            )

        # ── AM/PM Time: 4 plain selectboxes, no st.time_input at all ────────────
        st.markdown('<p style="font-size:0.8rem;color:#374151;margin-bottom:4px;font-weight:500;">Delivery Time</p>', unsafe_allow_html=True)
        tc1, tc2, tc3, tc4 = st.columns(4)
        with tc1:
            sel_hour = st.selectbox("Hour", list(range(1, 13)),
                                    index=4, key="t_hour",
                                    label_visibility="collapsed")
        with tc2:
            sel_min  = st.selectbox("Minute", [f"{m:02d}" for m in range(60)],
                                    index=0, key="t_min",
                                    label_visibility="collapsed")
        with tc3:
            sel_sec  = st.selectbox("Second", [f"{s:02d}" for s in range(60)],
                                    index=0, key="t_sec",
                                    label_visibility="collapsed")
        with tc4:
            sel_ampm = st.selectbox("AMPM", ["AM", "PM"],
                                    index=1, key="t_ampm",
                                    label_visibility="collapsed")

        # ── Convert to 24h datetime ───────────────────────────────────────────────
        hour_24          = (sel_hour % 12) + (12 if sel_ampm == "PM" else 0)
        delivery_time_obj = dtime(hour_24, int(sel_min), int(sel_sec))
        delivery_time_str = f"{sel_hour:02d}:{sel_min}:{sel_sec} {sel_ampm}"
        delivery_dt       = datetime.combine(delivery_date, delivery_time_obj)

        # ── Past-time validation ──────────────────────────────────────────────────
        is_past = delivery_dt <= datetime.now()

        total_price = round(top["price"] * qty_num)
        st.markdown(
            '<div class="card" style="background:#f0fdf4;border:1px solid #bbf7d0;margin-bottom:.5rem;">'
            '<div style="display:flex;justify-content:space-between;align-items:center;">'
            '<span style="font-size:.8rem;color:#15803d;">&#x1F9FE; Order Summary</span>'
            f'<span style="font-size:1.1rem;font-weight:700;color:#15803d;">&#8377;{total_price}</span>'
            '</div>'
            f'<div style="font-size:.75rem;color:#64748b;margin-top:4px;">'
            f'{product["name"]} &nbsp;·&nbsp; {qty_label} &nbsp;·&nbsp; from {top["name"]}'
            f'<br>{delivery_date.strftime("%d %b %Y")} at {delivery_time_str}'
            '</div></div>',
            unsafe_allow_html=True,
        )

        if is_past:
            st.warning(
                f"&#x26A0;&#xFE0F; **{delivery_time_str} on "
                f"{delivery_date.strftime('%d %b %Y')}** is in the past. "
                "Please pick a future time."
            )

        order_btn = st.button(
            "&#x1F6D2; Confirm & Place Order",
            use_container_width=True,
            type="primary",
            disabled=is_past,
        )

        if order_btn and not is_past:
            if qty_num > top["stock"]:
                st.error(f"&#x274C; Only {top['stock']} {unit} in stock. Reduce quantity.")
            else:
                st.session_state.order_placed  = True
                st.session_state.track_step    = 1
                st.session_state.order_details = {
                    "shop":        top["name"],
                    "area":        top["area"],
                    "product":     product["name"],
                    "qty":         qty_label,
                    "price":       total_price,
                    "unit":        unit,
                    "dist":        top["distance"],
                    "eta":         top["travel_min"],
                    "date":        delivery_date.strftime("%d %b %Y"),
                    "time_str":    delivery_time_str,
                    "delivery_dt": delivery_dt.isoformat(),
                }
                st.rerun()

        # ── Order confirmed view ──────────────────────────────────────────────────
        if st.session_state.order_placed:
            od        = st.session_state.order_details
            stored_dt = datetime.fromisoformat(od["delivery_dt"])

            st.success(
                f"&#x2705; **Order Confirmed!** &nbsp; {od['qty']} of **{od['product']}** "
                f"from **{od['shop']}**, {od['area']}  \n"
                f"&#x1F4B0; &#8377;{od['price']} &nbsp;·&nbsp; "
                f"&#x1F4C5; {od['date']} &nbsp;·&nbsp; "
                f"&#x1F550; {od['time_str']} &nbsp;·&nbsp; "
                f"&#x1F4CF; {od['dist']} km"
            )

            # ── Live HH:MM:SS countdown ───────────────────────────────────────────
            # Uses st.empty so ONLY the countdown div is replaced each second.
            # st.rerun() is NOT used — avoids wiping order state.
            countdown_slot = st.empty()
            while True:
                diff      = stored_dt - datetime.now()
                total_sec = int(diff.total_seconds())
                if total_sec > 0:
                    hrs  = total_sec // 3600
                    mins = (total_sec % 3600) // 60
                    secs = total_sec % 60
                    hms  = f"{hrs:02d}:{mins:02d}:{secs:02d}"
                    countdown_slot.markdown(
                        '<div class="countdown-box">'
                        f'<div class="countdown-time">&#x23F3; {hms}</div>'
                        f'<div class="countdown-label">remaining until delivery on '
                        f'{od["date"]} at {od["time_str"]}</div>'
                        '</div>',
                        unsafe_allow_html=True,
                    )
                    time.sleep(1)
                else:
                    countdown_slot.markdown(
                        '<div class="countdown-box">'
                        '<div class="countdown-time">&#x1F389; Delivered!</div>'
                        f'<div class="countdown-label">Order delivered on {od["date"]} at {od["time_str"]}</div>'
                        '</div>',
                        unsafe_allow_html=True,
                    )
                    break

            # ── Order Tracking Steps ──────────────────────────────────────────────
            st.markdown('<div class="section-title">Live Order Tracking</div>', unsafe_allow_html=True)
            TRACK_STEPS = [
                ("&#x2713;",  "Order Confirmed",  "Payment processed successfully"),
                ("&#x1F4E6;", "Packing",           f"Items being packed at {od['shop']}"),
                ("&#x1F6F5;", "Out for Delivery",  f"On the way — {od['dist']} km · ~{od['eta']} min"),
                ("&#x1F3E0;", "Delivered",          "Enjoy your purchase! &#x2764;&#xFE0F;"),
            ]
            steps_html = ""
            for idx, (icon, label, sub) in enumerate(TRACK_STEPS):
                if idx < st.session_state.track_step:
                    css = "t-done";    ico = "&#x2713;"
                elif idx == st.session_state.track_step:
                    css = "t-active";  ico = icon
                else:
                    css = "t-pending"; ico = icon
                steps_html += (
                    '<div class="track-step">'
                    f'<div class="track-circle {css}">{ico}</div>'
                    f'<div><div class="track-label">{label}</div>'
                    f'<div class="track-sub">{sub}</div></div>'
                    '</div>'
                )
            st.markdown(f'<div class="card">{steps_html}</div>', unsafe_allow_html=True)

            if st.session_state.track_step < len(TRACK_STEPS) - 1:
                if st.button("&#x23E9; Simulate Next Step", use_container_width=True):
                    st.session_state.track_step += 1
                    st.rerun()
            else:
                st.balloons()
                st.success("&#x1F389; Delivered! Thank you for using AI SmartBuy.")

else:
    st.markdown(
        '<div class="empty-state">'
        '<div style="font-size:3rem;margin-bottom:1rem;">&#x1F50D;</div>'
        '<div style="font-size:1.1rem;font-weight:600;color:#475569;margin-bottom:.5rem;">'
        'Search any product to get started</div>'
        '<div style="font-size:.85rem;margin-bottom:1rem;">'
        '100 products &nbsp;·&nbsp; 20 shops &nbsp;·&nbsp; AI scoring &nbsp;·&nbsp; Distance routing</div>'
        '<div style="font-size:.82rem;color:#64748b;">'
        'Try: <b>tomato</b> &nbsp;·&nbsp; <b>rice</b> &nbsp;·&nbsp; <b>ghee</b> &nbsp;·&nbsp; '
        '<b>chicken</b> &nbsp;·&nbsp; <b>milk</b> &nbsp;·&nbsp; <b>eggs</b></div>'
        '</div>',
        unsafe_allow_html=True,
    )

st.markdown("---")
st.markdown(
    "<div style='text-align:center;font-size:.72rem;color:#94a3b8;'>"
    "&#x1F9E0; AI SmartBuy &nbsp;·&nbsp; 20 Shops &nbsp;·&nbsp; 100 Products &nbsp;·&nbsp; "
    "Haversine Distance &nbsp;·&nbsp; Weighted AI Scoring (Price 50% + Distance 30% + Stock 20%)"
    "</div>",
    unsafe_allow_html=True,
)