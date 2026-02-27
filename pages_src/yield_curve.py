import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from . import data as D

MATURITIES = {
    "DGS1MO": 1/12, "DGS3MO": 3/12, "DGS6MO": 6/12,
    "DGS1": 1, "DGS2": 2, "DGS5": 5,
    "DGS7": 7, "DGS10": 10, "DGS20": 20, "DGS30": 30,
}
LABELS = ["1M", "3M", "6M", "1Y", "2Y", "5Y", "7Y", "10Y", "20Y", "30Y"]

LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="DM Sans", color="#e2e8f0"),
    margin=dict(l=10, r=10, t=30, b=10),
    legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor="#1f2d40"),
)


def render(api_key: str):
    st.markdown('<div class="page-title">Yield Curve Lab</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">US Treasury Yield Curve · Shape Analysis · Inversion Tracker</div>', unsafe_allow_html=True)
    st.markdown("<hr class='divider'>", unsafe_allow_html=True)

    if not api_key:
        st.markdown("<div class='info-box'>Enter your FRED API key in the sidebar to load yield curve data.</div>", unsafe_allow_html=True)
        return

    with st.spinner("Loading yield curve data..."):
        try:
            df = D.fetch_many(list(MATURITIES.keys()), api_key, start="1990-01-01")
            spreads_df = D.fetch_many(["T10Y2Y", "T10Y3M", "USREC"], api_key, start="1990-01-01")
        except Exception as e:
            st.error(f"Error: {e}"); return

    tabs = st.tabs(["📐  Current Curve", "🎬  Historical Snapshot", "📉  Spread History", "⚠️  Inversion Alerts"])

    # ── Tab 1: Current curve ─────────────────────────────────────────────────
    with tabs[0]:
        col1, col2 = st.columns([2, 1])

        today_row = df.dropna(how="all").iloc[-1]
        week_row  = df.dropna(how="all").iloc[-6] if len(df) > 6 else today_row
        month_row = df.dropna(how="all").iloc[-22] if len(df) > 22 else today_row
        year_row  = df.dropna(how="all").iloc[-252] if len(df) > 252 else today_row

        today_vals = [today_row.get(k, np.nan) for k in MATURITIES]
        week_vals  = [week_row.get(k, np.nan) for k in MATURITIES]
        month_vals = [month_row.get(k, np.nan) for k in MATURITIES]
        year_vals  = [year_row.get(k, np.nan) for k in MATURITIES]

        with col1:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=LABELS, y=year_vals,  line=dict(color="#1f2d40", width=1.5, dash="dot"),  name="1Y Ago"))
            fig.add_trace(go.Scatter(x=LABELS, y=month_vals, line=dict(color="#2d4a6b", width=1.5, dash="dash"), name="1M Ago"))
            fig.add_trace(go.Scatter(x=LABELS, y=week_vals,  line=dict(color="#4a7fa0", width=1.5),              name="1W Ago"))
            fig.add_trace(go.Scatter(x=LABELS, y=today_vals,
                                     line=dict(color="#00d4ff", width=3),
                                     marker=dict(size=8, color="#00d4ff"),
                                     fill="tozeroy", fillcolor="rgba(0,212,255,0.06)",
                                     name="Today"))
            fig.update_layout(**LAYOUT, height=380, title="US Treasury Yield Curve",
                              xaxis=dict(gridcolor="#1f2d40"), yaxis=dict(gridcolor="#1f2d40", title="Yield (%)"))
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.markdown('<div class="section-header" style="font-size:16px;">Today\'s Rates</div>', unsafe_allow_html=True)
            for label, sid in zip(LABELS, MATURITIES.keys()):
                v = today_row.get(sid, np.nan)
                ch = v - year_row.get(sid, np.nan) if not np.isnan(v) else np.nan
                if not np.isnan(v):
                    color = "#00d4ff" if not np.isnan(v) else "#64748b"
                    delta_color = "#ff4757" if ch > 0 else "#00e5a0" if ch < 0 else "#64748b"
                    delta_str = f'<span style="color:{delta_color}; font-size:11px;">{"▲" if ch>0 else "▼"} {abs(ch):.2f}% YoY</span>' if not np.isnan(ch) else ""
                    st.markdown(f"""
                    <div style="display:flex; justify-content:space-between; align-items:center;
                                padding: 8px 0; border-bottom: 1px solid #1f2d40;">
                        <span style="font-family:DM Mono,monospace; font-size:12px; color:#64748b;">{label}</span>
                        <div style="text-align:right;">
                            <span style="color:{color}; font-weight:600;">{v:.2f}%</span><br>
                            {delta_str}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

    # ── Tab 2: Historical snapshot ───────────────────────────────────────────
    with tabs[1]:
        st.markdown('<div class="info-box">Compare yield curves across different dates. Use the slider to travel back in time.</div>', unsafe_allow_html=True)

        df_clean = df.dropna(how="any", subset=list(MATURITIES.keys()))
        min_date = df_clean.index.min().date()
        max_date = df_clean.index.max().date()

        selected_date = st.slider("Select Date", min_value=min_date, max_value=max_date,
                                   value=max_date, format="YYYY-MM-DD")

        # Find closest date
        idx = df_clean.index.searchsorted(pd.Timestamp(selected_date))
        idx = min(idx, len(df_clean) - 1)
        sel_row = df_clean.iloc[idx]
        sel_vals = [sel_row.get(k, np.nan) for k in MATURITIES]
        today_row_clean = df_clean.iloc[-1]
        today_clean_vals = [today_row_clean.get(k, np.nan) for k in MATURITIES]

        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=LABELS, y=today_clean_vals, line=dict(color="#00d4ff", width=2, dash="dash"),
                                  name="Today", opacity=0.5))
        fig2.add_trace(go.Scatter(x=LABELS, y=sel_vals,
                                  line=dict(color="#f5c842", width=3),
                                  marker=dict(size=9, color="#f5c842"),
                                  fill="tozeroy", fillcolor="rgba(245,200,66,0.06)",
                                  name=str(df_clean.index[idx].date())))

        # Color fill based on inversion
        is_inverted = sel_vals[1] > sel_vals[-1] if not np.isnan(sel_vals[1]) and not np.isnan(sel_vals[-1]) else False
        shape_label = "⚡ INVERTED" if is_inverted else "✓ NORMAL"
        shape_color = "#ff4757" if is_inverted else "#00e5a0"
        fig2.add_annotation(x=0.98, y=0.95, xref="paper", yref="paper",
                            text=f'<span style="color:{shape_color}">{shape_label}</span>',
                            showarrow=False, font=dict(family="DM Mono", size=13))

        fig2.update_layout(**LAYOUT, height=420,
                           title=f"Yield Curve on {df_clean.index[idx].strftime('%d %b %Y')}",
                           xaxis=dict(gridcolor="#1f2d40"), yaxis=dict(gridcolor="#1f2d40", title="Yield (%)"))
        st.plotly_chart(fig2, use_container_width=True)

    # ── Tab 3: Spread History ────────────────────────────────────────────────
    with tabs[2]:
        recessions = spreads_df["USREC"] if "USREC" in spreads_df.columns else pd.Series()
        bands = D.recession_bands(recessions)

        fig3 = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.06,
                             subplot_titles=["10Y – 2Y Spread (Classic)", "10Y – 3M Spread (Fed preferred)"])

        for sid, label, color, row in [("T10Y2Y", "10Y–2Y", "#00d4ff", 1),
                                        ("T10Y3M", "10Y–3M", "#ff6b35", 2)]:
            s = spreads_df[sid].dropna() if sid in spreads_df.columns else pd.Series()
            if not s.empty:
                fig3.add_trace(go.Scatter(x=s.index, y=s.values,
                                          line=dict(color=color, width=1.5),
                                          fill="tozeroy",
                                          fillcolor=f"rgba({int(color[1:3],16)},{int(color[3:5],16)},{int(color[5:7],16)},0.07)",
                                          name=label), row=row, col=1)
                fig3.add_hline(y=0, line=dict(color="#ff4757", width=1, dash="dash"), row=row, col=1)

        for band in bands:
            for r in [1, 2]:
                fig3.add_vrect(x0=band["x0"], x1=band["x1"],
                               fillcolor="rgba(100,116,139,0.10)", line_width=0, row=r, col=1)

        fig3.update_layout(**LAYOUT, height=520, showlegend=False)
        fig3.update_annotations(font=dict(family="DM Mono", size=11, color="#64748b"))
        for r in [1, 2]:
            fig3.update_xaxes(gridcolor="#1f2d40", row=r, col=1)
            fig3.update_yaxes(gridcolor="#1f2d40", row=r, col=1)

        st.plotly_chart(fig3, use_container_width=True)
        st.markdown('<div class="info-box">Grey bands = NBER recessions. Negative readings (below 0) = yield curve inverted. Sustained inversion historically precedes recessions by 12–18 months.</div>', unsafe_allow_html=True)

    # ── Tab 4: Inversion Alerts ──────────────────────────────────────────────
    with tabs[3]:
        s2 = spreads_df["T10Y2Y"].dropna() if "T10Y2Y" in spreads_df.columns else pd.Series()
        s3 = spreads_df["T10Y3M"].dropna() if "T10Y3M" in spreads_df.columns else pd.Series()

        c1, c2 = st.columns(2)

        def inversion_stats(series, label):
            current = D.latest(series)
            days_inverted = int((series < 0).sum())
            consec = 0
            for v in reversed(series.values):
                if v < 0: consec += 1
                else: break
            status = "INVERTED" if current < 0 else "NORMAL"
            css = "signal-risk" if current < 0 else "signal-safe"
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">{label}</div>
                <div class="metric-value">{current:+.2f} bps</div>
                <div style="margin-top:12px;">
                    <span class="signal-badge {css}">{status}</span>
                </div>
                <div style="margin-top:12px; font-family: DM Mono, monospace; font-size: 12px; color: #64748b;">
                    Days inverted (all-time): <b style="color:#e2e8f0">{days_inverted}</b><br>
                    Current streak: <b style="color:{"#ff4757" if consec > 0 else "#00e5a0"}">{consec} days</b>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with c1:
            if not s2.empty:
                inversion_stats(s2, "10Y – 2Y Spread")
        with c2:
            if not s3.empty:
                inversion_stats(s3, "10Y – 3M Spread")

        st.markdown("<hr class='divider'>", unsafe_allow_html=True)
        st.markdown('<div class="section-header" style="font-size:16px;">Historical Inversion Periods</div>', unsafe_allow_html=True)

        if not s2.empty:
            inv = s2 < 0
            inv_changes = inv.astype(int).diff().fillna(0)
            starts = s2.index[inv_changes == 1].tolist()
            ends   = s2.index[inv_changes == -1].tolist()

            if inv.iloc[-1]:
                ends.append(s2.index[-1])
            if len(ends) < len(starts):
                ends.append(s2.index[-1])

            periods = []
            for s, e in zip(starts, ends):
                dur = (e - s).days
                min_spread = round(s2[s:e].min(), 2)
                periods.append({"Start": s.strftime("%Y-%m-%d"), "End": e.strftime("%Y-%m-%d"),
                                 "Duration (days)": dur, "Min Spread (bps)": min_spread})

            if periods:
                pdf = pd.DataFrame(periods).sort_values("Start", ascending=False)
                st.dataframe(pdf, use_container_width=True, hide_index=True)
