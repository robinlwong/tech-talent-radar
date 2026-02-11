import pandas as pd
import numpy as np
import re

# ==========================================
# 1. CONFIGURATION: The "Skill Dictionaries"
# ==========================================
# These regex patterns are your "IP". They map messy titles to clean Skill Tags.

IT_KEYWORDS = {
    # --- DATA & AI ---
    'Python': r'\bpython\b',
    'SQL': r'\bsql\b',
    'Data Science/AI': r'\b(data scien|machine learning|deep learning|ai|nlp|torch|tensorflow)\b',
    'Data Analyst': r'\b(data analyst|business intelligence|tableau|power bi)\b',

    # --- CLOUD & DEVOPS ---
    'AWS': r'\baws\b',
    'Azure': r'\bazure\b',
    'Cloud (Gen)': r'\b(cloud|gcp)\b',
    'DevOps': r'\b(devops|sre|site reliability|ci/cd|jenkins|kubernetes|docker|terraform)\b',

    # --- WEB DEV ---
    'React/JS': r'\b(react|angular|vue|node|javascript|typescript|frontend|full stack|fullstack)\b',
    'Java (Backend)': r'\b(java|spring|boot)\b',
    '.NET/C#': r'\b(\.net|c#|asp\.net)\b',
    'PHP/Laravel': r'\b(php|laravel)\b',

    # --- SPECIALIZED ---
    'Cybersecurity': r'\b(cyber|security|infosec|penetration)\b',
    'Blockchain': r'\b(blockchain|web3|crypto)\b',
    'Mobile Dev': r'\b(ios|android|flutter|react native|swift|kotlin)\b'
}

ENG_KEYWORDS = {
    # --- CIVIL / INFRA ---
    'Civil/Structural': r'\b(civil|structural|concrete|steel)\b',
    'Geotechnical/Tunnel': r'\b(geotechnical|tunnel|soil|excavation)\b',
    'M&E (Building)': r'\b(m&e|mechanical and electrical|building services)\b',

    # --- HARDWARE / MECH ---
    'Mechanical': r'\b(mechanical|hvac|piping)\b',
    'Electrical': r'\b(electrical|power|high voltage|switchgear)\b',
    'Electronics': r'\b(electronics|pcb|embedded|firmware|semiconductor|wafer)\b',

    # --- PROCESS / IND ---
    'Chemical/Process': r'\b(chemical|process eng|refinery|oil and gas)\b',
    'Marine/Offshore': r'\b(marine|offshore|naval|ship)\b'
}

# ==========================================
# 2. HELPER FUNCTIONS
# ==========================================

def clean_salary(val):
    """
    Parses salary columns which might be strings like '$5,000' or '5000'.
    Returns a float or NaN.
    """
    try:
        # If it's already a number, return it
        if isinstance(val, (int, float)):
            return float(val)

        # Remove '$', ',', ' ' and convert to float
        clean_str = re.sub(r'[^\d.]', '', str(val))
        return float(clean_str) if clean_str else np.nan
    except:
        return np.nan

def get_skills(row, it_dict, eng_dict):
    """
    Applies the correct dictionary based on the category.
    """
    title = str(row['job_title']).lower()
    found_skills = []

    # Decide which dictionary to use
    # Note: Adjust 'Information Technology' to match your exact CSV category string
    if 'information technology' in str(row['category']).lower():
        target_dict = it_dict
    elif 'engineering' in str(row['category']).lower():
        target_dict = eng_dict
    else:
        return ['Other'] # Should be filtered out anyway

    # Check patterns
    for skill, pattern in target_dict.items():
        if re.search(pattern, title):
            found_skills.append(skill)

    return found_skills if found_skills else ['General/Management']

# ==========================================
# 3. MAIN EXECUTION
# ==========================================

def process_data(input_file, output_file):
    print(f"🔄 Loading {input_file}...")

    # 1. Load Data
    # low_memory=False helps with mixed types in large files
    df = pd.read_csv(input_file, low_memory=False)
    print(f"   Original Rows: {len(df)}")

    # 2. Filter for Target Sectors
    # Make sure to check your CSV for exact spelling of these categories!
    target_sectors = ['Information Technology', 'Engineering', 'Sciences / Laboratory / R&D']

    # Normalizing category column to handle case sensitivity
    df['category_lower'] = df['category'].astype(str).str.lower()

    # Create mask
    mask = df['category_lower'].apply(lambda x: any(sect.lower() in x for sect in target_sectors))
    df_clean = df[mask].copy()

    print(f"   Filtered Rows (IT/Eng): {len(df_clean)}")

    # 3. Clean Salary
    # Assuming columns are 'salary_min' and 'salary_max'. Change if different.
    print("   Cleaning Salaries...")
    if 'min_salary' in df_clean.columns: # Handle common variations
        df_clean.rename(columns={'min_salary': 'salary_min', 'max_salary': 'salary_max'}, inplace=True)

    df_clean['salary_min'] = df_clean['salary_min'].apply(clean_salary)
    df_clean['salary_max'] = df_clean['salary_max'].apply(clean_salary)

    # Drop rows with no salary info (optional, but recommended for charts)
    df_clean = df_clean.dropna(subset=['salary_min'])

    # Create Average Salary
    df_clean['salary_avg'] = (df_clean['salary_min'] + df_clean['salary_max']) / 2

    # 4. Tag Skills
    print("   Tagging Skills (Regex Engine)...")
    df_clean['Skills'] = df_clean.apply(
        lambda row: get_skills(row, IT_KEYWORDS, ENG_KEYWORDS), axis=1
    )

    # 5. Explode
    # This duplicates rows: One row for "Java", one for "AWS" if both in title
    print("   Exploding Skill Rows...")
    df_exploded = df_clean.explode('Skills')

    # 6. Save
    print(f"💾 Saving to {output_file}...")
    # Select only columns needed for dashboard to keep file small
    cols_to_keep = ['job_title', 'company', 'category', 'salary_avg', 'Skills', 'date']

    # Only keep columns that actually exist in your dataframe
    final_cols = [c for c in cols_to_keep if c in df_exploded.columns]

    df_exploded[final_cols].to_csv(output_file, index=False)
    print("✅ Done! Success.")

if __name__ == "__main__":
    # CHANGE THIS to your actual file name
    INPUT_CSV = "DS2F M1 Assignment Project Team - Sheet1.csv"
    OUTPUT_CSV = "tech_talent_radar_processed.csv"

    process_data(INPUT_CSV, OUTPUT_CSV)
