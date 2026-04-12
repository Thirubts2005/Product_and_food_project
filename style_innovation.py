import streamlit as st

def apply_innovation():
    """
    Injects a premium "Aura" design system into the Streamlit app.
    Features: Glassmorphism, Neon Accents, Premium Typography, and Animated Transitions.
    """
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&family=DM+Serif+Display&display=swap');

    :root {
        --primary-glow: rgba(99, 102, 241, 0.15);
        --accent-glow: rgba(14, 165, 233, 0.2);
        --glass-bg: rgba(15, 23, 42, 0.7);
        --glass-border: rgba(255, 255, 255, 0.1);
    }

    /* Global Typography & Background */
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
        color: #e2e8f0;
    }
    
    .stApp {
        background: radial-gradient(circle at 50% 0%, #1e293b 0%, #0f172a 100%);
        background-attachment: fixed;
    }

    /* Glassmorphism Sidebar */
    section[data-testid="stSidebar"] {
        background: rgba(15, 23, 42, 0.95) !important;
        backdrop-filter: blur(20px);
        border-right: 1px solid var(--glass-border);
    }

    /* Innovation Header */
    .main-header {
        background: linear-gradient(135deg, #6366f1 0%, #0ea5e9 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-family: 'DM Serif Display', serif;
        font-size: 3.5rem !important;
        font-weight: 700;
        text-align: center;
        padding: 2rem 0;
        margin-bottom: 2rem;
        filter: drop-shadow(0 0 10px rgba(14, 165, 233, 0.3));
    }

    /* Glass Cards */
    .stMarkdown div[data-testid="stMarkdownContainer"] .card, 
    div[data-testid="metric-container"], 
    .stTabs [data-baseweb="tabpanel"] {
        background: var(--glass-bg);
        backdrop-filter: blur(12px);
        border: 1px solid var(--glass-border);
        border-radius: 20px;
        padding: 1.5rem;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        transition: all 0.3s ease;
    }

    div[data-testid="metric-container"]:hover {
        transform: translateY(-5px);
        border-color: rgba(14, 165, 233, 0.5);
        box-shadow: 0 12px 40px 0 rgba(14, 165, 233, 0.2);
    }

    /* Animated Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.6rem 2rem !important;
        font-weight: 600 !important;
        letter-spacing: 0.5px !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: 0 4px 15px rgba(99, 102, 241, 0.3) !important;
    }

    .stButton > button:hover {
        transform: scale(1.02) translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(168, 85, 247, 0.4) !important;
        filter: brightness(1.1);
    }

    /* Inputs & Selectboxes */
    .stTextInput input, .stSelectbox [data-baseweb="select"], .stTextArea textarea {
        background: rgba(30, 41, 59, 0.5) !important;
        border: 1px solid var(--glass-border) !important;
        border-radius: 12px !important;
        color: #f1f5f9 !important;
    }

    .stTextInput input:focus {
        border-color: #0ea5e9 !important;
        box-shadow: 0 0 0 2px rgba(14, 165, 233, 0.2) !important;
    }

    /* Custom Badges */
    .badge-aura {
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.1), rgba(14, 165, 233, 0.1));
        border: 1px solid rgba(14, 165, 233, 0.3);
        color: #0ea5e9;
        padding: 4px 12px;
        border-radius: 100px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background: transparent;
    }

    .stTabs [data-baseweb="tab"] {
        background: rgba(30, 41, 59, 0.5);
        border: 1px solid var(--glass-border);
        border-radius: 12px 12px 0 0;
        color: #94a3b8;
        padding: 10px 20px;
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #6366f1 0%, #0ea5e9 100%) !important;
        color: white !important;
    }

    /* Hide default Streamlit elements if any remain */
    #MainMenu, footer, header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)
