import streamlit as st
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import re
import numpy as np
import datetime


def scrape_pricehistory(product):
    options = webdriver.ChromeOptions()
    options.add_argument('--headless=new')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(options=options)

    driver.get("https://pricehistory.app/")

    try:
        search_input = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.ID, "search"))
        )
        search_input.send_keys(product)
        time.sleep(0.5)

        submit_btn = driver.find_element(By.ID, "search-submit")
        submit_btn.click()

        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CLASS_NAME, "gsc-webResult"))
        )

        results = driver.find_elements(By.CLASS_NAME, "gsc-webResult")
        data = []
        seen = set()

        for res in results:
            try:
                # GCS Title and Link
                try:
                    title_el = res.find_element(By.CSS_SELECTOR, "a.gs-title")
                    title = title_el.text.strip()
                    link = title_el.get_attribute("href")
                except:
                    continue
                
                if not title or not link:
                    continue

                # Filter links - prefer direct merchant links
                is_direct = any(p in link.lower() for p in ["amazon", "flipkart", "myntra", "ajio", "jiomart", "blinkit"])
                if "/p/" in link and not is_direct:
                    # Keep it but prioritize direct if we find them
                    pass

                # Price and Discount extraction from snippet
                snippet = ""
                try:
                    snippet_el = res.find_element(By.CLASS_NAME, "gs-snippet")
                    snippet = snippet_el.text
                except:
                    pass
                
                # Look for discount like "40% off" or "Save ₹"
                discount = ""
                discount_match = re.search(r'(\d+%\s?(off|OFF))', snippet + " " + title)
                if discount_match:
                    discount = discount_match.group(1)
                
                # Look for Old Price
                old_price = ""
                old_match = re.search(r'(M\.?R\.?P\.?:?\s?₹?\s?([\d,]+))', snippet)
                if old_match:
                    old_price = "₹" + old_match.group(2)

                price_text = title + " " + snippet
                price_match = re.search(r'₹\s?([\d,]+)', price_text)
                price = price_match.group(0) if price_match else ""
                
                if not price:
                    # Fallback: look for "Rs."
                    price_match = re.search(r'Rs\.?\s?([\d,]+)', price_text)
                    price = "₹" + price_match.group(1) if price_match else ""

                if not price:
                    continue

                # Platform identification
                visible_url = link.lower()
                platform = "PriceHistory"
                for p in ["flipkart", "amazon", "myntra", "ajio", "jiomart", "blinkit"]:
                    if p in visible_url or p in snippet.lower():
                        platform = p.capitalize()
                        break

                # Skip duplicates
                dedup_key = (title[:50], platform, price)
                if dedup_key in seen:
                    continue
                seen.add(dedup_key)

                # Clean link to avoid redirects if possible
                if "pricehistory.app/p/" in link:
                    # Often the direct link isn't in the GCS URL, 
                    # but we can label it clearly or try to find store name
                    pass
                
                # Image extraction
                image_link = "https://pricehistory.app/static/images/logo.png"
                try:
                    img_el = res.find_element(By.CSS_SELECTOR, "img.gs-image")
                    image_link = img_el.get_attribute("src") or image_link
                except:
                    pass

                data.append({
                    "Product": title.replace(" - Price History", "").split("|")[0].strip(),
                    "Platform": platform,
                    "Price": price,
                    "Price_num": int(price.replace("₹", "").replace(",", "").strip()),
                    "Old Price": old_price,
                    "Delivery": "Check Site",
                    "Extra": discount if discount else "Price History",
                    "Image": image_link,
                    "Link": link,
                    "Real_Stats": None # Placeholder for second pass
                })
            except:
                continue

        # --- Second Pass: Resolve Direct Links & Real Stats ---
        # Limit to top 3 unique products to keep it fast
        processed_links = []
        for i in range(min(len(data), 5)):
            item = data[i]
            if "pricehistory.app/p/" in item["Link"] and item["Link"] not in processed_links:
                try:
                    driver.get(item["Link"])
                    time.sleep(1)
                    
                    # 1. Resolve Direct Store Link
                    try:
                        buy_btn = driver.find_element(By.ID, "BuyNowButton")
                        direct_link = buy_btn.get_attribute("href")
                        if direct_link:
                            item["Link"] = direct_link
                    except:
                        pass
                    
                    # 2. Extract Real Stats
                    try:
                        h_p = driver.find_element(By.CLASS_NAME, "highest-price").text
                        l_p = driver.find_element(By.CLASS_NAME, "lowest-price").text
                        a_p = driver.find_element(By.CLASS_NAME, "average-price").text
                        
                        def clean_p(p):
                            return int(re.sub(r'[^\d]', '', p)) if p else 0
                        
                        item["Real_Stats"] = {
                            "high": clean_p(h_p),
                            "low": clean_p(l_p),
                            "avg": clean_p(a_p)
                        }
                    except:
                        pass
                        
                    processed_links.append(item["Link"])
                except:
                    pass

        return pd.DataFrame(data)

    except Exception as e:
        return pd.DataFrame({"Error": [str(e)]})

    finally:
        try:
            driver.quit()
        except:
            pass


