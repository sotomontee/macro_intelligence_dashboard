# 📊 Macro Intelligence Dashboard
---
### 🏠 Overview
- Real-time key metric cards with signal badges (Inverted / Elevated / Normal)
- 2×2 overview chart: Yield spread, CPI vs PCE, Real Yields, Sahm Rule
- NBER recession shading across all historical charts

### 📈 Yield Curve Lab
- Live US Treasury yield curve with 1W / 1M / 1Y comparisons
- **Historical time-travel slider** — see the curve on any date since 1990
- Spread history: 10Y–2Y and 10Y–3M with inversion detection
- Inversion alerts with duration tracking and all-time inversion period table

### 🔥 Inflation Monitor
- CPI vs Core CPI vs PCE vs Core PCE — all on one chart
- Headline vs Core decomposition (food & energy contribution)
- Real yields (TIPS) + 10Y breakeven inflation + Umich expectations
- Fed 2% target tracker with distance chart and months-above counter

### 🚨 Recession Radar
- **Composite Recession Risk Score (0–100)** — original weighted model
- Gauge chart with live score, labelled Low / Elevated / High Risk
- Historical score chart with individual component breakdown
- Sahm Rule signal + labor market charts
- Full methodology explanation

---

## 🚀 Getting Started

### 1. Clone the repo
```bash
git clone https://github.com/yourusername/macro-dashboard.git
cd macro-dashboard
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Get a free FRED API key
Visit [fred.stlouisfed.org](https://fred.stlouisfed.org/docs/api/api_key.html) and register — it's free and instant.

### 4. Run
```bash
streamlit run app.py
```

Paste your FRED API key in the sidebar when prompted.

---

## 📦 Project Structure

```
macro-dashboard/
├── app.py                  # Entry point, layout, sidebar, routing
├── requirements.txt
├── pages_src/
│   ├── __init__.py
│   ├── data.py             # FRED API fetching + utility functions
│   ├── overview.py         # Overview page
│   ├── yield_curve.py      # Yield Curve Lab
│   ├── inflation.py        # Inflation Monitor
│   └── recession.py        # Recession Radar + composite score
└── README.md
```

---

## 🌐 Deploy to Streamlit Cloud (Free)

1. Push to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your repo and set `app.py` as the entry point

> **Tip:** Add `FRED_API_KEY` as a [Streamlit Secret](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management) to avoid entering it manually each session.

---

## 📊 Data Sources

All data sourced from the **Federal Reserve Bank of St. Louis (FRED)** via their public API:

| Series | Description |
|--------|-------------|
| DGS1MO – DGS30 | US Treasury yields by maturity |
| T10Y2Y, T10Y3M | Yield curve spreads |
| CPIAUCSL, CPILFESL | CPI headline & core |
| PCEPI, PCEPILFE | PCE headline & core |
| T10YIE | 10Y breakeven inflation |
| DFII10 | 10Y TIPS real yield |
| MICH | UMich inflation expectations |
| SAHMREALTIME | Sahm Rule real-time indicator |
| UNRATE | Unemployment rate |
| PAYEMS | Nonfarm payrolls |
| USREC | NBER recession indicator |

---

## ⚠️ Disclaimer

This dashboard is for **educational and research purposes only**. The Composite Recession Risk Score is a custom model and does not constitute financial advice or a trading signal.
