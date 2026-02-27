import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from . import data as D

LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="DM Sans", color="#e2e8f0"),
    margin=dict(l=10, r=10, t=30, b=10),
    legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor="#1f2d40"),
)


def compute_recession_score(sahm: pd.Series, spread2: pd.Series, spread3m: pd.Series) -> pd.Series:
    """
    Composite recession probability score (0–100).
    Weights:
      - Sahm Rule (40%): triggered (>=0.5) contributes full weight
      - 10Y–2Y Inversion (30%): negative and deepening
      - 10Y–3M Inversion (30%): most reliable Fed indicator
    """
    dates = sahm.index.union(spread2.index).union(spread3m.index)
    sahm_r   = sahm.reindex(dates, method="ffill")
    spread2_r = spread2.reindex(dates, method="ffill")
    spread3m_r = spread3m.reindex(dates, method="ffill")

    # Sahm signal: 0 to 40 based on 0 to 0.5+ range
    sahm_score = (sahm_r.clip(0, 0.8) / 0.8 * 40).fillna(0)

    # 10Y-2Y: max 30 pts when deeply inverted (-1 bps or below)
    s2_score = (-spread2_r.clip(-1.5, 0) / 1.5 * 30).fillna(0)

    # 10Y-3M: max 30 pts
    s3_score = (-spread3m_r.clip(-2.0, 0) / 2.0 * 30).fillna(0)

    total = (sahm_score + s2_score + s3_score).clip(0, 100)
    return total.round(1)


