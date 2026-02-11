Repository Overview: Tech & Engineering Talent Radar v4
Purpose: A B2B market intelligence dashboard for analyzing Singapore's tech job market. It answers the question: "How hard and expensive is it to fill a role?" by mapping salary cost vs. applicant supply across 11 tech stack categories.

Tech Stack
Layer	Technology
Language	Python 3
Web framework	Streamlit (>=1.30.0)
Data processing	Pandas (>=2.0.0), NumPy (>=1.24.0)
Visualization	Plotly (>=5.18.0)
Skill extraction	Regex pattern matching on job titles
No build tools, Docker, CI/CD, or test framework present.

Main Entry Points
app.py — Primary Streamlit dashboard (streamlit run app.py). Loads processed data from a compressed ZIP and renders 4 interactive tabs: Salary Distribution, Demand Trends, Supply Scarcity, and the "Quadrant of Pain" (cost vs. difficulty).

data_processor_v4.py — ETL pipeline (python data_processor_v4.py). Ingests a raw ~256MB CSV, filters for IT & Engineering jobs, applies regex-based tech stack tagging across 11 categories, cleans salary/application data, and outputs a compressed ZIP for the dashboard.

app_recommender.py — Separate B2C Streamlit app for job seekers with AI-powered recommendations. Depends on a backend/recommendation_engine.py module that is not included in the repo.

Data Flow
Raw CSV (~1M rows) → data_processor_v4.py → compressed ZIP → app.py (dashboard)

Project Structure
All source files live at the root level — no nested packages or subdirectories. Key files: requirements.txt for dependencies, README.md for documentation, and a claude-opus-code-review file with prior review notes.

Notable Observations
The v4 "Talent Scarcity Index" and "Quadrant of Pain" analysis are the key differentiators
Data files (CSVs, ZIPs) are gitignored and not in the repo
No tests, linting, or CI — designed for rapid iteration
app_recommender.py has undeclared dependencies (missing backend module)
