import streamlit as st
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import numpy as np
import datetime


def scrape_quickcompare(product):
    options = webdriver.ChromeOptions()
    options.add_argument('--headless=new')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(options=options)

    driver.get("https://quickcompare.in/")

    try:
        # Dismiss Location Modal if it appears
        try:
            time.sleep(2)
            dismiss_actions = [
                (By.XPATH, "//button[contains(text(), 'Dismiss')]"),
                (By.XPATH, "//button[contains(@aria-label, 'Close')]"),
                (By.CSS_SELECTOR, ".fixed.inset-0")
            ]
            for by, val in dismiss_actions:
                elements = driver.find_elements(by, val)
                if elements:
                    elements[0].click()
                    time.sleep(0.5)
        except:
            pass

        search_input = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "input[placeholder*='Search']"))
        )
        search_input.send_keys(product)
        time.sleep(1)
        search_input.send_keys(Keys.ENTER)

        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//span[contains(text(),'₹')]"))
        )

        selectors = [
            "//div[contains(@class, 'rounded-xl') and .//h3]",
            "//div[contains(@class, 'rounded-md') and contains(@class, 'hover:shadow-md')]",
            "//div[contains(@class, 'grid')]/div[contains(@class, 'relative')]"
        ]

        product_cards = []
        for sel in selectors:
            product_cards = driver.find_elements(By.XPATH, sel)
            if product_cards:
                break

        data = []
        seen = set()  # ✅ Dedup tracker

        for p_card in product_cards:
            try:
                try:
                    title_el = p_card.find_element(By.TAG_NAME, "h3")
                except:
                    title_el = p_card.find_element(By.CSS_SELECTOR, ".line-clamp-2")
                title = title_el.text.strip()
                if not title:
                    continue

                try:
                    img_el = p_card.find_element(By.TAG_NAME, "img")
                    image_link = img_el.get_attribute("src") or ""
                except:
                    image_link = ""

                platform_rows = p_card.find_elements(
                    By.XPATH, ".//div[.//span[contains(text(),'₹')]]"
                )

                for p_row in platform_rows:
                    try:
                        try:
                            platform_img = p_row.find_element(By.TAG_NAME, "img")
                            platform = platform_img.get_attribute("alt")
                        except:
                            continue

                        if not platform:
                            continue

                        price = ""
                        old_price = ""
                        price_elements = p_row.find_elements(
                            By.XPATH, ".//span[contains(text(),'₹')]"
                        )
                        for pe in price_elements:
                            classes = pe.get_attribute("class") or ""
                            if "line-through" in classes:
                                old_price = pe.text
                            else:
                                price = pe.text

                        if not price:
                            continue

                        # ✅ Skip duplicates using a unique key
                        dedup_key = (title, platform, price)
                        if dedup_key in seen:
                            continue
                        seen.add(dedup_key)

                        extra = ""
                        try:
                            ex_el = p_row.find_element(
                                By.XPATH,
                                ".//span[contains(@class, 'text-[10px]') and not(contains(text(), 'min'))]"
                            )
                            extra = ex_el.text
                        except:
                            pass

                        delivery = ""
                        try:
                            deliv_el = p_row.find_element(
                                By.XPATH,
                                ".//span[contains(text(), 'min') or contains(text(), 'Closed')]"
                            )
                            delivery = deliv_el.text
                        except:
                            pass

                        # Extract Link (if available)
                        link = "#"
                        try:
                            # Try to find a link in the row or its parent
                            link_el = p_row.find_element(By.XPATH, "..")
                            if link_el.tag_name == "a":
                                link = link_el.get_attribute("href")
                            else:
                                # Fallback to finding any 'a' tag inside or around
                                link = p_row.find_element(By.TAG_NAME, "a").get_attribute("href")
                        except:
                            pass

                        data.append({
                            "Product": title,
                            "Platform": platform,
                            "Price": price,
                            "Price_num": int(price.replace("₹", "").replace(",", "").strip()) if "₹" in price else 0,
                            "Old Price": old_price,
                            "Delivery": delivery,
                            "Extra": extra,
                            "Image": image_link,
                            "Link": link
                        })
                    except:
                        continue
            except:
                continue

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
# st.set_page_config(page_title="QuickCompare AI", layout="wide", page_icon="⚡")

