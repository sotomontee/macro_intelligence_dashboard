import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from . import data as D

LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="DM Sans", color="#e2e8f0"),
    margin=dict(l=10, r=10, t=30, b=10),
    legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor="#1f2d40"),
)


def render(api_key: str):
    st.markdown('<div class="page-title">Inflation Monitor</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">CPI · PCE · Real Yields · Breakeven Inflation</div>', unsafe_allow_html=True)
    st.markdown("<hr class='divider'>", unsafe_allow_html=True)

    if not api_key:
        st.markdown("<div class='info-box'>Enter your FRED API key in the sidebar.</div>", unsafe_allow_html=True)
        return

    with st.spinner("Loading inflation data..."):
        try:
            ids = ["CPIAUCSL", "CPILFESL", "PCEPI", "PCEPILFE", "MICH", "T10YIE", "DFII10", "USREC"]
            df = D.fetch_many(ids, api_key, start="1990-01-01")
        except Exception as e:
            st.error(f"Error: {e}"); return

    recessions = df["USREC"].dropna() if "USREC" in df.columns else pd.Series()
    bands = D.recession_bands(recessions)

    def safe(sid):
        return df[sid].dropna() if sid in df.columns else pd.Series(dtype=float)

    # ── Key metrics ──────────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    metrics = [
        ("CPI YoY", "CPIAUCSL", "yoy"),
        ("Core CPI YoY", "CPILFESL", "yoy"),
        ("Core PCE YoY", "PCEPILFE", "yoy"),
        ("10Y Breakeven", "T10YIE", "latest"),
    ]
    for col, (label, sid, mode) in zip([c1, c2, c3, c4], metrics):
        s = safe(sid)
        if mode == "yoy":
            v = D.yoy_change(s)
            ch = v - D.yoy_change(s.iloc[:-1]) if len(s) > 14 else 0
        else:
            v = D.latest(s)
            ch = v - D.prev(s, 20)
        target_diff = v - 2.0
        css = "signal-risk" if target_diff > 2 else "signal-caution" if target_diff > 0.5 else "signal-safe"
        badge = "🔴 ABOVE TARGET" if target_diff > 2 else "🟡 ELEVATED" if target_diff > 0.5 else "🟢 NEAR TARGET"
        col.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{v:.2f}%</div>
            <div class="metric-delta {'delta-up' if ch > 0 else 'delta-down' if ch < 0 else 'delta-neut'}">
                {'▲' if ch>0 else '▼' if ch<0 else '–'} {abs(ch):.2f}% recent change
            </div>
            <div style="margin-top:8px"><span class="signal-badge {css}">{badge}</span></div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<hr class='divider'>", unsafe_allow_html=True)

    tabs = st.tabs(["📊  CPI vs PCE", "🔬  Core Decomposition", "💡  Real Yields", "🎯  Fed Target Tracker"])

    # ── Tab 1 ────────────────────────────────────────────────────────────────
    with tabs[0]:
        cpi  = safe("CPIAUCSL")
        cpic = safe("CPILFESL")
        pce  = safe("PCEPI")
        pcec = safe("PCEPILFE")

        cpi_yoy  = cpi.pct_change(12) * 100
        cpic_yoy = cpic.pct_change(12) * 100
        pce_yoy  = pce.pct_change(12) * 100
        pcec_yoy = pcec.pct_change(12) * 100

        fig = go.Figure()
        for series, label, color, dash in [
            (cpi_yoy,  "CPI",       "#ff6b35", "solid"),
            (cpic_yoy, "Core CPI",  "#00d4ff", "dash"),
            (pce_yoy,  "PCE",       "#f5c842", "solid"),
            (pcec_yoy, "Core PCE",  "#00e5a0", "dash"),
        ]:
            if not series.empty:
                fig.add_trace(go.Scatter(x=series.index, y=series.values,
                                         line=dict(color=color, width=2, dash=dash), name=label))

        fig.add_hline(y=2, line=dict(color="#ffffff", width=1, dash="dot"), annotation_text="Fed 2% Target",
                      annotation_font=dict(family="DM Mono", size=10, color="#64748b"))

        for band in bands:
            fig.add_vrect(x0=band["x0"], x1=band["x1"], fillcolor="rgba(100,116,139,0.10)", line_width=0)

        fig.update_layout(**LAYOUT, height=420, title="CPI vs PCE: YoY Inflation (%)",
                          xaxis=dict(gridcolor="#1f2d40"), yaxis=dict(gridcolor="#1f2d40", title="YoY %"))
        st.plotly_chart(fig, use_container_width=True)

    # ── Tab 2: Core decomposition ────────────────────────────────────────────
    with tabs[1]:
        st.markdown('<div class="info-box">Core measures strip food & energy. The gap between headline and core CPI shows the contribution of volatile components.</div>', unsafe_allow_html=True)

        cpi_yoy  = safe("CPIAUCSL").pct_change(12) * 100
        cpic_yoy = safe("CPILFESL").pct_change(12) * 100

        common = cpi_yoy.index.intersection(cpic_yoy.index)
        cpi_aligned  = cpi_yoy.reindex(common).dropna()
        cpic_aligned = cpic_yoy.reindex(common).dropna()
        common = cpi_aligned.index.intersection(cpic_aligned.index)
        gap = (cpi_aligned.reindex(common) - cpic_aligned.reindex(common))

        fig2 = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.08,
                             subplot_titles=["Headline vs Core CPI", "Food & Energy Contribution (Headline – Core)"])

        fig2.add_trace(go.Scatter(x=cpi_aligned.index, y=cpi_aligned.values,
                                   line=dict(color="#ff6b35", width=2), name="CPI"), row=1, col=1)
        fig2.add_trace(go.Scatter(x=cpic_aligned.index, y=cpic_aligned.values,
                                   line=dict(color="#00d4ff", width=2), name="Core CPI"), row=1, col=1)
        fig2.add_hline(y=2, line=dict(color="#ffffff", width=1, dash="dot"), row=1, col=1)

        colors_gap = ["#ff4757" if v > 0 else "#00e5a0" for v in gap.values]
        fig2.add_trace(go.Bar(x=gap.index, y=gap.values, marker_color=colors_gap,
                              name="F&E Gap", opacity=0.8), row=2, col=1)
        fig2.add_hline(y=0, line=dict(color="#64748b", width=1), row=2, col=1)

        for band in bands:
            for r in [1, 2]:
                fig2.add_vrect(x0=band["x0"], x1=band["x1"],
                               fillcolor="rgba(100,116,139,0.10)", line_width=0, row=r, col=1)

        fig2.update_layout(**LAYOUT, height=520, showlegend=True)
        fig2.update_annotations(font=dict(family="DM Mono", size=11, color="#64748b"))
        for r in [1, 2]:
            fig2.update_xaxes(gridcolor="#1f2d40", row=r, col=1)
            fig2.update_yaxes(gridcolor="#1f2d40", row=r, col=1)
        st.plotly_chart(fig2, use_container_width=True)

    # ── Tab 3: Real yields ────────────────────────────────────────────────────
    with tabs[2]:
        ry = safe("DFII10")
        be = safe("T10YIE")
        mi = safe("MICH")

        fig3 = make_subplots(rows=2, cols=1, shared_xaxes=False, vertical_spacing=0.10,
                             subplot_titles=["10Y Real Yield vs Breakeven Inflation", "Umich 1Y Inflation Expectations"])

        if not ry.empty:
            fig3.add_trace(go.Scatter(x=ry.index, y=ry.values, line=dict(color="#00e5a0", width=2),
                                       fill="tozeroy", fillcolor="rgba(0,229,160,0.05)", name="Real Yield (TIPS)"), row=1, col=1)
        if not be.empty:
            fig3.add_trace(go.Scatter(x=be.index, y=be.values, line=dict(color="#f5c842", width=2),
                                       name="10Y Breakeven"), row=1, col=1)
        fig3.add_hline(y=0, line=dict(color="#ff4757", width=1, dash="dash"), row=1, col=1)
        fig3.add_hline(y=2, line=dict(color="#64748b", width=1, dash="dot"), row=1, col=1)

        if not mi.empty:
            fig3.add_trace(go.Scatter(x=mi.index, y=mi.values, line=dict(color="#ff6b35", width=2),
                                       fill="tozeroy", fillcolor="rgba(255,107,53,0.05)", name="UMich 1Y Exp."), row=2, col=1)
        fig3.add_hline(y=2, line=dict(color="#64748b", width=1, dash="dot"), row=2, col=1)

        for band in bands:
            for r in [1, 2]:
                fig3.add_vrect(x0=band["x0"], x1=band["x1"],
                               fillcolor="rgba(100,116,139,0.10)", line_width=0, row=r, col=1)

        fig3.update_layout(**LAYOUT, height=520)
        fig3.update_annotations(font=dict(family="DM Mono", size=11, color="#64748b"))
        for r in [1, 2]:
            fig3.update_xaxes(gridcolor="#1f2d40", row=r, col=1)
            fig3.update_yaxes(gridcolor="#1f2d40", row=r, col=1)
        st.plotly_chart(fig3, use_container_width=True)

    # ── Tab 4: Fed target tracker ─────────────────────────────────────────────
    with tabs[3]:
        st.markdown('<div class="info-box">How far are we from the Fed\'s 2% PCE target? This chart tracks the gap over time and shows "months above target."</div>', unsafe_allow_html=True)

        pcec_yoy = safe("PCEPILFE").pct_change(12) * 100
        gap_to_target = pcec_yoy - 2.0

        fig4 = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.08,
                             subplot_titles=["Core PCE YoY vs 2% Target", "Distance from Target (bps above/below)"])

        fig4.add_trace(go.Scatter(x=pcec_yoy.index, y=pcec_yoy.values,
                                   line=dict(color="#00d4ff", width=2), fill="tozeroy",
                                   fillcolor="rgba(0,212,255,0.05)", name="Core PCE YoY"), row=1, col=1)
        fig4.add_hline(y=2, line=dict(color="#f5c842", width=2, dash="dash"),
                       annotation_text="Fed Target 2%",
                       annotation_font=dict(family="DM Mono", size=10, color="#f5c842"), row=1, col=1)

        colors_gap = ["#ff4757" if v > 0 else "#00e5a0" for v in gap_to_target.values]
        fig4.add_trace(go.Bar(x=gap_to_target.index, y=gap_to_target.values,
                              marker_color=colors_gap, opacity=0.8, name="Gap to Target"), row=2, col=1)
        fig4.add_hline(y=0, line=dict(color="#f5c842", width=1), row=2, col=1)

        for band in bands:
            for r in [1, 2]:
                fig4.add_vrect(x0=band["x0"], x1=band["x1"],
                               fillcolor="rgba(100,116,139,0.10)", line_width=0, row=r, col=1)

        fig4.update_layout(**LAYOUT, height=520, showlegend=False)
        fig4.update_annotations(font=dict(family="DM Mono", size=11, color="#64748b"))
        for r in [1, 2]:
            fig4.update_xaxes(gridcolor="#1f2d40", row=r, col=1)
            fig4.update_yaxes(gridcolor="#1f2d40", row=r, col=1)
        st.plotly_chart(fig4, use_container_width=True)

        # Stats
        months_above = int((gap_to_target.dropna() > 0).sum())
        current_gap  = round(D.latest(gap_to_target), 2)
        st.markdown(f"""
        <div style="display:flex; gap:20px; flex-wrap:wrap; margin-top:10px;">
            <div class="metric-card" style="flex:1; min-width:150px;">
                <div class="metric-label">Months Above 2% Target</div>
                <div class="metric-value">{months_above}</div>
            </div>
            <div class="metric-card" style="flex:1; min-width:150px;">
                <div class="metric-label">Current Gap to Target</div>
                <div class="metric-value" style="color:{'#ff4757' if current_gap > 0 else '#00e5a0'}">
                    {'+' if current_gap > 0 else ''}{current_gap:.2f}%
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
