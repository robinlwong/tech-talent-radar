# 📡 Tech & Engineering Talent Radar

**Group 6** — Singapore Job Market Intelligence for IT & Engineering sectors.

## Strategy

While other groups analyze the generic job market, we provide **deep competitive intelligence** on Singapore's most critical sectors: Tech and Engineering. We don't just tell you who is hiring — we tell you **what specific technologies** (Python vs. Java, Tunnelling vs. Structural) are driving the economy.

### Key Insight
In IT and Engineering, the **skill is in the title**: "Full Stack Python Developer" tells you everything. No job description needed.

## Dashboard Views

1. **📈 Market Demand** — Track skill demand over time ("Language Wars")
2. **💰 Salary Arbitrage** — Which skills command premium pay?
3. **🏢 Corporate Strategy** — What are competitors building?

## Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Process real data (optional)
```bash
# Place your CSV in this folder, then:
python data_processor.py
```

### 3. Run the dashboard
```bash
streamlit run app.py
```

The app runs with **mock data** by default. Process your real CSV to see actual insights.

## Files

| File | Purpose |
|------|---------|
| `app.py` | Streamlit dashboard |
| `data_processor.py` | Raw CSV → processed CSV pipeline |
| `requirements.txt` | Python dependencies |

## Methodology

**Regex Title Extraction** — Maps job titles to 25+ skill categories using pattern matching:
- IT: Python, Java, React/JS, AWS, Data/AI, Cybersecurity, DevOps, etc.
- Engineering: Civil/Structural, Mechanical, Electrical, Chemical/Process, etc.

## Tech Stack
Python · Streamlit · Pandas · Plotly · Regex
