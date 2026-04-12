import streamlit as st
from streamlit_option_menu import option_menu

st.title("Menu Test")

if "cart_click" not in st.session_state:
    st.session_state.cart_click = False

if st.button("Programmatically Go to Cart"):
    st.session_state.my_menu = "Cart"
    st.session_state.cart_click = True

tabs = ["Home", "Inventory", "Cart"]
selected = option_menu(
    menu_title=None, 
    options=tabs,
    key="my_menu"
)

st.write("Selected:", selected)
st.write("Session State:", st.session_state)
