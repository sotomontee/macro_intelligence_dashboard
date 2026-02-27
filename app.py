import streamlit as st

st.set_page_config(
    page_title="Macro Intelligence Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Global CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@300;400;500&family=Playfair+Display:wght@700;900&family=DM+Sans:wght@300;400;500&display=swap');

:root {
  --bg:        #0a0e17;
  --surface:   #111827;
  --border:    #1f2d40;
  --accent:    #00d4ff;
  --accent2:   #ff6b35;
  --green:     #00e5a0;
  --red:       #ff4757;
  --text:      #e2e8f0;
  --muted:     #64748b;
  --gold:      #f5c842;
}

html, body, [data-testid="stAppViewContainer"] {
    background-color: var(--bg) !important;
    color: var(--text) !important;
    font-family: 'DM Sans', sans-serif;
}

[data-testid="stSidebar"] {
    background-color: var(--surface) !important;
    border-right: 1px solid var(--border);
}

[data-testid="stSidebar"] * { color: var(--text) !important; }

.stSelectbox > div > div, .stMultiSelect > div > div {
    background-color: var(--surface) !important;
    border: 1px solid var(--border) !important;
    color: var(--text) !important;
}

/* Hide default streamlit branding */
#MainMenu, footer, header { visibility: hidden; }

/* Metric cards */
.metric-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px 24px;
    position: relative;
    overflow: hidden;
}
.metric-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, var(--accent), transparent);
}
.metric-label {
    font-family: 'DM Mono', monospace;
    font-size: 11px;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 8px;
}
.metric-value {
    font-family: 'Playfair Display', serif;
    font-size: 32px;
    font-weight: 900;
    line-height: 1;
    color: var(--text);
}
.metric-delta {
    font-family: 'DM Mono', monospace;
    font-size: 12px;
    margin-top: 6px;
}
.delta-up   { color: var(--red);   }
.delta-down { color: var(--green); }
.delta-neut { color: var(--muted); }

/* Section headers */
.section-header {
    font-family: 'Playfair Display', serif;
    font-size: 22px;
    font-weight: 700;
    color: var(--text);
    border-bottom: 1px solid var(--border);
    padding-bottom: 10px;
    margin-bottom: 20px;
}

/* Signal badges */
.signal-badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 20px;
    font-family: 'DM Mono', monospace;
    font-size: 11px;
    font-weight: 500;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}
.signal-risk  { background: rgba(255,71,87,0.15);  color: var(--red);   border: 1px solid rgba(255,71,87,0.3);  }
.signal-caution { background: rgba(245,200,66,0.15); color: var(--gold);  border: 1px solid rgba(245,200,66,0.3); }
.signal-safe  { background: rgba(0,229,160,0.15);  color: var(--green); border: 1px solid rgba(0,229,160,0.3);  }

/* Page title */
.page-title {
    font-family: 'Playfair Display', serif;
    font-size: 42px;
    font-weight: 900;
    background: linear-gradient(135deg, var(--accent), var(--green));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    line-height: 1.1;
}
.page-subtitle {
    font-family: 'DM Mono', monospace;
    font-size: 12px;
    letter-spacing: 0.15em;
    color: var(--muted);
    text-transform: uppercase;
    margin-top: 4px;
}

hr.divider {
    border: none;
    border-top: 1px solid var(--border);
    margin: 24px 0;
}

/* Plotly chart background fix */
.js-plotly-plot .plotly { background: transparent !important; }

.stTabs [data-baseweb="tab-list"] {
    background-color: var(--surface);
    border-radius: 8px;
    gap: 4px;
    padding: 4px;
    border: 1px solid var(--border);
}
.stTabs [data-baseweb="tab"] {
    background-color: transparent;
    color: var(--muted) !important;
    font-family: 'DM Mono', monospace;
    font-size: 12px;
    letter-spacing: 0.08em;
    border-radius: 6px;
}
.stTabs [aria-selected="true"] {
    background-color: var(--accent) !important;
    color: var(--bg) !important;
}

.info-box {
    background: rgba(0, 212, 255, 0.05);
    border: 1px solid rgba(0, 212, 255, 0.2);
    border-radius: 8px;
    padding: 12px 16px;
    font-size: 13px;
    color: var(--muted);
    font-family: 'DM Sans', sans-serif;
    margin-bottom: 16px;
}
</style>
""", unsafe_allow_html=True)

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='padding: 20px 0 10px 0;'>
        <div style='font-family: Playfair Display, serif; font-size: 20px; font-weight: 900; color: #00d4ff;'>
            MACRO INTEL
        </div>
        <div style='font-family: DM Mono, monospace; font-size: 10px; letter-spacing: 0.15em; color: #64748b; text-transform: uppercase; margin-top: 2px;'>
            Intelligence Dashboard v1.0
        </div>
    </div>
    <hr style='border-color: #1f2d40; margin: 10px 0 20px 0;'>
    """, unsafe_allow_html=True)

    page = st.radio(
        "Navigation",
        ["🏠  Overview", "📈  Yield Curve Lab", "🔥  Inflation Monitor", "🚨  Recession Radar"],
        label_visibility="collapsed"
    )

    st.markdown("<hr style='border-color: #1f2d40; margin: 20px 0;'>", unsafe_allow_html=True)

    # Try Streamlit Cloud secrets first, fall back to manual input
    try:
        fred_key = st.secrets["FRED_API_KEY"]
        st.markdown("<div class='info-box'>✅ API key loaded automatically.</div>", unsafe_allow_html=True)
    except:
        fred_key = st.text_input(
            "FRED API Key",
            type="password",
            placeholder="Paste your key here",
            help="Get a free key at fred.stlouisfed.org/docs/api/api_key.html"
        )
        if not fred_key:
            st.markdown("""
            <div class='info-box'>
                🔑 Enter your free FRED API key to load live data.<br><br>
                Get one at <b>fred.stlouisfed.org</b> — takes 30 seconds.
            </div>
            """, unsafe_allow_html=True)

    st.markdown("""
    <div style='position: absolute; bottom: 20px; font-family: DM Mono, monospace; font-size: 10px; color: #2d3f55; letter-spacing: 0.1em;'>
        DATA: FRED · ST. LOUIS FED
    </div>
    """, unsafe_allow_html=True)

# ── Route pages ──────────────────────────────────────────────────────────────
if "🏠" in page:
    from pages_src import overview
    overview.render(fred_key)
elif "📈" in page:
    from pages_src import yield_curve
    yield_curve.render(fred_key)
elif "🔥" in page:
    from pages_src import inflation
    inflation.render(fred_key)
elif "🚨" in page:
    from pages_src import recession
    recession.render(fred_key)