def render(api_key: str):
    st.markdown('<div class="page-title">Recession Radar</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Composite Risk Score · Sahm Rule · Yield Curve Signals · NBER Tracking</div>', unsafe_allow_html=True)
    st.markdown("<hr class='divider'>", unsafe_allow_html=True)

    if not api_key:
        st.markdown("<div class='info-box'>Enter your FRED API key in the sidebar.</div>", unsafe_allow_html=True)
        return

    with st.spinner("Loading recession indicators..."):
        try:
            ids = ["SAHMREALTIME", "T10Y2Y", "T10Y3M", "UNRATE", "PAYEMS", "INDPRO", "USREC"]
            df = D.fetch_many(ids, api_key, start="1990-01-01")
        except Exception as e:
            st.error(f"Error: {e}"); return

    def safe(sid):
        return df[sid].dropna() if sid in df.columns else pd.Series(dtype=float)

    sahm    = safe("SAHMREALTIME")
    sp2     = safe("T10Y2Y")
    sp3     = safe("T10Y3M")
    unrate  = safe("UNRATE")
    payems  = safe("PAYEMS")
    indpro  = safe("INDPRO")
    recessions = safe("USREC")
    bands   = D.recession_bands(recessions)

    # Compute composite score
    score_series = compute_recession_score(sahm, sp2, sp3)
    current_score = round(score_series.iloc[-1], 1) if not score_series.empty else 0

    # ── Composite Gauge ──────────────────────────────────────────────────────
    col_gauge, col_signals = st.columns([1, 2])

    with col_gauge:
        gauge_color = "#ff4757" if current_score >= 60 else "#f5c842" if current_score >= 35 else "#00e5a0"
        label = "HIGH RISK" if current_score >= 60 else "ELEVATED" if current_score >= 35 else "LOW RISK"

        fig_g = go.Figure(go.Indicator(
            mode="gauge+number",
            value=current_score,
            domain={"x": [0, 1], "y": [0, 1]},
            title={"text": "RECESSION RISK SCORE",
                   "font": {"family": "DM Mono", "size": 11, "color": "#64748b"}},
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#1f2d40",
                          "tickfont": {"family": "DM Mono", "size": 10, "color": "#64748b"}},
                "bar": {"color": gauge_color, "thickness": 0.3},
                "bgcolor": "#111827",
                "borderwidth": 1,
                "bordercolor": "#1f2d40",
                "steps": [
                    {"range": [0, 35],  "color": "rgba(0,229,160,0.08)"},
                    {"range": [35, 60], "color": "rgba(245,200,66,0.08)"},
                    {"range": [60, 100],"color": "rgba(255,71,87,0.08)"},
                ],
                "threshold": {
                    "line": {"color": gauge_color, "width": 3},
                    "thickness": 0.75,
                    "value": current_score,
                },
            },
            number={"font": {"family": "Playfair Display", "size": 52, "color": gauge_color},
                    "suffix": "/100"},
        ))
        fig_g.update_layout(paper_bgcolor="rgba(0,0,0,0)", height=280,
                             margin=dict(l=20, r=20, t=40, b=10))
        st.plotly_chart(fig_g, use_container_width=True)

        css = "signal-risk" if current_score >= 60 else "signal-caution" if current_score >= 35 else "signal-safe"
        st.markdown(f'<div style="text-align:center"><span class="signal-badge {css}">{label}</span></div>', unsafe_allow_html=True)
        st.markdown("""
        <div style='font-family: DM Mono, monospace; font-size: 10px; color: #2d3f55;
                    text-align: center; margin-top: 12px; line-height: 1.8;'>
            Sahm Rule 40% · 10Y–2Y 30% · 10Y–3M 30%
        </div>
        """, unsafe_allow_html=True)

    with col_signals:
        st.markdown('<div class="section-header" style="font-size:16px;">Individual Signals</div>', unsafe_allow_html=True)

        # Signal rows
        def signal_row(name, value, threshold, unit="", desc="", higher_is_bad=True):
            triggered = value >= threshold if higher_is_bad else value <= threshold
            css = "signal-risk" if triggered else "signal-safe"
            badge = "TRIGGERED" if triggered else "CLEAR"
            st.markdown(f"""
            <div style="display:flex; justify-content:space-between; align-items:center;
                        padding: 12px 16px; background: #111827; border: 1px solid #1f2d40;
                        border-radius: 8px; margin-bottom: 8px;">
                <div>
                    <div style="font-family: DM Sans; font-weight:500; font-size:14px;">{name}</div>
                    <div style="font-family: DM Mono, monospace; font-size:11px; color:#64748b; margin-top:2px;">{desc}</div>
                </div>
                <div style="text-align:right;">
                    <div style="font-family: Playfair Display, serif; font-size:22px; font-weight:700;">
                        {value:.2f}{unit}
                    </div>
                    <span class="signal-badge {css}">{badge}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

        sahm_val = D.latest(sahm)
        sp2_val  = D.latest(sp2)
        sp3_val  = D.latest(sp3)

        signal_row("Sahm Rule", sahm_val, 0.5, "", "Triggered at ≥ 0.50 — recession likely begun", higher_is_bad=True)
        signal_row("10Y – 2Y Spread", sp2_val, 0, " bps", "Negative = inverted", higher_is_bad=False)
        signal_row("10Y – 3M Spread", sp3_val, 0, " bps", "Fed's preferred indicator", higher_is_bad=False)

    st.markdown("<hr class='divider'>", unsafe_allow_html=True)

    # ── Historical score + components ────────────────────────────────────────
    st.markdown('<div class="section-header">Composite Score History</div>', unsafe_allow_html=True)

    fig2 = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.05,
                         subplot_titles=["Composite Recession Risk Score (0–100)",
                                          "Sahm Rule Indicator (threshold: 0.50)",
                                          "Yield Curve Spreads (10Y–2Y & 10Y–3M)"])

    # Composite score
    fig2.add_trace(go.Scatter(x=score_series.index, y=score_series.values,
                               line=dict(color="#ff6b35", width=2),
                               fill="tozeroy", fillcolor="rgba(255,107,53,0.08)",
                               name="Risk Score"), row=1, col=1)
    fig2.add_hline(y=60, line=dict(color="#ff4757", width=1, dash="dash"), row=1, col=1)
    fig2.add_hline(y=35, line=dict(color="#f5c842", width=1, dash="dash"), row=1, col=1)

    # Sahm
    if not sahm.empty:
        fig2.add_trace(go.Scatter(x=sahm.index, y=sahm.values,
                                   line=dict(color="#00d4ff", width=2),
                                   fill="tozeroy", fillcolor="rgba(0,212,255,0.06)",
                                   name="Sahm"), row=2, col=1)
        fig2.add_hline(y=0.5, line=dict(color="#ff4757", width=1.5, dash="dash"), row=2, col=1)

    # Spreads
    if not sp2.empty:
        fig2.add_trace(go.Scatter(x=sp2.index, y=sp2.values,
                                   line=dict(color="#f5c842", width=1.5), name="10Y–2Y"), row=3, col=1)
    if not sp3.empty:
        fig2.add_trace(go.Scatter(x=sp3.index, y=sp3.values,
                                   line=dict(color="#00e5a0", width=1.5), name="10Y–3M"), row=3, col=1)
    fig2.add_hline(y=0, line=dict(color="#ff4757", width=1, dash="dash"), row=3, col=1)

    for band in bands:
        for r in [1, 2, 3]:
            fig2.add_vrect(x0=band["x0"], x1=band["x1"],
                           fillcolor="rgba(100,116,139,0.12)", line_width=0, row=r, col=1)

    fig2.update_layout(**LAYOUT, height=680, showlegend=False)
    fig2.update_annotations(font=dict(family="DM Mono", size=11, color="#64748b"))
    for r in [1, 2, 3]:
        fig2.update_xaxes(gridcolor="#1f2d40", row=r, col=1)
        fig2.update_yaxes(gridcolor="#1f2d40", row=r, col=1)
    st.plotly_chart(fig2, use_container_width=True)

    st.markdown("<hr class='divider'>", unsafe_allow_html=True)

    # ── Labor market ─────────────────────────────────────────────────────────
    st.markdown('<div class="section-header">Labor Market</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)

    with c1:
        fig3 = go.Figure()
        if not unrate.empty:
            fig3.add_trace(go.Scatter(x=unrate.index, y=unrate.values,
                                       line=dict(color="#ff6b35", width=2),
                                       fill="tozeroy", fillcolor="rgba(255,107,53,0.07)", name="Unemployment Rate"))
        for band in bands:
            fig3.add_vrect(x0=band["x0"], x1=band["x1"], fillcolor="rgba(100,116,139,0.10)", line_width=0)
        fig3.update_layout(**LAYOUT, height=280, title="Unemployment Rate (%)",
                           xaxis=dict(gridcolor="#1f2d40"), yaxis=dict(gridcolor="#1f2d40"))
        st.plotly_chart(fig3, use_container_width=True)

    with c2:
        if not payems.empty:
            payems_mom = payems.diff()
            fig4 = go.Figure()
            colors_pay = ["#ff4757" if v < 0 else "#00e5a0" for v in payems_mom.values]
            fig4.add_trace(go.Bar(x=payems_mom.index, y=payems_mom.values,
                                   marker_color=colors_pay, opacity=0.8, name="MoM Change"))
            for band in bands:
                fig4.add_vrect(x0=band["x0"], x1=band["x1"], fillcolor="rgba(100,116,139,0.10)", line_width=0)
            fig4.update_layout(**LAYOUT, height=280, title="Nonfarm Payrolls MoM Change (thousands)",
                               xaxis=dict(gridcolor="#1f2d40"), yaxis=dict(gridcolor="#1f2d40"))
            st.plotly_chart(fig4, use_container_width=True)

    # ── Methodology note ─────────────────────────────────────────────────────
    with st.expander("📖 Methodology — Composite Recession Risk Score"):
        st.markdown("""
        <div style='font-family: DM Sans; font-size: 14px; line-height: 1.8; color: #94a3b8;'>
        <b style='color: #e2e8f0'>How the composite score is calculated:</b><br><br>

        The score runs from 0 to 100 and combines three leading recession indicators:

        <br><br><b style='color:#00d4ff'>Sahm Rule (40% weight)</b><br>
        Created by economist Claudia Sahm. Triggered when the 3-month moving average of unemployment rises by ≥0.5pp above its 12-month low. Score scales linearly from 0 to 0.8 reading → 0 to 40 points.

        <br><br><b style='color:#f5c842'>10Y–2Y Spread (30% weight)</b><br>
        The classic recession warning signal. Points accrue when the spread turns negative. A reading of -1.5 bps contributes the full 30 points.

        <br><br><b style='color:#00e5a0'>10Y–3M Spread (30% weight)</b><br>
        Preferred by the NY Fed for recession probability models. Historically more reliable than 2Y. Max 30 points at -2.0 bps inversion.

        <br><br><b style='color: #e2e8f0'>Thresholds:</b>
        🔴 ≥60 = High Risk &nbsp;|&nbsp; 🟡 35–59 = Elevated &nbsp;|&nbsp; 🟢 &lt;35 = Low Risk

        <br><br>This is an educational model — not a trading signal.
        </div>
        """, unsafe_allow_html=True)
