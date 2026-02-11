# CLAUDE.md — Tech & Engineering Talent Radar v4

## Project Overview

A B2B market intelligence dashboard analyzing Singapore's tech and engineering job market. Built by SCTP Group 6. The core innovation is the **Talent Scarcity Index** and **Quadrant of Pain** analysis, which maps salary cost vs. applicant supply to determine how hard and expensive it is to fill specific roles.

The project contains two separate Streamlit applications:
- **app.py** — B2B dashboard for CTOs, investors, and recruiters (market intelligence)
- **app_recommender.py** — B2C job recommender for job seekers (personalized matching)

These are intentionally separate apps with different audiences.

## Tech Stack

- **Language:** Python 3
- **Web framework:** Streamlit (>=1.30.0)
- **Data processing:** Pandas (>=2.0.0), NumPy (>=1.24.0)
- **Visualization:** Plotly Express (>=5.18.0)
- **Pattern matching:** `re` (stdlib) for regex-based tech stack extraction from job titles

## Repository Structure

```
tech-talent-radar/
├── app.py                     # Main B2B Streamlit dashboard (130 lines)
├── data_processor_v4.py       # ETL pipeline: raw CSV → processed ZIP (121 lines)
├── app_recommender.py         # B2C job recommender app (421 lines)
├── requirements.txt           # Python dependencies (4 packages)
├── .gitignore                 # Excludes data files, caches, venv
├── README.md                  # Project documentation
├── code_explanation.md        # Architecture notes
└── claude_opus_code_review.md # Prior code review
```

All source files are at the repository root. There is no package hierarchy or subdirectory structure.

## Data Pipeline

```
tech_talent_radar.csv (raw, ~256MB, gitignored)
        ↓  python data_processor_v4.py
tech_talent_radar_final_v4.zip (processed, committed when available)
        ↓  streamlit run app.py
Dashboard with 4 tabs: Salary, Demand, Scarcity, Quadrant of Pain
```

**Important:** The raw CSV (`tech_talent_radar.csv`) and recommender data (`SGJobData.csv`) are gitignored and not in the repository. The processed ZIP output must be generated locally before the dashboard will run.

## Key Source Files

### app.py — Main Dashboard

Entry point: `streamlit run app.py`

- `load_data()` — Cached loader for processed ZIP file
- Sidebar with sector filter (radio) and tech stack multiselect
- 4 KPI metrics row: Active Roles, Avg Salary, Avg Applicants, Dominant Skill
- Tab 1 (Salary): Box plot of salary distributions by tech stack
- Tab 2 (Demand): Line chart of job posting trends over time
- Tab 3 (Scarcity): Bar chart with RdYlGn color scale for applicants per role
- Tab 4 (Quadrant of Pain): Scatter plot of Cost vs. Difficulty with reference lines

### data_processor_v4.py — ETL Pipeline

Entry point: `python data_processor_v4.py`

Processing steps:
1. Load raw CSV
2. Filter rows to "Information Technology" and "Engineering" categories (parsed from JSON)
3. Rename columns to standardized names
4. Tag tech stacks via regex matching on job titles (11 categories)
5. Clean numeric fields (salary, application counts)
6. Save as compressed ZIP

Tech stack regex patterns are defined in the `TECH_KEYWORDS` dict (line 13-25). The patterns use word-boundary matching (`\b`) on lowercased job titles.

Output columns: `job_title, company, category, salary_avg, date, Tech_Stack, num_applications`

### app_recommender.py — Job Recommender

Entry point: `streamlit run app_recommender.py`

**Note:** This app depends on `backend.recommendation_engine.JobRecommendationEngine` which is **not included in the repository**. It also requires `SGJobData.csv` which is gitignored. This app will not run without those dependencies.

## How to Run

```bash
# Install dependencies
pip install -r requirements.txt

# Generate processed data (requires tech_talent_radar.csv in project root)
python data_processor_v4.py

# Run the dashboard
streamlit run app.py
```

## Development Conventions

### Code Style
- snake_case for functions and variables
- UPPER_CASE for module-level constants (e.g., `INPUT_FILE`, `TECH_KEYWORDS`)
- No type hints in app.py or data_processor_v4.py; app_recommender.py uses some (`List[str]`, `pd.DataFrame`)
- No docstring standard enforced, but some functions have them

### Streamlit Patterns
- `@st.cache_data` for caching data loaders and computations
- `@st.cache_resource` for caching expensive objects (recommendation engine)
- `st.tabs()` for multi-view layouts
- `st.columns()` for responsive grid layouts
- `st.session_state` for cross-interaction state persistence

### Data Handling
- JSON category fields are parsed with `json.loads()` after replacing single quotes with double quotes
- Numeric cleaning uses regex: `re.sub(r'[^\d.]', '', str(val))`
- Missing average salary is filled from `(salary_min + salary_max) / 2`

## Known Issues

1. **No tests** — No test framework, no test files, zero test coverage
2. **No CI/CD** — No automated pipelines or quality gates
3. **No linting/formatting config** — No flake8, black, mypy, or pre-commit hooks
4. **Bare `except:` clause** — `app.py:53` uses bare `except:` which catches all exceptions silently
5. **Missing backend module** — `app_recommender.py` imports `backend.recommendation_engine` which is not in the repo
6. **Data files not in repo** — Both raw and recommender CSV files are gitignored; new contributors get immediate errors without them
7. **Incomplete requirements.txt** — Only covers the main dashboard dependencies; app_recommender.py may need additional packages for the recommendation engine
