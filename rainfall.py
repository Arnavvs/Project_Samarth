import os
import requests
import pandas as pd
import time
from ssl import SSLError

# --- Configuration ---
# --- PASTE YOUR PERSONAL API KEY HERE ---
# --- DO NOT USE THE SAMPLE KEY ---
API_KEY = "579b464db66ec23bdd00000171c6ef9a5e35496551607d9840a03284" 

BASE_URL = "https://api.data.gov.in/resource/"
RAIN_RESOURCE_ID = "6c05cd1b-ed59-40c2-bc31-e314f39c6971"
RAIN_OUTPUT_FILE = "raw_rainfall_data.csv"

# Years to fetch
YEARS_TO_FETCH = list(range(2018, 2026)) # 2018, 2019, ..., 2025

# Hardcoded list of states from your screenshots
STATES_LIST = [
    "Uttar Pradesh", "Madhya Pradesh", "Karnataka", "Bihar", "Assam", "Odisha",
    "Tamil Nadu", "Maharashtra", "Rajasthan", "Chhattisgarh", "Andhra Pradesh",
    "West Bengal", "Gujarat", "Haryana", "Telangana", "Uttarakhand", "Kerala",
    "Nagaland", "Punjab", "Meghalaya", "Arunachal Pradesh", "Himachal Pradesh",
    "Jammu and Kashmir", "Tripura", "Manipur", "Jharkhand", "Mizoram",
    "Puducherry", "Sikkim", "Dadra and Nagar Haveli", "Goa",
    "Andaman and Nicobar Islands", "Chandigarh"
]

# --- Helper Function to Fetch Data (Handles Pagination & Retries) ---

def fetch_paginated_data(resource_id, filters=None):
    """
    Fetches all records for a *specific query* (with filters)
    by handling pagination and retrying on network errors.
    """
    all_records = []
    limit = 1000  # Fetch in chunks of 1000
    offset = 0
    max_retries = 5
    
    # Add base params
    params = {
        "api-key": API_KEY,
        "format": "json",
        "limit": limit
    }
    # Add any custom filters (like for the year)
    if filters:
        for key, value in filters.items():
            params[f"filters[{key}]"] = value

    while True:
        params["offset"] = offset
        
        # Retry loop
        current_retry = 0
        for current_retry in range(max_retries):
            try:
                response = requests.get(f"{BASE_URL}{resource_id}", params=params, timeout=30)
                response.raise_for_status()
                data = response.json()
                break 
                
            except requests.exceptions.RequestException as e:
                # 403 Forbidden is a fatal error, don't retry
                if e.response and e.response.status_code == 403:
                    print("    [FATAL ERROR] 403 Forbidden. Your API key is likely invalid or restricted.")
                    print("    Please create a new, personal API key on data.gov.in and try again.")
                    return "FATAL_ERROR" # Special signal to stop
                
                print(f"    [Attempt {current_retry + 1}/{max_retries}] Network error: {e}. Retrying in 3 seconds...")
                time.sleep(3)
        else:
            print(f"    Failed to fetch chunk at offset {offset} after {max_retries} retries. Stopping.")
            break 

        if data == "FATAL_ERROR":
            return "FATAL_ERROR"

        records = data.get("records", [])
        if not records:
            # This is the normal exit condition (no more records for this query)
            break
            
        all_records.extend(records)
        
        if len(records) < limit:
            # We got the last page for this query
            break
            
        offset += limit
            
    return all_records

# --- Main Execution ---

def main():
    if API_KEY == "YOUR_PERSONAL_API_KEY_GOES_HERE":
        print("--- ERROR ---")
        print("Please open fetch_rainfall_v4.py and paste your personal API key")
        print("into the 'API_KEY' variable at the top of the file.")
        return

    print(f"Found {len(STATES_LIST)} states to query.")
    print("\nFetching ALL rainfall data (Agency: NRSC VIC MODEL)... This will take a significant amount of time.")
    all_rainfall_records = []
    
    for year in YEARS_TO_FETCH:
        print(f"\n--- Processing Year: {year} ---")
        for state in STATES_LIST:
            print(f"  Fetching data for: {state}, {year}")
            
            # --- THIS IS THE UPDATE ---
            # These are the filters for our highly specific query
            query_filters = {
                "Year": str(year),
                "State": state,
                "Agency_name": "NRSC VIC MODEL" # <--- YOUR NEW FILTER
            }
            # --------------------------
            
            records_for_query = fetch_paginated_data(RAIN_RESOURCE_ID, filters=query_filters)
            
            # Check for the fatal error signal
            if records_for_query == "FATAL_ERROR":
                print("\nStopping script due to fatal API key error.")
                return

            if records_for_query:
                print(f"    ...Fetched {len(records_for_query)} records.")
                all_rainfall_records.extend(records_for_query)
            else:
                print(f"    ...No records found.")
            
            time.sleep(0.5) # Be nice to the API server, wait 0.5s between states

    # --- Step 3: Save Rainfall Data ---
    if all_rainfall_records:
        df_rain = pd.DataFrame(all_rainfall_records)
        df_rain.to_csv(RAIN_OUTPUT_FILE, index=False, mode='w') # 'w' to overwrite old file
        print(f"\n\n--- SUCCESS ---")
        print(f"Successfully saved a TOTAL of {len(df_rain)} raw rainfall records to '{RAIN_OUTPUT_FILE}'")
    else:
        print("\nFailed to fetch any rainfall data.")
        
    print("\nRaw rainfall data fetching complete.")

if __name__ == "__main__":
    main()