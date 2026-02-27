"""
FRED API data fetching with Streamlit caching.
All series IDs documented at https://fred.stlouisfed.org
"""
import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta

FRED_BASE = "https://api.stlouisfed.org/fred/series/observations"

# ── Core series map ──────────────────────────────────────────────────────────
SERIES = {
    # Yield curve
    "DGS1MO":  "1-Month Treasury",
    "DGS3MO":  "3-Month Treasury",
    "DGS6MO":  "6-Month Treasury",
    "DGS1":    "1-Year Treasury",
    "DGS2":    "2-Year Treasury",
    "DGS5":    "5-Year Treasury",
    "DGS7":    "7-Year Treasury",
    "DGS10":   "10-Year Treasury",
    "DGS20":   "20-Year Treasury",
    "DGS30":   "30-Year Treasury",
    # Spreads
    "T10Y2Y":  "10Y-2Y Spread",
    "T10Y3M":  "10Y-3M Spread",
    # Inflation
    "CPIAUCSL": "CPI (All Urban)",
    "CPILFESL": "Core CPI (ex Food & Energy)",
    "PCEPI":    "PCE Price Index",
    "PCEPILFE": "Core PCE",
    "MICH":     "Umich Inflation Expectations (1Y)",
    "T10YIE":   "10Y Breakeven Inflation",
    "DFII10":   "10Y Real Yield (TIPS)",
    # Labor / recession
    "UNRATE":   "Unemployment Rate",
    "SAHMREALTIME": "Sahm Rule Indicator",
    "USREC":    "NBER Recession Indicator",
    "INDPRO":   "Industrial Production",
    "PAYEMS":   "Nonfarm Payrolls",
}


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_series(series_id: str, api_key: str, start: str = "2000-01-01") -> pd.Series:
    """Fetch a single FRED series, return as pd.Series indexed by date."""
    params = {
        "series_id": series_id,
        "api_key": api_key,
        "file_type": "json",
        "observation_start": start,
        "observation_end": datetime.today().strftime("%Y-%m-%d"),
    }
    r = requests.get(FRED_BASE, params=params, timeout=15)
    r.raise_for_status()
    obs = r.json().get("observations", [])
    df = pd.DataFrame(obs)[["date", "value"]]
    df["date"] = pd.to_datetime(df["date"])
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.dropna().set_index("date")["value"]
    return df


def fetch_many(series_ids: list, api_key: str, start: str = "2000-01-01") -> pd.DataFrame:
    """Fetch multiple series into a single DataFrame."""
    frames = {}
    for sid in series_ids:
        try:
            frames[sid] = fetch_series(sid, api_key, start)
        except Exception:
            pass
    if not frames:
        return pd.DataFrame()
    return pd.DataFrame(frames)


def latest(series: pd.Series) -> float:
    """Return most recent non-null value."""
    return round(series.dropna().iloc[-1], 2) if not series.dropna().empty else float("nan")


def prev(series: pd.Series, periods: int = 1) -> float:
    s = series.dropna()
    return round(s.iloc[-1 - periods], 2) if len(s) > periods else float("nan")


def yoy_change(series: pd.Series) -> float:
    """Year-over-year % change of last value."""
    s = series.dropna()
    if len(s) < 13:
        return float("nan")
    return round((s.iloc[-1] / s.iloc[-13] - 1) * 100, 2)


def mom_change(series: pd.Series) -> float:
    s = series.dropna()
    if len(s) < 2:
        return float("nan")
    return round((s.iloc[-1] / s.iloc[-2] - 1) * 100, 2)


def recession_bands(recessions: pd.Series) -> list[dict]:
    """Convert NBER 0/1 series into a list of shading rect dicts for Plotly."""
    if recessions is None or recessions.empty:
        return []
    bands = []
    in_rec = False
    start_date = None
    for date, val in recessions.items():
        if val == 1 and not in_rec:
            in_rec = True
            start_date = date
        elif val == 0 and in_rec:
            in_rec = False
            bands.append({"x0": start_date, "x1": date})
    if in_rec:
        bands.append({"x0": start_date, "x1": recessions.index[-1]})
    return bands


def add_recession_shapes(fig, bands: list[dict], row=None, col=None):
    """Add grey recession shading rectangles to a Plotly figure."""
    for b in bands:
        shape = dict(
            type="rect",
            x0=b["x0"], x1=b["x1"],
            y0=0, y1=1,
            xref="x", yref="paper",
            fillcolor="rgba(100,116,139,0.12)",
            line_width=0,
            layer="below",
        )
        if row is not None:
            shape["row"] = row
            shape["col"] = col
        fig.add_shape(**shape)
    return fig