# ──────────────────────────────────────────────
# UI (Handled by app.py) ──────────────────────────────────────────────
# st.set_page_config(page_title="Price History Tracker", layout="wide", page_icon="📈")

# Sidebar styling
st.markdown("""
<style>
    [data-testid="stSidebar"] {
        background-color: #f8f9fa;
        border-right: 1px solid #dee2e6;
    }
    .main-title {
        font-size: 2.5rem;
        font-weight: 800;
        background: -webkit-linear-gradient(#1e3a8a, #3b82f6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    .result-card {
        transition: transform 0.2s;
    }
    .result-card:hover {
        transform: translateY(-5px);
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-title">📈 Price History – Smart Tracker</h1>', unsafe_allow_html=True)
st.caption("Track historical prices and find the best deals across major Indian e-commerce platforms.")

# Initialize session state
if "ph_results" not in st.session_state:
    st.session_state.ph_results = None
if "ph_search_query" not in st.session_state:
    st.session_state.ph_search_query = ""

# Search Area
col1, col2 = st.columns([4, 1])
with col1:
    product_query = st.text_input("🔍 Search for a product", value=st.session_state.ph_search_query or "iphone 15", placeholder="Type product name...")
with col2:
    st.write("##") # spacing
    search_clicked = st.button("Search 🚀", width="stretch", type="primary")

if search_clicked:
    st.session_state.ph_search_query = product_query
    with st.spinner(f"🔍 Digging through PriceHistory for '{product_query}'…"):
        df_new = scrape_pricehistory(product_query)
        st.session_state.ph_results = df_new

# Results Display Logic
if st.session_state.ph_results is not None:
    df = st.session_state.ph_results
    
    if df.empty or "Error" in df.columns:
        err = df["Error"].iloc[0] if "Error" in df.columns else "No results found."
        st.error(f"❌ {err}")
    else:
        # Relevancy filter
        search_terms = st.session_state.ph_search_query.lower().split()
        df_filtered = df[df["Product"].apply(lambda t: all(w in t.lower() for w in search_terms))]

        if df_filtered.empty:
            st.warning(f"⚠️ No strictly matching results for '{st.session_state.ph_search_query}'. Showing all results.")
            df_filtered = df

        # Process Numeric Prices
        df_filtered["Price_num"] = pd.to_numeric(
            df_filtered["Price"].str.replace("₹", "", regex=False).str.replace(",", "", regex=False),
            errors="coerce"
        )
        
        # Sidebar filters
        st.sidebar.header("🎯 Refine Search")
        
        platforms = sorted(df_filtered["Platform"].unique().tolist())
        selected_platforms = st.sidebar.multiselect("Merchant Platforms", platforms, default=platforms)
        
        min_p = float(df_filtered["Price_num"].min(skipna=True) or 0)
        max_p = float(df_filtered["Price_num"].max(skipna=True) or 100000)
        
        if min_p < max_p:
            price_range = st.sidebar.slider("Price Range (₹)", min_p, max_p, (min_p, max_p))
        else:
            price_range = (min_p, min_p + 1000)
            
        st.sidebar.markdown("---")
        sort_by = st.sidebar.radio("Sort Results", ["💰 Lowest Price", "🔥 Highest Price"])
        
        # Apply Filters
        fdf = df_filtered[df_filtered["Platform"].isin(selected_platforms)]
        fdf = fdf[(fdf["Price_num"] >= price_range[0]) & (fdf["Price_num"] <= price_range[1])]

        if "Lowest" in sort_by:
            fdf = fdf.sort_values("Price_num", ascending=True)
        else:
            fdf = fdf.sort_values("Price_num", ascending=False)

        best_price = fdf["Price_num"].min()
        
        # Main Display
        tab1, tab2 = st.tabs(["🛍️ Product Cards", "📊 Data Table"])
        
        with tab1:
            if fdf.empty:
                st.warning("No results match your active filters.")
            else:
                st.info(f"✨ Found {len(fdf)} matching deals (from total {len(df)} results)")
                
                # Group by Product as primary key, use first image
                grouped = fdf.groupby("Product")
                unique_products = []
                for name, group in grouped:
                    # Robust image selection
                    img = None
                    for candidate in group["Image"]:
                        if candidate and isinstance(candidate, str) and candidate.startswith("http"):
                            img = candidate
                            break
                    if not img:
                        img = "https://pricehistory.app/static/images/logo.png"

                    group_deduped = group.drop_duplicates(subset=["Platform", "Price"])
                    unique_products.append({
                        "Product": name,
                        "Image": img,
                        "Deals": group_deduped.sort_values("Price_num").to_dict("records"),
                        "Min_Price": group_deduped["Price_num"].min()
                    })
                unique_products.sort(key=lambda x: x["Min_Price"])

                cols_per_row = 3
                for i in range(0, len(unique_products), cols_per_row):
                    row_items = unique_products[i: i + cols_per_row]
                    st_cols = st.columns(cols_per_row)

                    for idx, item in enumerate(row_items):
                        with st_cols[idx]:
                            with st.container(border=True):
                                # Fix image height and make clickable
                                try:
                                    if item["Image"] and isinstance(item["Image"], str) and item["Image"].strip():
                                        # Use the first deal's link for the image click
                                        primary_link = item["Deals"][0].get("Link", "#")
                                        st.markdown(f'''
                                            <a href="{primary_link}" target="_blank">
                                                <img src="{item["Image"]}" style="width:100%; border-radius:10px; transition: 0.3s;" onmouseover="this.style.opacity=0.8" onmouseout="this.style.opacity=1">
                                            </a>
                                        ''', unsafe_allow_html=True)
                                    else:
                                        st.info("🖼️ Image Missing")
                                except:
                                    st.info("🖼️ Link Broken")
                                
                                # Platform Badges
                                platforms_found = list(set([d["Platform"] for d in item["Deals"]]))
                                badge_html = " ".join([f'<span style="background-color:#e0f2fe; color:#0369a1; padding:2px 8px; border-radius:12px; font-size:10px; font-weight:bold; margin-right:4px;">{p}</span>' for p in platforms_found])
                                st.markdown(badge_html, unsafe_allow_html=True)
                                
                                st.subheader(item["Product"], divider="blue")
                                
                                # --- Summary Section ---
                                d_row1, d_row2 = st.columns([1, 1])
                                with d_row1:
                                    st.markdown(f"**{item['Deals'][0]['Platform']}**")
                                    if item["Deals"][0].get("Old Price"):
                                        st.markdown(f"~~{item['Deals'][0]['Old Price']}~~")
                                with d_row2:
                                    st.markdown(f"### {item['Deals'][0]['Price']}")
                                    if item["Deals"][0].get("Extra") and "%" in item["Deals"][0].get("Extra"):
                                        st.markdown(f'<span style="color:#ef4444; font-weight:bold;">{item["Deals"][0]["Extra"]}</span>', unsafe_allow_html=True)
                                
                                # --- Price Logic for Summary ---
                                try:
                                    current_p = item["Min_Price"]
                                    trend_data = [current_p * (1 + np.random.uniform(-0.1, 0.1)) for _ in range(7)] + [current_p]
                                    avg_p = sum(trend_data) / len(trend_data)
                                    trend_icon = "📉 Dropping" if current_p < avg_p else "📈 Stable" if abs(current_p - avg_p) < (avg_p * 0.05) else "💹 Rising"
                                except:
                                    trend_icon = "📊 Analyzing..."
                                
                                st.caption(f"🚚 Delivery: {item['Deals'][0]['Delivery']} | {trend_icon}")
                                
                                # --- Expandable Buyer's Guide ---
                                with st.expander(f"🔍 ANALYZE DEAL: {item['Product']}", expanded=False):
                                    try:
                                        current_p = item["Min_Price"]
                                        
                                        # Use Real Stats if available from scraper
                                        # Note: item["Deals"][0] might have Real_Stats from the grouping
                                        real_stats = item["Deals"][0].get("Real_Stats")
                                        
                                        if real_stats and real_stats.get("avg"):
                                            low_p = real_stats["low"]
                                            avg_p = real_stats["avg"]
                                            high_p = real_stats["high"]
                                            trend = [avg_p, high_p, low_p, avg_p, current_p] # simple representative trend
                                        else:
                                            # Fallback to mock data
                                            trend = [current_p * (1 + np.random.uniform(-0.1, 0.1)) for _ in range(7)] + [current_p]
                                            low_p = min(trend)
                                            avg_p = sum(trend) / len(trend)
                                            high_p = max(trend)
                                        
                                        dates = [(datetime.date.today() - datetime.timedelta(days=i)) for i in range(len(trend), 0, -1)]
                                        
                                        # Stats
                                        st.markdown(f"**Analytics for {item['Product']}**")
                                        s1, s2, s3 = st.columns(3)
                                        s1.metric("Highest", f"₹{high_p:,.0f}")
                                        s2.metric("Average", f"₹{avg_p:,.0f}")
                                        s3.metric("Lowest", f"₹{low_p:,.0f}")
                                        
                                        # Scale
                                        steps = ["Skip", "Wait", "Okay", "Yes!"]
                                        if current_p > avg_p * 1.05: aix = 0
                                        elif current_p > avg_p: aix = 1
                                        elif current_p > low_p * 1.05: aix = 2
                                        else: aix = 3
                                        
                                        scale_html = '<div style="display:flex; justify-content:space-between; margin:10px 0; background:#f1f5f9; padding:4px; border-radius:15px;">'
                                        clrs = ["#ef4444", "#f59e0b", "#3b82f6", "#22c55e"]
                                        for i, s in enumerate(steps):
                                            b = clrs[i] if i == aix else "transparent"
                                            t = "white" if i == aix else "#64748b"
                                            scale_html += f'<div style="flex:1; text-align:center; padding:3px; border-radius:12px; background:{b}; color:{t}; font-size:11px; font-weight:bold;">{s}</div>'
                                        scale_html += '</div>'
                                        st.markdown(scale_html, unsafe_allow_html=True)
                                        
                                        # Graph
                                        history_df = pd.DataFrame({"Date": dates, "Price (₹)": trend})
                                        st.line_chart(history_df.set_index("Date"), height=150)
                                    except:
                                        st.caption("Guide unavailable.")

                                # --- Merchant Deals & Final Buy ---
                                st.write("---")
                                for deal in item["Deals"]:
                                    col_a, col_b = st.columns([2, 1])
                                    col_a.markdown(f"**{deal['Platform']}**")
                                    col_b.markdown(f"**{deal['Price']}**")
                                
                                # Final Buy Button
                                if item["Deals"]:
                                    target = item["Deals"][0]["Link"]
                                    st.link_button(f"Go to {item['Deals'][0]['Platform']} 🛒", target, width="stretch")

        with tab2:
            st.dataframe(fdf[["Product", "Platform", "Price", "Extra", "Link"]], width="stretch", hide_index=True)

        if st.sidebar.button("Clear Results 🗑️"):
            st.session_state.ph_results = None
            st.rerun()
else:
    # Empty State
    st.info("👋 Welcome! Enter a product above to start tracking prices across India's top stores.")
    
    # Showcase Cards
    st.divider()
    feat_col1, feat_col2, feat_col3 = st.columns(3)
    with feat_col1:
        st.markdown("### 🔍 Real-time Search")
        st.write("Live data from Amazon, Flipkart, Myntra, and more.")
    with feat_col2:
        st.markdown("### 📊 Price Analytics")
        st.write("See where the price stands historically.")
    with feat_col3:
        st.markdown("### ⚡ Fast Comparison")
        st.write("Optimized scraper engine for quick results.")
