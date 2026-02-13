import os
import json
from typing import List

import pandas as pd
import streamlit as st

from backend.recommendation_engine import JobRecommendationEngine


CSV_PATH = os.path.join(os.path.dirname(__file__), "SGJobData.csv")

@st.cache_data
def get_skill_options(_engine: JobRecommendationEngine) -> List[str]:
    """
    Get the list of all skills that can be inferred from jobs.
    This ensures user-selectable skills match what the engine can actually find.
    The leading underscore tells Streamlit not to hash this argument.
    """
    return _engine.get_all_inferable_skills()


@st.cache_data(show_spinner="Loading job data (this can take a while the first time)...")
def load_job_data() -> pd.DataFrame:
    """Load and preprocess the SG job data CSV."""
    if not os.path.exists(CSV_PATH):
        raise FileNotFoundError(f"CSV file not found at {CSV_PATH}")

    df = pd.read_csv(
        CSV_PATH,
        low_memory=False,
        dtype={
            "salary_minimum": "float64",
            "salary_maximum": "float64",
            "average_salary": "float64",
            "minimumYearsExperience": "float64",
            "numberOfVacancies": "float64",
            "metadata_totalNumberJobApplication": "float64",
            "metadata_totalNumberOfView": "float64",
        },
    )

    def parse_categories(x):
        if pd.isna(x):
            return []
        try:
            return json.loads(x) if isinstance(x, str) else x
        except (json.JSONDecodeError, TypeError):
            return []

    df["categories"] = df["categories"].apply(parse_categories)
    return df


@st.cache_data
def compute_stats(df: pd.DataFrame):
    """Compute basic stats and unique values for filters."""
    all_categories = set()
    for cats in df["categories"]:
        if isinstance(cats, list):
            for cat in cats:
                if isinstance(cat, dict) and "category" in cat:
                    all_categories.add(cat["category"])

    position_levels = (
        df["positionLevels"].dropna().astype(str).sort_values().unique().tolist()
    )
    employment_types = (
        df["employmentTypes"].dropna().astype(str).sort_values().unique().tolist()
    )

    salary_stats = {
        "min": float(df["salary_minimum"].min())
        if not df["salary_minimum"].isna().all()
        else 0,
        "max": float(df["salary_maximum"].max())
        if not df["salary_maximum"].isna().all()
        else 0,
        "avg": float(df["average_salary"].mean())
        if not df["average_salary"].isna().all()
        else 0,
    }

    return sorted(all_categories), position_levels, employment_types, salary_stats


@st.cache_resource(show_spinner="Initializing recommendation engine...")
def get_recommendation_engine(df: pd.DataFrame) -> JobRecommendationEngine:
    """Create and cache the recommendation engine."""
    return JobRecommendationEngine(df.copy())


def filter_jobs(
    df: pd.DataFrame,
    search: str = "",
    category: str = "",
    min_salary=None,
    max_salary=None,
    position_level: str = "",
    employment_type: str = "",
) -> pd.DataFrame:
    """Apply the same filters as the Flask API."""
    filtered_df = df.copy()

    if search:
        s = search.lower()
        filtered_df = filtered_df[
            filtered_df["title"].astype(str).str.lower().str.contains(s, na=False)
            | filtered_df["postedCompany_name"]
            .astype(str)
            .str.lower()
            .str.contains(s, na=False)
        ]

    if category:
        filtered_df = filtered_df[
            filtered_df["categories"].apply(
                lambda cats: any(
                    cat.get("category", "") == category for cat in cats
                )
                if isinstance(cats, list)
                else False
            )
        ]

    if min_salary is not None:
        filtered_df = filtered_df[
            filtered_df["salary_minimum"].fillna(0) >= float(min_salary)
        ]

    if max_salary is not None:
        filtered_df = filtered_df[
            filtered_df["salary_maximum"].fillna(float("inf")) <= float(max_salary)
        ]

    if position_level:
        filtered_df = filtered_df[filtered_df["positionLevels"] == position_level]

    if employment_type:
        filtered_df = filtered_df[filtered_df["employmentTypes"] == employment_type]

    return filtered_df


