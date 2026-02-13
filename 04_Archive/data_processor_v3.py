import pandas as pd
import numpy as np
import re
import json

# ==========================================
# CONFIGURATION
# ==========================================
# 1. CHANGE THIS to your large file name
INPUT_FILE = "tech_talent_radar.csv"
OUTPUT_FILE = "tech_talent_radar_final.zip"

# 2. Define Tech Stack Keywords (The Strategy Engine)
TECH_KEYWORDS = {
    'Python': r'\bpython\b',
    'Java': r'\bjava\b',
    'React/JS': r'\b(react|node|javascript|typescript|vue|angular)\b',
    'Cloud/AWS': r'\b(aws|azure|cloud|gcp|google cloud)\b',
    'Data/AI': r'\b(data|ai|machine learning|nlp|torch|tensorflow|bi|tableau)\b',
    'Cybersecurity': r'\b(cyber|security|infosec)\b',
    'DevOps': r'\b(devops|sre|ci/cd|kubernetes|docker|jenkins)\b',
    '.NET/C#': r'\b(\.net|c#|dotnet)\b',
    'Civil/Struct': r'\b(civil|structural|tunnel|bridge|geotechnical)\b',
    'Mechanical': r'\b(mechanical|hvac|piping|m&e)\b',
    'Electrical': r'\b(electrical|power|switchgear)\b'
}

def parse_categories(val):
    """Extracts category names from JSON string."""
    try:
        # Handle string representation of list
        if isinstance(val, str) and val.strip().startswith('['):
            # Safe eval or json load
            val = val.replace("'", '"') # Fix common quote issues
            data = json.loads(val)
            return [item.get('category', '') for item in data]
        return []
    except:
        return []

def get_tech_stack(title):
    """Scans title for keywords to assign a 'Stack'."""
    title = str(title).lower()
    for stack, pattern in TECH_KEYWORDS.items():
        if re.search(pattern, title):
            return stack
    return None

def clean_salary(val):
    try:
        return float(val)
    except:
        return np.nan

def process():
    print(f"🔄 Loading {INPUT_FILE}...")
    try:
        df = pd.read_csv(INPUT_FILE, low_memory=False)
    except FileNotFoundError:
        print(f"❌ Error: Could not find {INPUT_FILE}. Please rename your large file.")
        return

    # 1. Filter for IT & Engineering (Using JSON parsing)
    print("   Parsing Categories & Filtering...")

    # Helper to filter rows
    def is_target(row_val):
        cats = parse_categories(row_val)
        return any(c in ['Information Technology', 'Engineering'] for c in cats)

    mask = df['categories'].apply(is_target)
    df_filtered = df[mask].copy()
    print(f"   ✅ Filtered down to {len(df_filtered)} rows.")

    # 2. Rename Columns to Standard Names
    print("   Standardizing Columns...")
    rename_map = {
        'title': 'job_title',
        'postedCompany_name': 'company',
        'metadata_newPostingDate': 'date',
        'average_salary': 'salary_avg',
        'salary_minimum': 'salary_min',
        'salary_maximum': 'salary_max'
    }
    df_filtered.rename(columns=rename_map, inplace=True)

    # 3. Create 'category' column (Simple string for dashboard)
    def get_main_cat(val):
        cats = parse_categories(val)
        if 'Information Technology' in cats: return 'Information Technology'
        if 'Engineering' in cats: return 'Engineering'
        return 'Other'
    df_filtered['category'] = df_filtered['categories'].apply(get_main_cat)

    # 4. Tag Tech Stacks
    print("   Tagging Tech Stacks...")
    df_filtered['Tech_Stack'] = df_filtered['job_title'].apply(get_tech_stack)

    # 5. Clean Salary
    for col in ['salary_min', 'salary_max', 'salary_avg']:
        if col in df_filtered.columns:
            df_filtered[col] = df_filtered[col].apply(clean_salary)

    # Fill missing average if min/max exist
    mask = df_filtered['salary_avg'].isna()
    df_filtered.loc[mask, 'salary_avg'] = (df_filtered['salary_min'] + df_filtered['salary_max']) / 2

    # 6. Save
    print(f"💾 Saving to {OUTPUT_FILE}...")
    cols = ['job_title', 'company', 'category', 'salary_avg', 'date', 'Tech_Stack']
    # Filter for existing columns only
    final_cols = [c for c in cols if c in df_filtered.columns]

    df_filtered[final_cols].to_csv(OUTPUT_FILE, index=False, compression='zip')
    print("✅ Done! Ready for Dashboard.")

if __name__ == "__main__":
    process()