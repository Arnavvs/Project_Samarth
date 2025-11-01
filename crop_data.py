import os
import requests
import pandas as pd
import time
from ssl import SSLError # Import the error so we can catch it

# --- Configuration ---
API_KEY = "579b464db66ec23bdd000001a2498286a9ab43a0426909464c78de93" 

BASE_URL = "https://api.data.gov.in/resource/"
CROP_RESOURCE_ID = "35be999b-0208-4354-b557-f6ca9a5355de"
RAIN_RESOURCE_ID = "6c05cd1b-ed59-40c2-bc31-e314f39c6971"

CROP_OUTPUT_FILE = "raw_crop_data.csv"
RAIN_OUTPUT_FILE = "raw_rainfall_data.csv"

# --- Helper Function to Fetch All Data (Handles Pagination & Retries) ---

def fetch_all_data(resource_id):
    """
    Fetches all records from a data.gov.in resource by handling
    pagination and retrying on network errors.
    """
    all_records = []
    limit = 1000  # Fetch in chunks of 1000
    offset = 0
    max_retries = 5 # NEW: Max retries per chunk
    
    print(f"Starting to fetch data for resource: {resource_id}")
    
    while True:
        params = {
            "api-key": API_KEY,
            "format": "json",
            "limit": limit,
            "offset": offset
        }
        
        # NEW: Retry loop
        current_retry = 0
        for current_retry in range(max_retries):
            try:
                response = requests.get(f"{BASE_URL}{resource_id}", params=params, timeout=30) # Add 30s timeout
                response.raise_for_status()  # Raise an error for bad responses
                data = response.json()
                
                # If successful, break the retry loop
                break 
                
            except (requests.exceptions.RequestException, SSLError) as e:
                print(f"  [Attempt {current_retry + 1}/{max_retries}] Network error: {e}. Retrying in 3 seconds...")
                time.sleep(3)
                
            except Exception as e:
                print(f"An unexpected error occurred: {e}")
                print(response.text) # Print response text for debugging
                return pd.DataFrame(all_records) # Return what we have so far
        
        else: # This 'else' block runs if the 'for' loop completes without 'break'
            print(f"Failed to fetch chunk at offset {offset} after {max_retries} retries. Stopping.")
            break # Stop fetching from this resource

        # We have the 'data'
        records = data.get("records", [])
        if not records:
            print("No more records found. Fetch complete.")
            break
            
        all_records.extend(records)
        print(f"Fetched {len(records)} records. Total: {len(all_records)}")
        
        if len(records) < limit:
            print("Reached the end of the data.")
            break
            
        offset += limit
            
    return pd.DataFrame(all_records)

# --- Main Execution ---

def main():
    # Fetch Crop Data
    df_crop = fetch_all_data(CROP_RESOURCE_ID)
    if not df_crop.empty:
        df_crop.to_csv(CROP_OUTPUT_FILE, index=False)
        print(f"\nSuccessfully saved {len(df_crop)} raw crop records to '{CROP_OUTPUT_FILE}'")
    else:
        print("\nFailed to fetch crop data or data was empty.")

    # Fetch Rainfall Data
    df_rain = fetch_all_data(RAIN_RESOURCE_ID)
    # --- THIS IS THE FIX ---
    if not df_rain.empty: 
        df_rain.to_csv(RAIN_OUTPUT_FILE, index=False)
        print(f"\nSuccessfully saved {len(df_rain)} raw rainfall records to '{RAIN_OUTPUT_FILE}'")
    else:
        print("\nFailed to fetch rainfall data or data was empty.")
        
    print("\nRaw data fetching complete.")

if __name__ == "__main__":
    main()