"""
Tech Talent Radar - Data Processor v2

Transforms raw SG job market CSV into optimized dashboard-ready output.
Handles JSON categories, correct column mappings, and regex skill tagging.

Usage:
    python data_processor.py [--input FILE] [--output FILE]
"""

import pandas as pd
import numpy as np
import re
import json
import sys

# ==========================================
# 1. CONFIGURATION: Skill Dictionaries
# ==========================================

TECH_KEYWORDS = {
    'Python': r'\bpython\b',
    'Java': r'\bjava\b',
    'React/JS': r'\b(react|node|javascript|typescript|vue|angular)\b',
    'Cloud/AWS': r'\b(aws|azure|cloud|gcp|google cloud)\b',
    'Data/AI': r'\b(data|ai|machine learning|nlp|torch|tensorflow|bi|tableau)\b',
    'Cybersecurity': r'\b(cyber|security|infosec)\b',
    'DevOps': r'\b(devops|sre|ci/cd|kubernetes|docker|jenkins)\b',
    '.NET/C#': r'\b(\.net|c#|dotnet)\b',
    'SQL': r'\bsql\b',
    'Mobile Dev': r'\b(ios|android|flutter|react native|swift|kotlin)\b',
    'PHP/Laravel': r'\b(php|laravel)\b',
    'Ruby': r'\bruby\b',
    'Go/Rust': r'\b(golang|go lang|\brust\b)\b',
}

ENG_KEYWORDS = {
    'Civil/Structural': r'\b(civil|structural|concrete|steel|tunnel|bridge|geotechnical)\b',
    'Mechanical': r'\b(mechanical|hvac|piping|m&e)\b',
    'Electrical': r'\b(electrical|power|high voltage|switchgear)\b',
    'Electronics': r'\b(electronics|pcb|embedded|firmware|semiconductor|wafer)\b',
    'Chemical/Process': r'\b(chemical|process eng|refinery|oil and gas)\b',
    'Marine/Offshore': r'\b(marine|offshore|naval|ship)\b',
}

# ==========================================
# 2. HELPER FUNCTIONS
# ==========================================

def parse_categories(val):
    """
    Parses JSON string in 'categories' column.
    Input: '[{"id":21,"category":"Information Technology"}]'
    Output: ['Information Technology']
    """
    try:
        if isinstance(val, list):
            return [x.get('category', '') for x in val]
        if isinstance(val, str) and val.startswith('['):
            data = json.loads(val.replace("'", '"'))
            return [item.get('category', '') for item in data]
        return []
    except Exception:
        return []


def is_target_sector(row_cat_str):
    """Quick check if row belongs to IT or Engineering."""
    if not isinstance(row_cat_str, str):
        return False
    row_lower = row_cat_str.lower()
    if 'information technology' not in row_lower and 'engineering' not in row_lower:
        return False
    cats = parse_categories(row_cat_str)
    return any(c in {'Information Technology', 'Engineering'} for c in cats)


def get_primary_category(val):
    """Get primary category for dashboard filter."""
    cats = parse_categories(val)
    if 'Information Technology' in cats:
        return 'Information Technology'
    if 'Engineering' in cats:
        return 'Engineering'
    return 'Other'


def get_tech_stack(title, category):
    """Scans title for keywords based on category."""
    title = str(title).lower()
    found_stacks = []

    target_dict = TECH_KEYWORDS if category == 'Information Technology' else ENG_KEYWORDS

    for stack, pattern in target_dict.items():
        if re.search(pattern, title):
            found_stacks.append(stack)

    return found_stacks if found_stacks else ['General/Management']


def clean_salary(val):
    """Parses salary to float."""
    try:
        return float(val)
    except (ValueError, TypeError):
        return np.nan


# ==========================================
# 3. MAIN EXECUTION
# ==========================================

