import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from . import data as D

PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="DM Sans", color="#e2e8f0"),
    xaxis=dict(gridcolor="#1f2d40", showgrid=True, zeroline=False),
    yaxis=dict(gridcolor="#1f2d40", showgrid=True, zeroline=False),
    margin=dict(l=10, r=10, t=30, b=10),
    legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor="#1f2d40"),
)


def metric_card(label, value, delta=None, delta_label="", invert=False, suffix=""):
    if delta is not None:
        if delta > 0:
            cls = "delta-up" if not invert else "delta-down"
            arrow = "▲"
        elif delta < 0:
            cls = "delta-down" if not invert else "delta-up"
            arrow = "▼"
        else:
            cls = "delta-neut"
            arrow = "–"
        delta_html = f'<div class="metric-delta {cls}">{arrow} {abs(delta):.2f}{suffix} {delta_label}</div>'
    else:
        delta_html = ""

    val_str = f"{value:.2f}{suffix}" if isinstance(value, float) else str(value)
    return f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{val_str}</div>
        {delta_html}
    </div>
    """


def render(api_key: str):
    st.markdown('<div class="page-title">Macro Intelligence</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">United States · Real-Time Economic Monitor</div>', unsafe_allow_html=True)
    st.markdown("<hr class='divider'>", unsafe_allow_html=True)

    if not api_key:
        st.markdown("""
        <div class='info-box' style='font-size:14px; padding: 20px;'>
            👈 Enter your <b>FRED API key</b> in the sidebar to load live data.
            It's free and takes 30 seconds to get at <b>fred.stlouisfed.org</b>
        </div>
        """, unsafe_allow_html=True)
        _render_demo()
        return

    with st.spinner("Fetching macro data from FRED..."):
        try:
            ids = ["DGS2", "DGS10", "T10Y2Y", "T10Y3M", "CPIAUCSL", "CPILFESL",
                   "PCEPILFE", "T10YIE", "DFII10", "SAHMREALTIME", "UNRATE", "USREC"]
            df = D.fetch_many(ids, api_key)
        except Exception as e:
            st.error(f"Failed to fetch data: {e}")
            return

    # ── Key metrics row ──────────────────────────────────────────────────────
    st.markdown('<div class="section-header">Key Indicators</div>', unsafe_allow_html=True)

    cols = st.columns(4)

    def safe(sid):
        return df[sid] if sid in df.columns else pd.Series(dtype=float)

    with cols[0]:
        s = safe("T10Y2Y")
        v = D.latest(s); ch = v - D.prev(s, 20)
        badge = "🔴 INVERTED" if v < 0 else "🟡 FLAT" if v < 0.5 else "🟢 NORMAL"
        st.markdown(metric_card("10Y–2Y Spread", v, ch, "vs 1M ago", suffix=" bps") +
                    f'<div style="margin-top:8px"><span class="signal-badge {"signal-risk" if v<0 else "signal-caution" if v<0.5 else "signal-safe"}">{badge}</span></div>',
                    unsafe_allow_html=True)

    with cols[1]:
        s = safe("CPIAUCSL")
        v = D.yoy_change(s); ch = v - D.yoy_change(s.iloc[:-1])
        badge = "🔴 HIGH" if v > 4 else "🟡 ELEVATED" if v > 2.5 else "🟢 STABLE"
        st.markdown(metric_card("CPI YoY", v, ch, "MoM change", suffix="%") +
                    f'<div style="margin-top:8px"><span class="signal-badge {"signal-risk" if v>4 else "signal-caution" if v>2.5 else "signal-safe"}">{badge}</span></div>',
                    unsafe_allow_html=True)

    with cols[2]:
        s = safe("PCEPILFE")
        v = D.yoy_change(s); ch = v - D.yoy_change(s.iloc[:-1])
        badge = "🔴 ABOVE TARGET" if v > 3 else "🟡 WATCH" if v > 2 else "🟢 AT TARGET"
        st.markdown(metric_card("Core PCE YoY", v, ch, "MoM change", suffix="%") +
                    f'<div style="margin-top:8px"><span class="signal-badge {"signal-risk" if v>3 else "signal-caution" if v>2 else "signal-safe"}">{badge}</span></div>',
                    unsafe_allow_html=True)

    with cols[3]:
        s = safe("SAHMREALTIME")
        v = D.latest(s); ch = v - D.prev(s, 3)
        badge = "🔴 TRIGGERED" if v >= 0.5 else "🟡 RISING" if v >= 0.3 else "🟢 CLEAR"
        st.markdown(metric_card("Sahm Rule", v, ch, "vs 3M ago", suffix="") +
                    f'<div style="margin-top:8px"><span class="signal-badge {"signal-risk" if v>=0.5 else "signal-caution" if v>=0.3 else "signal-safe"}">{badge}</span></div>',
                    unsafe_allow_html=True)

    st.markdown("<hr class='divider'>", unsafe_allow_html=True)

    # ── Secondary metrics ────────────────────────────────────────────────────
    st.markdown('<div class="section-header">Rates & Real Yields</div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        s = safe("DGS10")
        st.markdown(metric_card("10Y Treasury", D.latest(s), D.latest(s) - D.prev(s, 20), "vs 1M", suffix="%"), unsafe_allow_html=True)
    with c2:
        s = safe("DGS2")
        st.markdown(metric_card("2Y Treasury", D.latest(s), D.latest(s) - D.prev(s, 20), "vs 1M", suffix="%"), unsafe_allow_html=True)
    with c3:
        s = safe("DFII10")
        st.markdown(metric_card("10Y Real Yield", D.latest(s), D.latest(s) - D.prev(s, 20), "vs 1M", suffix="%"), unsafe_allow_html=True)
    with c4:
        s = safe("T10YIE")
        st.markdown(metric_card("10Y Breakeven", D.latest(s), D.latest(s) - D.prev(s, 20), "vs 1M", suffix="%"), unsafe_allow_html=True)

    st.markdown("<hr class='divider'>", unsafe_allow_html=True)

    # ── Overview chart ───────────────────────────────────────────────────────
    st.markdown('<div class="section-header">Historical Overview</div>', unsafe_allow_html=True)

    recessions = safe("USREC")
    bands = D.recession_bands(recessions)

    fig = make_subplots(rows=2, cols=2,
                        subplot_titles=["10Y–2Y Spread (bps)", "CPI vs Core PCE YoY (%)",
                                        "10Y Real Yield vs Breakeven", "Sahm Rule Indicator"],
                        shared_xaxes=False, vertical_spacing=0.12, horizontal_spacing=0.08)

    colors = {"accent": "#00d4ff", "accent2": "#ff6b35", "green": "#00e5a0", "gold": "#f5c842", "red": "#ff4757"}

    # 10Y-2Y
    s = safe("T10Y2Y").dropna()
    if not s.empty:
        fig.add_trace(go.Scatter(x=s.index, y=s.values, line=dict(color=colors["accent"], width=1.5),
                                 fill="tozeroy", fillcolor="rgba(0,212,255,0.06)", name="10Y–2Y"), row=1, col=1)
        fig.add_hline(y=0, line=dict(color=colors["red"], width=1, dash="dash"), row=1, col=1)

    # CPI vs Core PCE
    cpi = safe("CPIAUCSL").dropna()
    pce = safe("PCEPILFE").dropna()
    if not cpi.empty:
        cpi_yoy = cpi.pct_change(12) * 100
        fig.add_trace(go.Scatter(x=cpi_yoy.index, y=cpi_yoy.values, line=dict(color=colors["accent2"], width=1.5), name="CPI YoY"), row=1, col=2)
    if not pce.empty:
        pce_yoy = pce.pct_change(12) * 100
        fig.add_trace(go.Scatter(x=pce_yoy.index, y=pce_yoy.values, line=dict(color=colors["gold"], width=1.5), name="Core PCE YoY"), row=1, col=2)
    fig.add_hline(y=2, line=dict(color=colors["green"], width=1, dash="dot"), row=1, col=2)

    # Real yield vs breakeven
    ry = safe("DFII10").dropna()
    be = safe("T10YIE").dropna()
    if not ry.empty:
        fig.add_trace(go.Scatter(x=ry.index, y=ry.values, line=dict(color=colors["green"], width=1.5), name="Real Yield"), row=2, col=1)
    if not be.empty:
        fig.add_trace(go.Scatter(x=be.index, y=be.values, line=dict(color=colors["gold"], width=1.5), name="Breakeven"), row=2, col=1)

    # Sahm rule
    sahm = safe("SAHMREALTIME").dropna()
    if not sahm.empty:
        fig.add_trace(go.Scatter(x=sahm.index, y=sahm.values, line=dict(color=colors["red"], width=1.5),
                                 fill="tozeroy", fillcolor="rgba(255,71,87,0.07)", name="Sahm Rule"), row=2, col=2)
        fig.add_hline(y=0.5, line=dict(color=colors["gold"], width=1, dash="dash"), row=2, col=2)

    # Recession shading
    for band in bands:
        for r, c in [(1,1),(1,2),(2,1),(2,2)]:
            fig.add_vrect(x0=band["x0"], x1=band["x1"], fillcolor="rgba(100,116,139,0.10)",
                          line_width=0, row=r, col=c)

    fig.update_layout(**PLOTLY_LAYOUT, height=600,
                      title_text="", showlegend=True)
    fig.update_annotations(font=dict(family="DM Mono", size=11, color="#64748b"))

    for i in range(1, 3):
        for j in range(1, 3):
            fig.update_xaxes(gridcolor="#1f2d40", showgrid=True, zeroline=False, row=i, col=j)
            fig.update_yaxes(gridcolor="#1f2d40", showgrid=True, zeroline=False, row=i, col=j)

    st.plotly_chart(fig, use_container_width=True)


def _render_demo():
    st.markdown("""
    <div style='text-align:center; padding: 60px 20px; color: #2d3f55;'>
        <div style='font-family: Playfair Display, serif; font-size: 36px; font-weight: 900; color: #1f2d40;'>
            Dashboard Preview
        </div>
        <div style='font-family: DM Mono, monospace; font-size: 12px; letter-spacing: 0.1em; margin-top: 12px;'>
            ADD YOUR FREE FRED API KEY TO ACTIVATE LIVE DATA
        </div>
        <div style='margin-top: 24px; display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;'>
            <span class='signal-badge signal-risk'>10Y–2Y Spread</span>
            <span class='signal-badge signal-caution'>CPI YoY</span>
            <span class='signal-badge signal-safe'>Core PCE</span>
            <span class='signal-badge signal-caution'>Sahm Rule</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
