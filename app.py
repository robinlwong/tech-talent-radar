import streamlit as st
import pandas as pd
import numpy as np
import re
import json
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# ==========================================
# 1. CONFIGURATION & DATA LOADING
# ==========================================
st.set_page_config(page_title="Tech & Eng Talent Radar", layout="wide")

# Skill Dictionaries
it_keywords = {
    'Python': r'\bpython\b',
    'Java': r'\bjava\b',
    'React/JS': r'\b(react|node|javascript|typescript|vue|angular)\b',
    'Cloud/AWS': r'\b(aws|azure|cloud|gcp|google cloud)\b',
    'Data/AI': r'\b(data|ai|machine learning|nlp|torch|tensorflow|bi|tableau)\b',
    'Cybersecurity': r'\b(cyber|security|infosec)\b',
    'DevOps': r'\b(devops|sre|ci/cd|kubernetes|docker|jenkins)\b',
    '.NET/C#': r'\b(\.net|c#|dotnet)\b',
    'SQL': r'\bsql\b',
}

eng_keywords = {
    'Civil/Structural': r'\b(civil|structural|tunnel|bridge|geotechnical)\b',
    'Mechanical': r'\b(mechanical|hvac|piping|m&e)\b',
    'Electrical': r'\b(electrical|power|high voltage|switchgear)\b',
    'Electronics': r'\b(electronics|pcb|embedded|firmware|semiconductor|wafer)\b',
    'Chemical/Process': r'\b(chemical|process eng|refinery|oil and gas)\b',
    'Marine/Offshore': r'\b(marine|offshore|naval|ship)\b',
}


def parse_categories(val):
    """Parse JSON categories string."""
    try:
        if isinstance(val, list):
            return [x.get('category', '') for x in val]
        if isinstance(val, str) and val.startswith('['):
            data = json.loads(val.replace("'", '"'))
            return [item.get('category', '') for item in data]
        return []
    except Exception:
        return []


def extract_skills(row):
    """Scans title against dictionaries based on Category."""
    title = str(row['job_title']).lower()
    found = []
    target_dict = it_keywords if row['category'] == 'Information Technology' else eng_keywords
    for skill, pattern in target_dict.items():
        if re.search(pattern, title):
            found.append(skill)
    return found if found else ['General/Management']


@st.cache_data
def load_data():
    """
    Try loading processed data first, then raw data, then mock data.
    """
    # Option 1: Pre-processed CSV
    try:
        df = pd.read_csv("tech_talent_radar_processed.csv")
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
        return df, "processed"
    except FileNotFoundError:
        pass

    # Option 2: Raw CSV with correct column names
    for filename in ["tech_talent_radar.csv", "SGJobData.csv"]:
        try:
            df_raw = pd.read_csv(filename, low_memory=False)

            # Check if this is the raw format (has 'title' and 'categories' columns)
            if 'title' in df_raw.columns and 'categories' in df_raw.columns:
                # Filter for IT & Engineering
                target_sectors = {'Information Technology', 'Engineering'}
                mask = df_raw['categories'].apply(
                    lambda x: any(c in target_sectors for c in parse_categories(x))
                    if isinstance(x, str) else False
                )
                df_filtered = df_raw[mask].copy()

                # Rename columns
                rename_map = {
                    'title': 'job_title',
                    'postedCompany_name': 'company',
                    'metadata_newPostingDate': 'date',
                    'average_salary': 'salary_avg',
                    'salary_minimum': 'salary_min',
                    'salary_maximum': 'salary_max',
                }
                df_filtered.rename(columns={k: v for k, v in rename_map.items()
                                            if k in df_filtered.columns}, inplace=True)

                # Add primary category
                df_filtered['category'] = df_filtered['categories'].apply(
                    lambda val: 'Information Technology'
                    if 'Information Technology' in parse_categories(val)
                    else 'Engineering'
                )

                # Clean salaries
                for col in ['salary_min', 'salary_max', 'salary_avg']:
                    if col in df_filtered.columns:
                        df_filtered[col] = pd.to_numeric(df_filtered[col], errors='coerce')

                if 'salary_avg' in df_filtered.columns:
                    missing = df_filtered['salary_avg'].isna()
                    if 'salary_min' in df_filtered.columns and 'salary_max' in df_filtered.columns:
                        df_filtered.loc[missing, 'salary_avg'] = (
                            df_filtered.loc[missing, 'salary_min'] +
                            df_filtered.loc[missing, 'salary_max']
                        ) / 2

                # Parse date
                if 'date' in df_filtered.columns:
                    df_filtered['date'] = pd.to_datetime(df_filtered['date'], errors='coerce')

                # Tag skills & explode
                df_filtered['Skills'] = df_filtered.apply(extract_skills, axis=1)
                df_exploded = df_filtered.explode('Skills')

                return df_exploded, "raw"
        except FileNotFoundError:
            continue

    # Option 3: Mock data
    return generate_mock_data(), "mock"


