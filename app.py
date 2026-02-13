import streamlit as st
import pandas as pd
import plotly.express as px

# TECH TALENT RADAR DASHBOARD v4
# Code with comments explicitly highlighting every change made to fix the Streamlit deprecation warnings, 
# the Pandas future warnings, and stability issues.

# 1. PAGE SETUP
st.set_page_config(page_title="Tech Talent Radar v4", layout="wide")

# 2. LOAD DATA
@st.cache_data
def load_data():
    # Load the v4 data
    try:
        df = pd.read_csv("tech_talent_radar_final_v4.zip")
        # CHANGE: Added check to ensure 'date' exists before converting
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
        return df
    except FileNotFoundError:
        return None

df = load_data()

# CHANGE: Made error message more specific about the zip file
if df is None:
    st.error("❌ Data file not found. Please ensure 'tech_talent_radar_final_v4.zip' is in the repository!")
    st.stop()

# 3. SIDEBAR & FILTERS
st.title("📡 Tech Talent Radar: Strategic Intelligence")
st.markdown("### The Dashboard for CTOs & Investors")

with st.sidebar:
    st.header("Strategic Filters")
    
    # CHANGE: Added .dropna() to prevent 'nan' from appearing as a category option
    categories = df['category'].dropna().unique()
    selected_cat = st.radio("Sector Scope:", categories)
    
    # Filter by Category
    df_cat = df[df['category'] == selected_cat]
    
    # Filter by Tech Stack
    stacks = df_cat['Tech_Stack'].dropna().unique()
    
    # CHANGE: Added safety check (if len > 0) to prevent crash if category has no stacks
    selected_stacks = st.multiselect("Tech Stacks:", stacks, default=stacks[:6] if len(stacks) > 0 else None)

if selected_stacks:
    df_filtered = df_cat[df_cat['Tech_Stack'].isin(selected_stacks)]
else:
    df_filtered = df_cat

# 4. KPI ROW
c1, c2, c3, c4 = st.columns(4)
c1.metric("Active Roles", len(df_filtered))
c2.metric("Avg Salary", f"${df_filtered['salary_avg'].mean():,.0f}")
c3.metric("Avg Applicants/Role", f"{df_filtered['num_applications'].mean():.1f}")
try:
    top_stack = df_filtered['Tech_Stack'].mode()[0]
except:
    top_stack = "N/A"
c4.metric("Dominant Skill", top_stack)

st.divider()

# 5. THE STRATEGIC TABS
tab1, tab2, tab3, tab4 = st.tabs([
    "💰 Salary (Price)", 
    "📈 Demand (Volume)", 
    "⚠️ Scarcity (Supply)", 
    "🎯 The Quadrant (Strategy)"
])

# Tab 1: Salary
with tab1:
    st.subheader("Market Price Analysis")
    # CHANGE: Added empty check to prevent Plotly errors if filter returns 0 rows
    if not df_filtered.empty:
        order = df_filtered.groupby('Tech_Stack')['salary_avg'].median().sort_values(ascending=False).index
        fig = px.box(df_filtered, x='Tech_Stack', y='salary_avg', color='Tech_Stack',
                      category_orders={'Tech_Stack': order}, points=False,
                      title="Salary Distribution by Tech Stack")
        
        # CHANGE: Replaced 'use_container_width=True' (deprecated) with 'width="stretch"'
        st.plotly_chart(fig, width="stretch")

# Tab 2: Demand Trend
with tab2:
    st.subheader("Hiring Momentum")
    if 'date' in df_filtered.columns and not df_filtered['date'].isna().all():
        
        # CHANGE: Replaced freq='M' with freq='ME' (Month End) to fix Pandas FutureWarning
        trend = df_filtered.groupby([pd.Grouper(key='date', freq='ME'), 'Tech_Stack']).size().reset_index(name='Count')
        
        fig2 = px.line(trend, x='date', y='Count', color='Tech_Stack', markers=True,
                        title="Job Posting Volume Over Time")
        
        # CHANGE: Replaced 'use_container_width=True' with 'width="stretch"'
        st.plotly_chart(fig2, width="stretch")
    else:
        st.warning("No valid date data found for the selected filters.")

# Tab 3: Scarcity (The Pivot Feature)
with tab3:
    st.subheader("Talent Supply Heatmap")
    st.markdown("Low applicants (Red) = Hard to Hire. High applicants (Green) = Easy to Hire.")
    
    if not df_filtered.empty:
        scarcity = df_filtered.groupby('Tech_Stack')['num_applications'].mean().reset_index()
        scarcity = scarcity.sort_values('num_applications')
        
        fig3 = px.bar(scarcity, x='Tech_Stack', y='num_applications',
                      color='num_applications',
                      color_continuous_scale='RdYlGn', 
                      title="Average Applicants per Job Posting")
        
        # CHANGE: Replaced 'use_container_width=True' with 'width="stretch"'
        st.plotly_chart(fig3, width="stretch")

# Tab 4: The Strategy Quadrant
with tab4:
    st.subheader("The 'Quadrant of Pain' Analysis")
    st.markdown("**X-Axis:** How much it costs (Salary). **Y-Axis:** How hard to hire (Scarcity).")
    
    if not df_filtered.empty:
        quad_data = df_filtered.groupby('Tech_Stack').agg({
            'salary_avg': 'mean',
            'num_applications': 'mean',
            'job_title': 'count' 
        }).reset_index()
        
        fig4 = px.scatter(quad_data, x='salary_avg', y='num_applications',
                          size='job_title', color='Tech_Stack',
                          text='Tech_Stack',
                          title="Cost vs. Difficulty Matrix",
                          labels={'salary_avg': 'Avg Salary (Cost)', 'num_applications': 'Avg Applicants (Ease of Hire)'})
        
        fig4.add_hline(y=quad_data['num_applications'].mean(), line_dash="dash", annotation_text="Avg Difficulty")
        fig4.add_vline(x=quad_data['salary_avg'].mean(), line_dash="dash", annotation_text="Avg Cost")
        
        # CHANGE: Replaced 'use_container_width=True' with 'width="stretch"'
        st.plotly_chart(fig4, width="stretch")
    
    st.info("""
    **How to read this chart:**
    * **Bottom Right (High Pay, Low Apps):** The "Danger Zone". Hardest to hire. (e.g., DevOps, AI)
    * **Top Left (Low Pay, High Apps):** The "Value Zone". Easy to hire. (e.g., Juniors)
    """)