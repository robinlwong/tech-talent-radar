import pandas as pd
import numpy as np
import re
import plotly.express as px

# ==========================================
# CONFIGURATION
# ==========================================
INPUT_FILE = "tech-talent-radar.csv"       # Your 256MB raw file
OUTPUT_FILE = "tech_talent_radar_opt.zip"  # The optimized output file

# Define your "Killer Feature" Keywords
TECH_KEYWORDS = {
    'Python': r'\bpython\b',
    'Java': r'\bjava\b',
    'React/JS': r'\b(react|node|javascript|typescript|vue)\b',
    'Cloud/AWS': r'\b(aws|azure|cloud|gcp)\b',
    'Data/AI': r'\b(data|ai|machine learning|nlp|torch)\b',
    'Cybersecurity': r'\b(cyber|security)\b',
    'DevOps': r'\b(devops|sre|ci/cd)\b',
    '.NET/C#': r'\b(\.net|c#)\b'
}

def clean_salary(val):
    """Parses salary strings (e.g., '$5,000') into floats."""
    try:
        clean_str = re.sub(r'[^\d.]', '', str(val))
        return float(clean_str) if clean_str else np.nan
    except:
        return np.nan

def get_tech_stack(title):
    """Scans title for keywords to assign a 'Stack'."""
    title = str(title).lower()
    for stack, pattern in TECH_KEYWORDS.items():
        if re.search(pattern, title):
            return stack
    return None  # Return None if no match found

def process_dataset():
    print(f"🔄 Loading {INPUT_FILE} (this may take a moment)...")
    
    # 1. Load Data
    # low_memory=False handles mixed types in large files
    df = pd.read_csv(INPUT_FILE, low_memory=False)
    
    # 2. Filter for Target Sectors (IT & Engineering)
    print("   Filtering for IT & Engineering...")
    target_sectors = ['Information Technology', 'Engineering']
    
    # Ensure category column exists (adjust 'category' if your column is named 'industry')
    if 'category' not in df.columns:
        # Fallback for common column names
        col = [c for c in df.columns if 'cat' in c.lower() or 'ind' in c.lower()][0]
        print(f"   Warning: 'category' column not found. Using '{col}' instead.")
        df.rename(columns={col: 'category'}, inplace=True)

    # Apply Filter (Case Insensitive)
    mask = df['category'].astype(str).str.lower().apply(
        lambda x: any(s.lower() in x for s in target_sectors)
    )
    df_filtered = df[mask].copy()
    
    print(f"   ✅ Row Count: {len(df)} -> {len(df_filtered)} (Reduced by {100 - int(len(df_filtered)/len(df)*100)}%)")

    # 3. Scan Titles (The "Market Scan")
    print("\n📊 Top 20 Most Common Titles (Use these to refine keywords):")
    print(df_filtered['job_title'].value_counts().head(20))
    print("-" * 50)

    # 4. Clean Salaries & Tag Stacks
    print("   Cleaning salaries and tagging skills...")
    # Normalize salary column names
    if 'min_salary' in df_filtered.columns:
        df_filtered.rename(columns={'min_salary': 'salary_min', 'max_salary': 'salary_max'}, inplace=True)
    
    df_filtered['salary_min'] = df_filtered['salary_min'].apply(clean_salary)
    df_filtered['salary_max'] = df_filtered['salary_max'].apply(clean_salary)
    df_filtered['salary_avg'] = (df_filtered['salary_min'] + df_filtered['salary_max']) / 2
    
    # Apply Keyword Tagging
    df_filtered['Tech_Stack'] = df_filtered['job_title'].apply(get_tech_stack)

    # 5. Build "Stack vs Salary" Chart
    print("   Generating 'Stack vs Salary' Chart...")
    df_chart = df_filtered.dropna(subset=['salary_avg', 'Tech_Stack'])
    
    if not df_chart.empty:
        fig = px.box(df_chart, x='Tech_Stack', y='salary_avg', 
                     color='Tech_Stack', 
                     title="Tech Stack vs Salary (The Killer Feature)",
                     points=False) # Hide points to keep chart clean
        fig.write_html("stack_vs_salary_chart.html")
        print("   ✅ Chart saved as 'stack_vs_salary_chart.html'")
    else:
        print("   ⚠️ Not enough data to generate chart.")

    # 6. Save Optimized File
    print(f"💾 Saving optimized file to {OUTPUT_FILE}...")
    
    # Select only useful columns
    cols_to_keep = ['job_title', 'company', 'category', 'salary_min', 'salary_max', 'salary_avg', 'date', 'Tech_Stack']
    final_cols = [c for c in cols_to_keep if c in df_filtered.columns]
    
    # Save as ZIP (This is the key step for file size)
    df_filtered[final_cols].to_csv(OUTPUT_FILE, index=False, compression='zip')
    print("✅ Success! You can now upload the .zip file to GitHub.")

if __name__ == "__main__":
    process_dataset()