def parse_categories_str(categories_value) -> str:
    """Turn categories JSON/list into a readable string."""
    if isinstance(categories_value, list):
        return ", ".join(
            cat.get("category", "") for cat in categories_value if isinstance(cat, dict)
        )
    try:
        cats = json.loads(categories_value)
        if isinstance(cats, list):
            return ", ".join(
                cat.get("category", "") for cat in cats if isinstance(cat, dict)
            )
    except Exception:
        pass
    return ""


def main():
    st.set_page_config(
        page_title="SG Job Recommender (SCTP Group 6)",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.title("🇸🇬 AI-Powered Job Recommendation System (SCTP Group 6)")
    st.write(
        "Browse jobs, create your profile, and get personalized recommendations "
        "with skill gap analysis — all in one Python app."
    )

    df = load_job_data()
    categories, position_levels, employment_types, salary_stats = compute_stats(df)
    engine = get_recommendation_engine(df)
    
    # Get skills that can actually be inferred from jobs
    skill_options = get_skill_options(engine)

    if "user_profile" not in st.session_state:
        st.session_state.user_profile = None

    tab_browse, tab_profile, tab_reco = st.tabs(
        ["🔍 Browse Jobs", "👤 Profile & Preferences", "🎯 Recommendations"]
    )

    # ----- Profile Tab -----
    with tab_profile:
        st.subheader("Your Profile")

        with st.form("profile_form"):
            name = st.text_input("Name", value="")
            education = st.selectbox(
                "Education Level",
                ["", "NITEC", "Higher NITEC", "Diploma", "Degree", "Master", "PhD"],
            )
            qualification = st.text_input(
                "Qualification / Field (e.g., Information Technology, Business)"
            )
            skills_selected = st.multiselect(
                "Skills (choose those that best match you)",
                options=[s.title() for s in skill_options],
                help="These skills are aligned with what jobs actually require, ensuring better matching."
            )
            experience = st.text_area(
                "Work Experience",
                placeholder="Describe your work experience and roles",
            )
            coursework = st.text_area(
                "Relevant Coursework / Training",
                placeholder="List any relevant courses, certifications, or training",
            )
            preferred_categories = st.multiselect(
                "Preferred Job Categories", options=categories
            )
            preferred_position_level = st.selectbox(
                "Preferred Position Level", [""] + position_levels
            )
            years_of_exp = st.number_input(
                "Years of Experience", min_value=0, max_value=50, value=0
            )

            submitted = st.form_submit_button("Save Profile")

        if submitted:
            # Convert selected skills back to lower-case tokens for the engine
            skills_list = [s.lower() for s in skills_selected]
            st.session_state.user_profile = {
                "user_id": "streamlit_user",
                "name": name,
                "education": education,
                "qualification": qualification,
                "skills": skills_list,
                "experience": experience,
                "coursework": coursework,
                "preferred_categories": preferred_categories,
                "preferred_position_level": preferred_position_level,
                "years_of_experience": years_of_exp,
            }
            st.success("Profile saved! Go to the Recommendations tab to see matches.")

        if st.session_state.user_profile:
            with st.expander("Current profile (debug view)", expanded=False):
                st.json(st.session_state.user_profile)

    # ----- Browse Jobs Tab -----
    with tab_browse:
        st.subheader("Browse Jobs")

        with st.sidebar:
            st.markdown("### Filters")
            search = st.text_input("Search title / company")
            category = st.selectbox("Category", [""] + categories)
            pos_level = st.selectbox("Position Level", [""] + position_levels)
            emp_type = st.selectbox("Employment Type", [""] + employment_types)
            col_min, col_max = st.columns(2)
            with col_min:
                min_salary = st.number_input("Min Salary", min_value=0, value=0)
            with col_max:
                max_salary = st.number_input("Max Salary", min_value=0, value=0)

        filtered = filter_jobs(
            df,
            search=search,
            category=category,
            min_salary=min_salary if min_salary > 0 else None,
            max_salary=max_salary if max_salary > 0 else None,
            position_level=pos_level,
            employment_type=emp_type,
        )

        st.write(
            f"Showing **{min(len(filtered), 200):,}** of **{len(filtered):,}** matching jobs"
        )
        if len(filtered) == 0:
            st.info("No jobs found. Try relaxing your filters.")
        else:
            display_cols = [
                "title",
                "postedCompany_name",
                "positionLevels",
                "employmentTypes",
                "salary_minimum",
                "salary_maximum",
                "salary_type",
                "minimumYearsExperience",
            ]
            display_df = filtered[display_cols].head(200).copy()
            st.dataframe(display_df, use_container_width=True)

    # ----- Recommendations Tab -----
    with tab_reco:
        st.subheader("Personalized Recommendations")

        profile = st.session_state.user_profile
        if not profile:
            st.info(
                "Please create your profile in the **Profile & Preferences** tab first."
            )
            return

        top_n = st.slider("Number of recommendations", 5, 30, 10)

        if st.button("Get Recommendations"):
            with st.spinner("Analyzing your profile and finding best matches..."):
                recs = engine.recommend_jobs(profile, top_n=top_n)

            if not recs:
                st.warning(
                    "No recommendations found. Try adding more skills or preferred categories."
                )
                return

            # ----- Summary visualizations -----
            summary_rows = []
            for rec in recs:
                job = rec["job"]
                gap = rec["skill_gap"]
                summary_rows.append(
                    {
                        "Job": job.get("title", "(No title)"),
                        "Company": job.get("postedCompany_name", ""),
                        "Match %": gap["match_percentage"],
                        "Relevance Score": rec.get("similarity_score", 0) * 100,
                        "Matching Skills": gap["user_has"],
                        "Required Skills": gap["total_required"],
                    }
                )

            summary_df = pd.DataFrame(summary_rows)

            st.subheader("Recommendation Overview")
            col_chart1, col_chart2 = st.columns(2)

            with col_chart1:
                st.markdown("**Skill Match by Job**")
                st.bar_chart(
                    summary_df.set_index("Job")["Match %"],
                    use_container_width=True,
                )

            with col_chart2:
                st.markdown("**Relevance Score by Job**")
                st.bar_chart(
                    summary_df.set_index("Job")["Relevance Score"],
                    use_container_width=True,
                )

            total_required = int(summary_df["Required Skills"].sum())
            total_have = int(summary_df["Matching Skills"].sum())
            if total_required > 0:
                coverage = round(100 * total_have / total_required, 1)
            else:
                coverage = 0.0

            st.markdown("**Overall Skill Coverage Across Recommended Jobs**")
            st.metric(
                "Coverage",
                f"{coverage}%",
                help="Across all recommended jobs, what percentage of required skills you already have.",
            )

            for i, rec in enumerate(recs, start=1):
                job = rec["job"]
                gap = rec["skill_gap"]

                with st.expander(
                    f"{i}. {job.get('title','(No title)')} – "
                    f"{job.get('postedCompany_name','(No company)')} "
                    f"({gap['match_percentage']}% skill match)"
                ):
                    col_left, col_right = st.columns([2, 1])

                    with col_left:
                        st.markdown(f"**Company:** {job.get('postedCompany_name')}")
                        st.markdown(
                            f"**Position Level:** {job.get('positionLevels','N/A')}  "
                            f"**Employment Type:** {job.get('employmentTypes','N/A')}"
                        )
                        st.markdown(
                            f"**Salary:** {job.get('salary_minimum','?')} - "
                            f"{job.get('salary_maximum','?')} "
                            f"{job.get('salary_type','')}"
                        )
                        st.markdown(
                            f"**Experience Required:** "
                            f"{job.get('minimumYearsExperience',0)} years"
                        )
                        st.markdown(
                            f"**Categories:** {parse_categories_str(job.get('categories'))}"
                        )

                        st.markdown("**Why this job?**")
                        st.write(rec.get("recommendation_reason", ""))

                    with col_right:
                        st.markdown("**Skill Match**")
                        st.metric(
                            "Match %",
                            f"{gap['match_percentage']}%",
                            help="Percentage of required skills you already have.",
                        )
                        st.write(
                            f"You have {gap['user_has']} of "
                            f"{gap['total_required']} required skills."
                        )

                        if gap["matching_skills"]:
                            st.markdown("✅ **Your Matching Skills**")
                            st.write(", ".join(sorted(gap["matching_skills"])))

                        if gap["missing_skills"]:
                            st.markdown("📚 **Skills to Learn**")
                            st.write(", ".join(sorted(gap["missing_skills"])))


if __name__ == "__main__":
    main()

