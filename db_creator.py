import pandas as pd
import sqlite3
import os
import numpy as np

# --- Configuration ---
CROP_FILE = "raw_crop_data.csv"
RAIN_FILE = "raw_rainfall_data.csv"
DB_FILE = "data.gov.db"

# These are for the "source" column, ensuring traceability
CROP_API_URL = "https.api.data.gov.in/resource/35be999b-0208-4354-b557-f6ca9a5355de"
RAIN_API_URL = "https.api.data.gov.in/resource/6c05cd1b-ed59-40c2-bc31-e314f39c6971"

# --- Data Processing Functions ---

def process_crop_data(filepath):
    """
    Cleans and prepares the crop production data from the raw CSV.
    """
    try:
        df = pd.read_csv(filepath, low_memory=False)
    except FileNotFoundError:
        print(f"Error: '{filepath}' not found.")
        return None
        
    print(f"\nProcessing {len(df)} raw crop records from '{filepath}'...")
    
    # 1. Rename Columns
    df.rename(columns={
        "state_name": "state",
        "district_name": "district",
        "crop_year": "year",
        "season": "season",
        "crop": "crop",
        "area_": "area_hectares",
        "production_": "production_tonnes"
    }, inplace=True)
    
    # 2. Clean String Data (robustness)
    str_cols = ['state', 'district', 'crop', 'season']
    for col in str_cols:
        df[col] = df[col].astype(str).str.strip()
    
    # 3. Handle Bad Numeric Data (robustness)
    num_cols = ['area_hectares', 'production_tonnes']
    for col in num_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # 4. Handle Missing Data
    # We drop rows where production is missing, as they are not useful.
    original_count = len(df)
    df.dropna(subset=['production_tonnes'], inplace=True)
    dropped_count = original_count - len(df)
    if dropped_count > 0:
        print(f"  Dropped {dropped_count} rows due to missing production data.")
    
    # 5. Add Traceability
    df['source_name'] = "District-wise, season-wise crop production statistics"
    df['source_url'] = CROP_API_URL
    
    # Select only the columns we need
    final_cols = ['state', 'district', 'year', 'season', 'crop', 'area_hectares', 'production_tonnes', 'source_name', 'source_url']
    df_clean = df[final_cols].copy()
    
    print(f"Crop data processing complete. {len(df_clean)} clean records.")
    return df_clean

def process_rainfall_data(filepath):
    """
    Cleans, aggregates daily rainfall to annual, and prepares data.
    """
    try:
        df = pd.read_csv(filepath, low_memory=False)
    except FileNotFoundError:
        print(f"Error: '{filepath}' not found.")
        return None

    print(f"\nProcessing {len(df)} raw daily rainfall records from '{filepath}'...")
    
    # 1. Rename Columns
    df.rename(columns={
        "State": "state",
        "District": "district",
        "Year": "year",
        "Avg_rainfall": "rainfall_mm"
    }, inplace=True)
    
    # 2. Clean String Data
    str_cols = ['state', 'district']
    for col in str_cols:
        df[col] = df[col].astype(str).str.strip()

    # 3. Handle Bad Numeric Data (Erroneous Values)
    # This 3-step process is very robust.
    # 3a. Explicitly replace known non-numeric strings
    df['rainfall_mm'] = df['rainfall_mm'].replace('NR', 0)
    # 3b. Coerce all values to numeric, turning others (e.g., 'NA') into NaN
    df['rainfall_mm'] = pd.to_numeric(df['rainfall_mm'], errors='coerce')
    # 3c. Fill any missing values (NaN) with 0
    df['rainfall_mm'] = df['rainfall_mm'].fillna(0)
    
    # 4. The Core Transformation (Aggregation)
    print("  Aggregating daily rainfall to annual... This may take a moment.")
    annual_rainfall = df.groupby(['state', 'district', 'year'])['rainfall_mm'].sum().reset_index()
    # Rename the aggregated column
    annual_rainfall.rename(columns={'rainfall_mm': 'annual_rainfall_mm'}, inplace=True)
    
    # 5. Add Traceability
    annual_rainfall['source_name'] = "Daily District-wise Rainfall Data (Aggregated to Annual)"
    annual_rainfall['source_url'] = RAIN_API_URL
    
    print(f"Rainfall data processing complete. {len(annual_rainfall)} clean annual records.")
    return annual_rainfall

# --- Main Execution ---

def main():
    # Process both datasets
    df_crop_clean = process_crop_data(CROP_FILE)
    df_rain_clean = process_rainfall_data(RAIN_FILE)
    
    # Check if we have data to load
    if (df_crop_clean is not None) and (df_rain_clean is not None):
        try:
            # Connect to (and create) the SQLite database
            if os.path.exists(DB_FILE):
                os.remove(DB_FILE) # Remove old DB file to ensure freshness
                print(f"\nRemoved old database '{DB_FILE}'.")
                
            conn = sqlite3.connect(DB_FILE)
            print(f"Saving clean data to new database '{DB_FILE}'...")
            
            # Save crop data
            df_crop_clean.to_sql("agriculture_production", conn, if_exists="replace", index=False)
            print("  Successfully saved 'agriculture_production' table.")
            
            # Save rainfall data
            df_rain_clean.to_sql("climate_rainfall", conn, if_exists="replace", index=False)
            print("  Successfully saved 'climate_rainfall' table.")
            
            conn.close()
            print("\n--- DATABASE BUILD COMPLETE ---")
            print(f"The file '{DB_FILE}' is now ready for Phase 2.")
            
        except Exception as e:
            print(f"An error occurred while saving to database: {e}")
    else:
        print("\nDatabase build failed. One or both raw CSV files were not processed.")

if __name__ == "__main__":
    main()