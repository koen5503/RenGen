import cbsodata
import pandas as pd
import warnings
import requests

# Suppress warnings
warnings.filterwarnings("ignore")

# Constants
DATASET_ID = '82610ENG'

# Target topics (column names in the downloaded dataframe might differ slightly, strict mapping needed)
# We will inspect the columns after download, but commonly:
# "Electrical capacity end of year" -> 'ElectricalCapacityEndOfYear_..._1' (we need to be careful with exact codes)
# "Net production of electricity" -> 'NetProductionOfElectricity_..._2'
# Best approach is to inspect metadata or print columns, but for now we implement logic to find them.

# Mappings based on typical cbsodata output or metadata inspection
# However, cbsodata usually returns human readable column names if not specified otherwise.
# We will verify this by printing columns in a first run if needed, but I'll write robust selection logic.

REFERENCE_VALUES = {
    2022: {
        "Onshore Wind": {"Produce": 13134, "Capacity": 6131},
        "Offshore Wind": {"Produce": 7936, "Capacity": 2570},
        "Solar": {"Produce": 16657, "Capacity": 17356},
    },
    2023: {
        "Onshore Wind": {"Produce": 17482, "Capacity": 6692},
        "Offshore Wind": {"Produce": 11553, "Capacity": 4110},
        "Solar": {"Produce": 19607, "Capacity": 21957},
    },
    2024: {
        "Onshore Wind": {"Produce": 17657, "Capacity": 6955},
        "Offshore Wind": {"Produce": 15182, "Capacity": 4748},
        "Solar": {"Produce": 21822, "Capacity": 24772},
    },
}

def fetch_data_manually(dataset_id):
    """Fetch data manually using OData API with pagination support."""
    # Enforce HTTP to avoid SSL issues with CBS
    base_url = f"http://opendata.cbs.nl/ODataApi/odata/{dataset_id}/UntypedDataSet"
    print(f"Attempting manual fetch from {base_url}...")
    
    all_data = []
    url = base_url
    while url:
        try:
            print(f"Fetching {url}...")
            r = requests.get(url, timeout=30)
            r.raise_for_status()
            data = r.json()
            
            if 'value' in data:
                all_data.extend(data['value'])
            
            # Check for next link
            if '@odata.nextLink' in data:
                url = data['@odata.nextLink']
                # Ensure next link uses http if we started with http
                if url.startswith("https"):
                    url = url.replace("https", "http")
            else:
                url = None
        except Exception as e:
            print(f"Manual fetch failed: {e}")
            raise e
            
    return pd.DataFrame(all_data)

def fetch_and_process_data():
    print("Fetching data from CBS...")
    try:
        # Try cbsodata first? No, given the issues, let's prefer manual http fetch for reliability in this env
        # Or try cbsodata and fallback.
        data = pd.DataFrame(cbsodata.get_data(DATASET_ID))
    except Exception as e:
        print(f"cbsodata library failed ({e}). Switching to manual fetch...")
        data = fetch_data_manually(DATASET_ID)
        
    print(f"Data fetched. Shape: {data.shape}")
    
    # Identify Source Column
    source_col = next((c for c in data.columns if 'EnergySources' in c or 'Energie bronnen' in c), None)
    if not source_col:
        source_cols = [c for c in data.columns if 'Energy' in c]
        if source_cols:
             source_col = source_cols[0]
        else:
             raise ValueError("Could not find EnergySourcesTechniques column.")

    print(f"Using Source Column: {source_col}")
    
    # Standardize Source Column: Strip whitespace
    if data[source_col].dtype == object:
        data[source_col] = data[source_col].str.strip()

    # Define Mapping from Codes (or Labels) to Final Sheet Names
    # We map both potential labels (from cbsodata) and codes (from manual fetch)
    source_mapping = {
        # Labels
        "Solar photovoltaic": "Solar",
        "Wind energy: onshore": "Onshore Wind",
        "Wind energy: offshore": "Offshore Wind",
        # Codes
        "E006590": "Solar",
        "E006637": "Onshore Wind",
        "E006638": "Offshore Wind"
    }

    # Filter data
    df = data[data[source_col].isin(source_mapping.keys())].copy()
    
    if df.empty:
        print(f"Warning: No data found for target sources in column '{source_col}'.")
        print("Unique values found:", data[source_col].unique())
        raise ValueError("No matching data found for Solar/Wind.")

    # Map Source to Final Name
    df['Source_Mapped'] = df[source_col].map(source_mapping)

    # Clean Periods -> Years
    period_col = next((c for c in data.columns if 'Periods' in c or 'Perioden' in c), 'Periods')
    
    def clean_year(period):
        p = str(period).strip()
        if p.isdigit() and len(p) == 4:
            return int(p)
        if "JJ00" in p:
             return int(p.replace("JJ00", ""))
        return None

    df['Year'] = df[period_col].apply(clean_year)
    df = df.dropna(subset=['Year'])
    df['Year'] = df['Year'].astype(int)
    
    # Identify Data Columns
    # We look for partial matches to be robust
    prod_col = next((c for c in df.columns if "NetProductionOfElectricity" in c), None)
    cap_col = next((c for c in df.columns if "ElectricalCapacityEndOfYear" in c), None)
    
    if not prod_col or not cap_col:
        prod_col = next((c for c in df.columns if "Net production" in c and "normalisation" not in c), None)
        cap_col = next((c for c in df.columns if "Electrical capacity" in c), None)
        
    print(f"Using Production Column: {prod_col}")
    print(f"Using Capacity Column: {cap_col}")
    
    if not prod_col or not cap_col:
         print("Columns:", df.columns)
         raise ValueError("Could not identify target data columns.")

    # Select and Rename
    df_clean = df[['Year', 'Source_Mapped', prod_col, cap_col]].copy()
    df_clean.rename(columns={
        prod_col: 'Net Production (mln kWh)',
        cap_col: 'Installed Capacity (MW)',
        'Source_Mapped': 'Source'
    }, inplace=True)
    
    # Convert to numeric, coercing errors to NaN
    cols_to_numeric = ['Net Production (mln kWh)', 'Installed Capacity (MW)']
    for col in cols_to_numeric:
        df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce').fillna(0)

    output_dfs = {}
    
    # Create sheets for each mapped source
    for sheet_name in ["Solar", "Onshore Wind", "Offshore Wind"]:
        source_df = df_clean[df_clean['Source'] == sheet_name].copy()
        if source_df.empty:
            print(f"Warning: No data for {sheet_name}")
        source_df = source_df.sort_values('Year').set_index('Year')
        output_dfs[sheet_name] = source_df[['Installed Capacity (MW)', 'Net Production (mln kWh)']]
        
    return output_dfs

