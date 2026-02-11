import streamlit as st
import pandas as pd
import numpy as np
import re
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta


# ==========================================
# 1. CONFIGURATION & DATA LOADING
# ==========================================
st.set_page_config(page_title="Tech & Eng Talent Radar", layout="wide")


@st.cache_data
def load_data():
    """
    Loads processed data. Falls back to mock data if file not found.
    To use real data: run data_processor.py first to generate tech_talent_radar_processed.csv
    """
    try:
        df = pd.read_csv("tech_talent_radar_processed.csv")
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
        return df, False  # False = not mock
    except FileNotFoundError:
        return generate_mock_data(), True  # True = mock data


def generate_mock_data():
    """
    Simulates the dataset for demo/development.
    """
    dates = [datetime.today() - timedelta(days=x) for x in range(365)]

    seniority = ['Junior', 'Senior', 'Lead', 'Principal', 'Intern', 'Head of']

    it_skills = ['Python', 'Java', 'React', 'AWS', 'Node.js', 'Data', 'Cybersecurity', 'DevOps', 'C++', '.NET']
    it_roles = ['Developer', 'Engineer', 'Architect', 'Analyst', 'Scientist']

    eng_skills = ['Civil', 'Mechanical', 'Electrical', 'Structural', 'Chemical', 'Process', 'Project']
    eng_roles = ['Engineer', 'Manager', 'Technician', 'Consultant']

    companies = ['DBS Bank', 'Shopee', 'ByteDance', 'Grab', 'Micron', 'Keppel', 'Sembcorp', 'GovTech', 'Stripe', 'Google']

    data = []

    # Generate 2000 random IT rows
    for _ in range(2000):
        s = np.random.choice(seniority)
        k = np.random.choice(it_skills)
        r = np.random.choice(it_roles)
        title = f"{s} {k} {r}"

        base_pay = 4000
        if s in ['Senior', 'Lead', 'Principal', 'Head of']: base_pay += 4000
        if k in ['Python', 'AWS', 'Data']: base_pay += 1500

        data.append({
            'job_title': title,
            'company': np.random.choice(companies),
            'category': 'Information Technology',
            'salary_avg': base_pay + np.random.randint(-500, 1500),
            'Skills': None,  # Will be tagged below
            'date': np.random.choice(dates)
        })

    # Generate 2000 random Engineering rows
    for _ in range(2000):
        s = np.random.choice(seniority)
        k = np.random.choice(eng_skills)
        r = np.random.choice(eng_roles)
        title = f"{s} {k} {r}"

        base_pay = 3500
        if s in ['Senior', 'Lead', 'Head of']: base_pay += 3500
        if k in ['Structural', 'Process']: base_pay += 1000

        data.append({
            'job_title': title,
            'company': np.random.choice(companies),
            'category': 'Engineering',
            'salary_avg': base_pay + np.random.randint(-500, 1500),
            'Skills': None,
            'date': np.random.choice(dates)
        })

    df = pd.DataFrame(data)

    # Tag skills using regex
    from data_processor import IT_KEYWORDS, ENG_KEYWORDS, get_skills
    df['Skills'] = df.apply(lambda row: get_skills(row, IT_KEYWORDS, ENG_KEYWORDS), axis=1)
    df = df.explode('Skills')

    return df


# Load the data
df, is_mock = load_data()


# ==========================================
# 2. DASHBOARD LAYOUT
# ==========================================

st.title("📡 Tech & Engineering Talent Radar")
st.markdown("""
**Group 6 Strategy:** By filtering for IT & Engineering (26% of market), we utilize specific job titles 
as high-fidelity proxies for skills, bypassing the lack of job descriptions.
""")

if is_mock:
    st.warning("⚠️ Running with **mock data**. Run `python data_processor.py` first to load real data.")


# --- Sidebar Filters ---
st.sidebar.header("Filter Strategy")
selected_category = st.sidebar.radio("Select Sector:", ["Information Technology", "Engineering"])
available_companies = sorted(df['company'].dropna().unique())
selected_companies = st.sidebar.multiselect(
    "Benchmark Companies:", 
    available_companies, 
    default=available_companies[:5]
)


# Filter Data
filtered_df = df[
    (df['category'] == selected_category) & 
    (df['company'].isin(selected_companies))
]


# --- KPI Row ---
c1, c2, c3 = st.columns(3)
c1.metric("Total Active Roles", f"{len(filtered_df):,}")
c2.metric("Avg Market Salary", f"${int(filtered_df['salary_avg'].mean()):,}" if len(filtered_df) > 0 else "$0")

if len(filtered_df) > 0 and 'Skills' in filtered_df.columns:
    top_skill = filtered_df['Skills'].mode()
    c3.metric("Most In-Demand Skill", top_skill.iloc[0] if len(top_skill) > 0 else "N/A")
else:
    c3.metric("Most In-Demand Skill", "N/A")


st.divider()


# --- TAB VIEW ---
tab1, tab2, tab3 = st.tabs(["📈 Market Demand (Volume)", "💰 Salary Arbitrage (Value)", "🏢 Corporate Strategy (Competitors)"])


# View 1: Demand Trends
with tab1:
    st.subheader(f"The 'Language War' in {selected_category}")

    if 'date' in filtered_df.columns and len(filtered_df) > 0:
        trend_data = filtered_df.groupby(
            [pd.Grouper(key='date', freq='ME'), 'Skills']
        ).size().reset_index(name='Count')

        fig_trend = px.line(trend_data, x='date', y='Count', color='Skills', 
                            title="Skill Demand Over Time", markers=True)
        st.plotly_chart(fig_trend, use_container_width=True)
    else:
        st.info("No date data available for trend analysis.")

    st.info("💡 **Insight:** Rising lines indicate a tech stack gaining market share. Falling lines suggest legacy tech.")


# View 2: Salary Analysis
with tab2:
    st.subheader("Which Skills Command a Premium?")

    if len(filtered_df) > 0:
        # Calculate median salary per skill to sort the boxplot
        order = filtered_df.groupby('Skills')['salary_avg'].median().sort_values(ascending=False).index

        fig_box = px.box(filtered_df, x='Skills', y='salary_avg', color='Skills',
                         category_orders={'Skills': list(order)},
                         title="Salary Distribution by Skill Set")
        st.plotly_chart(fig_box, use_container_width=True)
    else:
        st.info("No data available for salary analysis.")

    st.info("💡 **Insight:** The 'spread' (height of the box) shows volatility. A high median with a tight box means consistently high pay.")


# View 3: Competitor Strategy
with tab3:
    st.subheader("What are your competitors building?")

    if len(filtered_df) > 0:
        strategy_data = filtered_df.groupby(['company', 'Skills']).size().reset_index(name='Job Count')

        fig_bar = px.bar(strategy_data, x='company', y='Job Count', color='Skills', 
                         title="Hiring Strategy by Company (Stacked)", barmode='stack')
        st.plotly_chart(fig_bar, use_container_width=True)

        st.write("### Skill Share Table")
        pivot = filtered_df.groupby(['company', 'Skills']).size().unstack().fillna(0)
        st.dataframe(pivot.style.background_gradient(cmap="Blues"))
    else:
        st.info("No data available for competitor analysis.")


# ==========================================
# 3. FOOTER & EXPORT
# ==========================================
st.divider()
st.caption("Project Group 6 | Data Source: SG Job Postings | Methodology: Regex Title Extraction")