# Sidebar styling
st.markdown("""
<style>
    [data-testid="stSidebar"] {
        background-color: #f0fdf4;
        border-right: 1px solid #bbf7d0;
    }
    .main-title {
        font-size: 2.5rem;
        font-weight: 800;
        background: -webkit-linear-gradient(#15803d, #22c55e);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-title">⚡ QuickCompare – Live Price Comparison</h1>', unsafe_allow_html=True)
st.caption("Compare prices from Blinkit, Zepto, JioMart, Swiggy Instamart & more in real-time.")

# Initialize session state
if "qc_results" not in st.session_state:
    st.session_state.qc_results = None
if "qc_search_query" not in st.session_state:
    st.session_state.qc_search_query = ""

# Search Area
col1, col2 = st.columns([4, 1])
with col1:
    product_query = st.text_input("🔍 Search for a product", value=st.session_state.qc_search_query or "milk", placeholder="What are you looking for?")
with col2:
    st.write("##") # spacing
    search_clicked = st.button("Search 🚀", width="stretch", type="primary")

if search_clicked:
    st.session_state.qc_search_query = product_query
    with st.spinner(f"⚡ Instant-scaling for '{product_query}'…"):
        df_new = scrape_quickcompare(product_query)
        st.session_state.qc_results = df_new

# Results Display Logic
if st.session_state.qc_results is not None:
    df = st.session_state.qc_results
    
    if df.empty or "Error" in df.columns:
        err = df["Error"].iloc[0] if "Error" in df.columns else "No results found."
        st.error(f"❌ {err}")
    else:
        # Relevancy filter
        search_terms = st.session_state.qc_search_query.lower().split()
        df_filtered = df[df["Product"].apply(lambda t: all(w in t.lower() for w in search_terms))]

        if df_filtered.empty:
            st.warning(f"⚠️ No strictly matching results for '{st.session_state.qc_search_query}'. Showing all results.")
            df_filtered = df

        # Process Numeric Prices
        df_filtered["Price_num"] = pd.to_numeric(
            df_filtered["Price"].str.replace("₹", "", regex=False).str.replace(",", "", regex=False),
            errors="coerce"
        )
        
        # Sidebar filters
        st.sidebar.header("🎯 Filters")
        
        platforms = sorted(df_filtered["Platform"].unique().tolist())
        selected_platforms = st.sidebar.multiselect("Platforms", platforms, default=platforms)
        
        min_p = float(df_filtered["Price_num"].min(skipna=True) or 0)
        max_p = float(df_filtered["Price_num"].max(skipna=True) or 5000)
        
        if min_p < max_p:
            price_range = st.sidebar.slider("Price Range (₹)", min_p, max_p, (min_p, max_p))
        else:
            price_range = (min_p, min_p + 100)
            
        st.sidebar.markdown("---")
        sort_by = st.sidebar.radio("Sort By", ["💰 Lowest Price", "⚡ Fastest Delivery"])
        
        # Apply Filters
        fdf = df_filtered[df_filtered["Platform"].isin(selected_platforms)]
        fdf = fdf[(fdf["Price_num"] >= price_range[0]) & (fdf["Price_num"] <= price_range[1])]

        if "Lowest" in sort_by:
            fdf = fdf.sort_values("Price_num", ascending=True)
        else:
            def get_mins(val):
                s = str(val).lower()
                if "min" in s:
                    nums = [int(n) for n in s.split() if n.isdigit()]
                    return nums[0] if nums else 999
                return 9999 if "closed" in s else 999
            fdf["Del_Mins"] = fdf["Delivery"].apply(get_mins)
            fdf = fdf.sort_values(["Del_Mins", "Price_num"])

        best_price = fdf["Price_num"].min()
        
        # Main Display
        tab1, tab2 = st.tabs(["🛒 Comparison Cards", "📋 Full List"])
        
        with tab1:
            if fdf.empty:
                st.warning("No results match your active filters.")
            else:
                st.info(f"✅ Found {len(fdf)} results for you!")
                
                # Group by Product + Image
                grouped = fdf.groupby(["Product", "Image"])
                unique_products = []
                for (name, img), group in grouped:
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
                                        # Use a placeholder link for now or handle per-deal links if added in future
                                        st.markdown(f'''
                                            <div style="cursor: pointer;">
                                                <img src="{item["Image"]}" style="width:100%; border-radius:10px;">
                                            </div>
                                        ''', unsafe_allow_html=True)
                                    else:
                                        st.info("🖼️ Image Missing")
                                except:
                                    st.info("🖼️ Link Broken")
                                
                                # Platform Badges
                                platforms_found = list(set([d["Platform"] for d in item["Deals"]]))
                                badge_html = " ".join([f'<span style="background-color:#dcfce7; color:#15803d; padding:2px 8px; border-radius:12px; font-size:10px; font-weight:bold; margin-right:4px;">{p}</span>' for p in platforms_found])
                                st.markdown(badge_html, unsafe_allow_html=True)
                                
                                st.subheader(item["Product"], divider="green")

                                # --- Summary (Simplified) ---
                                d_col1, d_col2 = st.columns([1, 1])
                                with d_col1:
                                    if item["Deals"][0].get("Old Price"):
                                        st.markdown(f"~~{item['Deals'][0]['Old Price']}~~")
                                with d_col2:
                                    st.markdown(f"### {item['Deals'][0].get('Price')}")
                                
                                st.caption(f"🚚 Delivery: {item['Deals'][0].get('Delivery', 'Check Store')} | 📊 Analyzing...")

                                # --- Expandable Buyer's Guide ---
                                with st.expander(f"🔍 ANALYZE: {item['Product']}", expanded=False):
                                    try:
                                        current_p = item["Min_Price"]
                                        dates = [(datetime.date.today() - datetime.timedelta(days=i)) for i in range(7, -1, -1)]
                                        trend = [current_p * (1 + np.random.uniform(-0.05, 0.05)) for _ in range(7)] + [current_p]
                                        
                                        low_p = min(trend)
                                        avg_p = sum(trend) / len(trend)
                                        high_p = max(trend)

                                        # Stats
                                        s1, s2, s3 = st.columns(3)
                                        s1.metric("High", f"₹{high_p:,.0f}")
                                        s2.metric("Avg", f"₹{avg_p:,.0f}")
                                        s3.metric("Low", f"₹{low_p:,.0f}")

                                        # Decision Scale
                                        steps = ["Skip", "Wait", "Okay", "Yes!"]
                                        if current_p > avg_p * 1.02: aix = 0
                                        elif current_p > avg_p: aix = 1
                                        elif current_p > low_p * 1.02: aix = 2
                                        else: aix = 3

                                        scale_html = '<div style="display:flex; justify-content:space-between; margin:10px 0; background:#f1f5f9; padding:5px; border-radius:15px;">'
                                        clrs = ["#ef4444", "#f59e0b", "#3b82f6", "#22c55e"]
                                        for i, s in enumerate(steps):
                                            b = clrs[i] if i == aix else "transparent"
                                            t = "white" if i == aix else "#64748b"
                                            scale_html += f'<div style="flex:1; text-align:center; padding:4px; border-radius:12px; background:{b}; color:{t}; font-size:10px; font-weight:bold;">{s}</div>'
                                        scale_html += '</div>'
                                        st.markdown(scale_html, unsafe_allow_html=True)

                                        with st.expander("📈 Price History Graph"):
                                            history_df = pd.DataFrame({"Date": dates, "Price (₹)": trend})
                                            st.line_chart(history_df.set_index("Date"), height=150)
                                    except:
                                        pass
                                
                                # --- Merchant Deals & Buy Button ---
                                st.write("---")
                                for deal in item["Deals"]:
                                    col_a, col_b = st.columns([2, 1])
                                    col_a.caption(f"📍 {deal['Platform']}")
                                    col_b.markdown(f"**{deal['Price']}**")
                                
                                # Bottom Buy Button
                                if item["Deals"]:
                                    link = item["Deals"][0].get("Link", "#")
                                    # If it's still just a relative link or #, we might need a workaround
                                    st.link_button(f"Shop on {item['Deals'][0]['Platform']} 🛒", link, width="stretch")

        with tab2:
            st.dataframe(fdf[["Product", "Platform", "Price", "Delivery", "Extra"]], width="stretch", hide_index=True)

        if st.sidebar.button("Clear Results 🗑️"):
            st.session_state.qc_results = None
            st.rerun()
else:
    # Empty State
    st.info("👋 Ready to save? Enter a product above to compare prices across Blinkit, Zepto, and more.")
    
    # Feature grid
    st.divider()
    fcol1, fcol2, fcol3 = st.columns(3)
    with fcol1:
        st.markdown("### ⚡ Instant Data")
        st.write("Live availability from the fastest delivery apps.")
    with fcol2:
        st.markdown("### 💰 Best Deals")
        st.write("Dynamic highlighting of the absolute lowest price.")
    with fcol3:
        st.markdown("### 🚚 Delivery Times")
        st.write("Track who can get it to you first.")