def process_data(input_file, output_file):
    print(f"🔄 Loading {input_file}...")

    try:
        df = pd.read_csv(input_file, low_memory=False)
    except FileNotFoundError:
        print(f"❌ Error: {input_file} not found.")
        sys.exit(1)

    print(f"   Original Rows: {len(df):,}")
    print(f"   Columns: {df.columns.tolist()}")

    # Verify expected columns exist
    required = ['title', 'categories']
    missing = [c for c in required if c not in df.columns]
    if missing:
        print(f"❌ Missing required columns: {missing}")
        print(f"   Available columns: {df.columns.tolist()}")
        sys.exit(1)

    # 1. FILTER for IT & Engineering
    print("   Filtering for IT & Engineering...")
    mask = df['categories'].apply(is_target_sector)
    df_filtered = df[mask].copy()
    print(f"   ✅ Filtered: {len(df):,} → {len(df_filtered):,} rows ({100 - int(len(df_filtered)/len(df)*100)}% reduction)")

    # 2. STANDARDIZE COLUMNS
    rename_map = {
        'title': 'job_title',
        'postedCompany_name': 'company',
        'metadata_newPostingDate': 'date',
        'average_salary': 'salary_avg',
        'salary_minimum': 'salary_min',
        'salary_maximum': 'salary_max',
    }
    df_filtered.rename(columns={k: v for k, v in rename_map.items() if k in df_filtered.columns}, inplace=True)

    # 3. ADD CATEGORY COLUMN
    df_filtered['category'] = df_filtered['categories'].apply(get_primary_category)

    # 4. CLEAN SALARIES
    print("   Cleaning salaries...")
    for col in ['salary_min', 'salary_max', 'salary_avg']:
        if col in df_filtered.columns:
            df_filtered[col] = df_filtered[col].apply(clean_salary)

    # Fill salary_avg if missing
    if 'salary_avg' in df_filtered.columns:
        missing_avg = df_filtered['salary_avg'].isna()
        if 'salary_min' in df_filtered.columns and 'salary_max' in df_filtered.columns:
            df_filtered.loc[missing_avg, 'salary_avg'] = (
                df_filtered.loc[missing_avg, 'salary_min'] +
                df_filtered.loc[missing_avg, 'salary_max']
            ) / 2

    # 5. TAG SKILLS (Regex Engine)
    print("   Tagging skills via Regex...")
    df_filtered['Skills'] = df_filtered.apply(
        lambda row: get_tech_stack(row.get('job_title', ''), row.get('category', '')),
        axis=1
    )

    # 6. EXPLODE (one row per skill)
    print("   Exploding skill rows...")
    df_exploded = df_filtered.explode('Skills')

    # 7. PRINT TOP TITLES (for keyword refinement)
    print("\n📊 Top 20 Job Titles (use to refine keywords):")
    print(df_filtered['job_title'].value_counts().head(20))
    print("-" * 50)

    # 8. PRINT SKILL DISTRIBUTION
    print("\n📊 Skill Distribution:")
    print(df_exploded['Skills'].value_counts())
    print("-" * 50)

    # 9. SAVE
    print(f"\n💾 Saving to {output_file}...")
    final_cols = ['job_title', 'company', 'category', 'salary_min', 'salary_max',
                  'salary_avg', 'date', 'Skills', 'positionLevels', 'employmentTypes',
                  'minimumYearsExperience']
    final_cols = [c for c in final_cols if c in df_exploded.columns]

    if output_file.endswith('.zip'):
        df_exploded[final_cols].to_csv(output_file, index=False, compression='zip')
    else:
        df_exploded[final_cols].to_csv(output_file, index=False)

    print(f"✅ Done! {len(df_exploded):,} rows saved to {output_file}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Process SG job data for Tech Talent Radar")
    parser.add_argument("--input", default="tech_talent_radar.csv", help="Input CSV file")
    parser.add_argument("--output", default="tech_talent_radar_processed.csv", help="Output file (.csv or .zip)")
    args = parser.parse_args()

    process_data(args.input, args.output)
