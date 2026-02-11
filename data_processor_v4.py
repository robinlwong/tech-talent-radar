import pandas as pd
import numpy as np
import re
import json

# ==========================================
# CONFIGURATION
# ==========================================
INPUT_FILE = "tech_talent_radar.csv"       
OUTPUT_FILE = "tech_talent_radar_final_v4.zip" 

# Tech Stack Strategy Dictionary
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
        if isinstance(val, str) and val.strip().startswith('['):
            val = val.replace("'", '"') 
            data = json.loads(val)
            return [item.get('category', '') for item in data]
        return []
    except (json.JSONDecodeError, KeyError, TypeError, AttributeError):
        return []

def get_tech_stack(title):
    """Scans title for keywords to assign a 'Stack'."""
    title = str(title).lower()
    for stack, pattern in TECH_KEYWORDS.items():
        if re.search(pattern, title):
            return stack
    return None

def clean_numeric(val):
    """Parses numeric values (salaries, app counts)."""
    try:
        clean_str = re.sub(r'[^\d.]', '', str(val))
        return float(clean_str)
    except (ValueError, TypeError):
        return np.nan

def process():
    print(f"🚀 Starting Data Processor V4...")
    print(f"   Target File: {INPUT_FILE}")
    
    try:
        df = pd.read_csv(INPUT_FILE, low_memory=False)
    except FileNotFoundError:
        print(f"❌ Error: Could not find {INPUT_FILE}.")
        return

    # 1. Filter for IT & Engineering
    print("   Step 1: Filtering for Target Sectors (IT & Eng)...")
    def is_target(row_val):
        cats = parse_categories(row_val)
        return any(c in ['Information Technology', 'Engineering'] for c in cats)
    
    mask = df['categories'].apply(is_target)
    df_filtered = df[mask].copy()
    print(f"   ✅ Retained {len(df_filtered)} relevant rows.")

    # 2. Standardize Column Names
    rename_map = {
        'title': 'job_title',
        'postedCompany_name': 'company',
        'metadata_newPostingDate': 'date',
        'average_salary': 'salary_avg',
        'salary_minimum': 'salary_min',
        'salary_maximum': 'salary_max',
        'metadata_totalNumberJobApplication': 'num_applications' 
    }
    df_filtered.rename(columns=rename_map, inplace=True)

    # 3. Create 'category' column for Dashboard Filters
    def get_main_cat(val):
        cats = parse_categories(val)
        if 'Information Technology' in cats: return 'Information Technology'
        if 'Engineering' in cats: return 'Engineering'
        return 'Other'
    df_filtered['category'] = df_filtered['categories'].apply(get_main_cat)

    # 4. Tag Tech Stacks (Regex Engine)
    print("   Step 2: Tagging Tech Stacks...")
    df_filtered['Tech_Stack'] = df_filtered['job_title'].apply(get_tech_stack)

    # 5. Clean Numeric Data (Salary + Applications)
    print("   Step 3: Cleaning Numeric Data...")
    numeric_cols = ['salary_min', 'salary_max', 'salary_avg', 'num_applications']
    
    for col in numeric_cols:
        if col in df_filtered.columns:
            df_filtered[col] = df_filtered[col].apply(clean_numeric)
    
    # Fill missing average salary
    mask = df_filtered['salary_avg'].isna()
    if 'salary_min' in df_filtered.columns and 'salary_max' in df_filtered.columns:
        df_filtered.loc[mask, 'salary_avg'] = (df_filtered['salary_min'] + df_filtered['salary_max']) / 2

    # 6. Save Optimized ZIP
    print(f"💾 Step 4: Saving to {OUTPUT_FILE}...")
    
    cols_to_keep = ['job_title', 'company', 'category', 'salary_avg', 'date', 'Tech_Stack', 'num_applications']
    final_cols = [c for c in cols_to_keep if c in df_filtered.columns]
    
    df_filtered[final_cols].to_csv(OUTPUT_FILE, index=False, compression='zip')
    print("✅ Done! Data Processor v4 Complete.")

if __name__ == "__main__":
    process()
