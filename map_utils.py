import json
import math
import folium
import streamlit as st

@st.cache_data
def load_db():
    try:
        with open("db.json", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"shops": [], "products": [], "stock": []}

db = load_db()
SHOPS_MAP = {s["id"]: s for s in db.get("shops", [])}
PRODUCTS_MAP = {p["id"]: p for p in db.get("products", [])}
PRODUCT_NAME_INDEX = {p["name"].lower(): p for p in db.get("products", [])}

@st.cache_data
def build_stock_index():
    idx = {}
    for entry in db.get("stock", []):
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

# ── Fixed location: Coimbatore
USER_LAT = 10.9010
USER_LON = 76.9558

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
    if not shops_raw: return []
    prices    = [s["price"]    for s in shops_raw]
    distances = [s["distance"] for s in shops_raw]
    stocks    = [s["stock"]    for s in shops_raw]
    
    ps = [1 - p for p in normalize(prices)] if prices else []
    ds = [1 - d for d in normalize(distances)] if distances else []
    ss = normalize(stocks) if stocks else []
    
    scored = []
    for i, s in enumerate(shops_raw):
        raw = 0.50 * ps[i] + 0.30 * ds[i] + 0.20 * ss[i]
        scored.append({**s, "score": round(raw * 100)})
    return sorted(scored, key=lambda x: x["score"], reverse=True)

def search_product(query):
    q = query.strip().lower()
    
    # Filter common conversational filler words from start of query for voice/natural chat
    stop_words = ["the", "a", "an", "some", "any", "find", "search", "for", "buy", "get"]
    changed = True
    while changed:
        changed = False
        for word in stop_words:
            if q.startswith(f"{word} "):
                q = q[len(word)+1:].strip()
                changed = True

    matched = None
    for name, prod in PRODUCT_NAME_INDEX.items():
        if q in name or name in q:
            matched = prod
            break
    if not matched: return None, []
    
    pid = matched["id"]
    raw = STOCK_INDEX.get(pid, [])
    if not raw: return matched, []
    
    raw_copy = [dict(s) for s in raw]
    for s in raw_copy:
        s["distance"]   = haversine(USER_LAT, USER_LON, s["lat"], s["lon"])
        s["travel_min"] = travel_min(s["distance"])
    return matched, ai_score_shops(raw_copy)

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
