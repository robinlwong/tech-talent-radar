import streamlit as st
import pandas as pd
import plotly.express as px

# PAGE CONFIG
st.set_page_config(page_title="Tech Talent Radar", layout="wide")

# LOAD DATA
@st.cache_data
def load_data():
    # Load the compressed file directly
    df = pd.read_csv("tech_talent_radar_final.zip")
    # Convert date
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
    return df

try:
    df = load_data()
except FileNotFoundError:
    st.error("❌ Data file not found. Please run 'data_processor_v3.py' first!")
    st.stop()

# TITLE & SIDEBAR
st.title("📡 Tech & Engineering Talent Radar")
st.markdown("### Competitive Intelligence for Singapore's Tech Sector")

with st.sidebar:
    st.header("Filters")
    # Category Filter
    cats = df['category'].unique()
    selected_cat = st.radio("Select Sector:", cats)

    # Filter Data by Category first
    df_cat = df[df['category'] == selected_cat]

    # Tech Stack Filter
    stacks = df_cat['Tech_Stack'].dropna().unique()
    selected_stacks = st.multiselect("Filter Tech Stacks:", stacks, default=stacks[:5])

# APPLY FILTERS
if selected_stacks:
    df_filtered = df_cat[df_cat['Tech_Stack'].isin(selected_stacks)]
else:
    df_filtered = df_cat

# KPIS
c1, c2, c3 = st.columns(3)
c1.metric("Active Job Postings", len(df_filtered))
avg_sal = df_filtered['salary_avg'].mean()
c2.metric("Avg Monthly Salary", f"${avg_sal:,.0f}" if not pd.isna(avg_sal) else "N/A")
top_skill = df_filtered['Tech_Stack'].mode()[0] if not df_filtered.empty else "N/A"
c3.metric("Top In-Demand Skill", top_skill)

st.divider()

# TABS
tab1, tab2, tab3 = st.tabs(["💰 Value (Salary)", "📈 Demand (Volume)", "🏢 Competition (Strategy)"])

with tab1:
    st.subheader("Which Tech Stack Pays the Most?")
    if not df_filtered.empty:
        # Sort by median salary
        order = df_filtered.groupby('Tech_Stack')['salary_avg'].median().sort_values(ascending=False).index
        fig = px.box(df_filtered, x='Tech_Stack', y='salary_avg', color='Tech_Stack',
                     category_orders={'Tech_Stack': order}, points=False)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Select Tech Stacks in the sidebar to see data.")

with tab2:
    st.subheader("Hiring Demand Over Time")
    if 'date' in df_filtered.columns and not df_filtered['date'].isna().all():
        # Group by Month
        trend = df_filtered.groupby([pd.Grouper(key='date', freq='M'), 'Tech_Stack']).size().reset_index(name='Count')
        fig2 = px.line(trend, x='date', y='Count', color='Tech_Stack', markers=True)
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.warning("Date data is missing or invalid.")

with tab3:
    st.subheader("Top Companies Hiring for these Roles")
    if not df_filtered.empty:
        top_companies = df_filtered['company'].value_counts().head(10).index
        df_top = df_filtered[df_filtered['company'].isin(top_companies)]

        fig3 = px.histogram(df_top, y='company', color='Tech_Stack', barmode='stack')
        st.plotly_chart(fig3, use_container_width=True)