def generate_mock_data():
    """Generate mock data for demo."""
    dates = [datetime.today() - timedelta(days=x) for x in range(365)]
    seniority = ['Junior', 'Senior', 'Lead', 'Principal', 'Intern', 'Head of']
    it_skills_list = ['Python', 'Java', 'React', 'AWS', 'Node.js', 'Data', 'Cybersecurity', 'DevOps', 'C++', '.NET']
    it_roles = ['Developer', 'Engineer', 'Architect', 'Analyst', 'Scientist']
    eng_skills_list = ['Civil', 'Mechanical', 'Electrical', 'Structural', 'Chemical', 'Process', 'Project']
    eng_roles = ['Engineer', 'Manager', 'Technician', 'Consultant']
    companies = ['DBS Bank', 'Shopee', 'ByteDance', 'Grab', 'Micron', 'Keppel', 'Sembcorp', 'GovTech', 'Stripe', 'Google']

    data = []
    for _ in range(2000):
        s = np.random.choice(seniority)
        k = np.random.choice(it_skills_list)
        r = np.random.choice(it_roles)
        base_pay = 4000
        if s in ['Senior', 'Lead', 'Principal', 'Head of']: base_pay += 4000
        if k in ['Python', 'AWS', 'Data']: base_pay += 1500
        data.append({
            'job_title': f"{s} {k} {r}",
            'company': np.random.choice(companies),
            'category': 'Information Technology',
            'salary_avg': base_pay + np.random.randint(-500, 1500),
            'date': np.random.choice(dates)
        })
    for _ in range(2000):
        s = np.random.choice(seniority)
        k = np.random.choice(eng_skills_list)
        r = np.random.choice(eng_roles)
        base_pay = 3500
        if s in ['Senior', 'Lead', 'Head of']: base_pay += 3500
        if k in ['Structural', 'Process']: base_pay += 1000
        data.append({
            'job_title': f"{s} {k} {r}",
            'company': np.random.choice(companies),
            'category': 'Engineering',
            'salary_avg': base_pay + np.random.randint(-500, 1500),
            'date': np.random.choice(dates)
        })

    df = pd.DataFrame(data)
    df['Skills'] = df.apply(extract_skills, axis=1)
    df = df.explode('Skills')
    return df


# Load data
df, data_source = load_data()

# ==========================================
# 2. DASHBOARD LAYOUT
# ==========================================

st.title("📡 Tech & Engineering Talent Radar")
st.markdown("""
**Group 6 Strategy:** By filtering for IT & Engineering (26% of market), we utilize specific job titles 
as high-fidelity proxies for skills, bypassing the lack of job descriptions.
""")

if data_source == "mock":
    st.warning("⚠️ Running with **mock data**. Place your CSV file in this folder and restart.")
elif data_source == "raw":
    st.success("✅ Loaded **real data** directly from raw CSV.")
else:
    st.success("✅ Loaded **pre-processed data**.")

# --- Sidebar Filters ---
st.sidebar.header("Filter Strategy")
selected_category = st.sidebar.radio("Select Sector:", ["Information Technology", "Engineering"])

available_companies = sorted(df['company'].dropna().unique())
selected_companies = st.sidebar.multiselect(
    "Benchmark Companies:",
    available_companies,
    default=available_companies[:5] if len(available_companies) >= 5 else available_companies
)

# Filter Data
filtered_df = df[
    (df['category'] == selected_category) &
    (df['company'].isin(selected_companies))
]

# --- KPI Row ---
c1, c2, c3 = st.columns(3)
c1.metric("Total Active Roles", f"{len(filtered_df):,}")

if len(filtered_df) > 0 and 'salary_avg' in filtered_df.columns:
    avg_sal = filtered_df['salary_avg'].mean()
    c2.metric("Avg Market Salary", f"${int(avg_sal):,}" if not pd.isna(avg_sal) else "N/A")
else:
    c2.metric("Avg Market Salary", "N/A")

if len(filtered_df) > 0:
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
        df_with_dates = filtered_df.dropna(subset=['date'])
        if len(df_with_dates) > 0:
            trend_data = df_with_dates.groupby(
                [pd.Grouper(key='date', freq='ME'), 'Skills']
            ).size().reset_index(name='Count')

            fig_trend = px.line(trend_data, x='date', y='Count', color='Skills',
                                title="Skill Demand Over Time", markers=True)
            st.plotly_chart(fig_trend, use_container_width=True)
        else:
            st.info("No date data available for trend analysis.")
    else:
        st.info("No date data available for trend analysis.")

    st.info("💡 **Insight:** Rising lines indicate a tech stack gaining market share. Falling lines suggest legacy tech.")

# View 2: Salary Analysis
with tab2:
    st.subheader("Which Skills Command a Premium?")

    df_salary = filtered_df.dropna(subset=['salary_avg']) if 'salary_avg' in filtered_df.columns else pd.DataFrame()

    if len(df_salary) > 0:
        order = df_salary.groupby('Skills')['salary_avg'].median().sort_values(ascending=False).index

        fig_box = px.box(df_salary, x='Skills', y='salary_avg', color='Skills',
                         category_orders={'Skills': list(order)},
                         title="Salary Distribution by Skill Set")
        st.plotly_chart(fig_box, use_container_width=True)
    else:
        st.info("No salary data available.")

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
col_footer1, col_footer2 = st.columns(2)
with col_footer1:
    st.caption(f"Project Group 6 | Data Source: {'SG Job Postings' if data_source != 'mock' else 'Simulated'} | Methodology: Regex Title Extraction")
with col_footer2:
    st.caption(f"Data mode: **{data_source}** | Rows loaded: {len(df):,}")
