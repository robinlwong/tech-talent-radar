Reviewed app.py, data_processor_v4.py, and requirements.txt files
Show more
Show more
Show more

Here's a summary of the 5 recent commits, from oldest to newest:

Commit History Summary
1. c4cb238 — Initial project scaffold

Created the Streamlit dashboard (app.py) with 3 views: Demand, Salary, Competitors
Added data_processor.py with regex-based skill extraction from raw CSV
Included mock data fallback for demo mode
Project is a Singapore job market intelligence tool (Group 6 project)
2. b332b3f — Column mapping fix + new tools

Updated data_processor.py to handle real dataset columns (title, categories as JSON, postedCompany_name, etc.)
Added app_recommender.py (AI-powered job recommendation, separate B2C tool)
Added optimize_data.py for compressing large datasets
Added sample_data.xlsx for testing
3. 806a5d2 — Major cleanup and v3 processor

Replaced data_processor.py with data_processor_v3.py
Cleaned up app.py to read from tech_talent_radar_final.zip
Deleted app_recommender.py, data_processor.py (v1), optimize_data.py, sample_data.xlsx
4. 9f6169c — Restored app_recommender.py

Re-added the recommender that was deleted in the previous commit
5. be03df9 (HEAD) — v4 with Talent Scarcity + Quadrant of Pain

Added data_processor_v4.py with num_applications field
Expanded dashboard to 4 tabs: Salary, Demand, Scarcity, Quadrant of Pain
New "Talent Supply Heatmap" and "Cost vs. Difficulty" bubble chart
Items That Need Attention
Stale data_processor_v3.py still in the repo. The app now uses data_processor_v4.py and reads tech_talent_radar_final_v4.zip, but data_processor_v3.py (which outputs a different zip file) is still present. It should either be removed or kept intentionally for reference.

Bare except: clauses throughout the code. Both app.py:53 and data_processor_v4.py:35-36,51-52 use bare except: blocks that silently swallow all exceptions. These can hide real bugs — at minimum they should catch specific exceptions (e.g., except (json.JSONDecodeError, KeyError):, except ValueError:).

app_recommender.py was deleted then immediately restored. The commit history shows a delete in 806a5d2 followed by a restore in 9f6169c. This 421-line file is not referenced by app.py and appears to be a standalone tool. Its role in the project should be clarified — if it's a separate app, consider documenting how to run it, or moving it to a subdirectory.

No data file committed. The app expects tech_talent_radar_final_v4.zip (and the raw tech_talent_radar.csv for the processor), but neither is in the repo. There's no .gitignore entry explaining this, and no instructions in the README about obtaining the data. New contributors will hit the st.error("Data file not found") wall immediately.

No tests or CI. The project has no test suite, linting, or CI pipeline. Given the rapid iteration (5 commits in one day with breaking changes), automated checks would help prevent regressions.

requirements.txt may be incomplete. app_recommender.py likely has additional dependencies (it's 421 lines and described as "AI-powered") that aren't listed in requirements.txt, which only includes streamlit, pandas, numpy, and plotly.