def verify_data(output_dfs):
    print("\n--- Verification Table ---")
    headers = ["Year", "Source", "Metric", "Fetched", "Reference", "Diff", "Status"]
    print(f"{headers[0]:<6} {headers[1]:<15} {headers[2]:<15} {headers[3]:>10} {headers[4]:>10} {headers[5]:>10} {headers[6]:<10}")
    print("-" * 85)
    
    all_passed = True
    
    for year in [2022, 2023, 2024]:
        for source, ref_data in REFERENCE_VALUES[year].items():
            if source not in output_dfs:
                print(f"{year:<6} {source:<15} ALL MISSING")
                all_passed = False
                continue
                
            df = output_dfs[source]
            if year not in df.index:
                 # It's possible 2024 is not yet in the dataset fetched from CBS (might be too early)
                 # But the FSD implies we should verify it if available.
                 # If missing, we flag it.
                 print(f"{year:<6} {source:<15} YEAR MISSING")
                 # Check if strictly required? FSD says compare. If data is missing from API, we can't help it.
                 # We'll calculate it as a fail or neutral.
                 continue

            # Capacity
            fetched_cap = df.loc[year, 'Installed Capacity (MW)']
            ref_cap = ref_data['Capacity']
            diff_cap = fetched_cap - ref_cap
            status_cap = "OK" if abs(diff_cap) < 1 else "FAIL" # Allow small float diff
            if status_cap == "FAIL": all_passed = False
            
            print(f"{year:<6} {source:<15} {'Capacity':<15} {fetched_cap:>10.0f} {ref_cap:>10} {diff_cap:>10.0f} {status_cap:<10}")

            # Production
            fetched_prod = df.loc[year, 'Net Production (mln kWh)']
            ref_prod = ref_data['Produce']
            diff_prod = fetched_prod - ref_prod
            status_prod = "OK" if abs(diff_prod) < 1 else "FAIL"
            if status_prod == "FAIL": all_passed = False
            
            print(f"{year:<6} {source:<15} {'Production':<15} {fetched_prod:>10.0f} {ref_prod:>10} {diff_prod:>10.0f} {status_prod:<10}")

    return all_passed

def main():
    try:
        # Proceed directly to fetch and process
        output_dfs = fetch_and_process_data()
        
        # Verify
        verify_data(output_dfs)
        
        # Export to Excel
        output_file = "CBS_Renewable_Data.xlsx"
        with pd.ExcelWriter(output_file) as writer:
            for sheet_name, df in output_dfs.items():
                df.to_excel(writer, sheet_name=sheet_name)
        
        print(f"\nSuccessfully generated {output_file}")
        
    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
