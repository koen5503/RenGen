#!/usr/bin/env python3
"""
CBS Renewable Energy Data Retrieval Script
Fetches historical renewable energy data from CBS Open Data Portal
Author: Generated script based on FSD requirements
Dataset: 82610ENG - Renewable electricity; production and capacity
"""

import requests
import pandas as pd
import time
from typing import Dict

# Configuration
DATASET_ID = "82610ENG"
BASE_URL = f"https://opendata.cbs.nl/ODataApi/odata/{DATASET_ID}"
OUTPUT_FILE = "CBS_Renewable_Data.xlsx"

# Energy source mappings (Key -> Sheet Name)
ENERGY_SOURCES = {
    "E006590 ": "Solar",           # Solar photovoltaic
    "E006637 ": "Onshore Wind",    # Onshore wind energy
    "E006638 ": "Offshore Wind"    # Offshore wind energy
}

# Reference values from CBS_Ref.pdf for verification
REFERENCE_DATA = {
    "Onshore Wind": {
        2022: {"Net Production (mln kWh)": 13.134, "Installed Capacity (MW)": 6131},
        2023: {"Net Production (mln kWh)": 17.482, "Installed Capacity (MW)": 6692},
        2024: {"Net Production (mln kWh)": 17.657, "Installed Capacity (MW)": 6955},
    },
    "Offshore Wind": {
        2022: {"Net Production (mln kWh)": 7.936, "Installed Capacity (MW)": 2570},
        2023: {"Net Production (mln kWh)": 11.553, "Installed Capacity (MW)": 4110},
        2024: {"Net Production (mln kWh)": 15.182, "Installed Capacity (MW)": 4748},
    },
    "Solar": {
        2022: {"Net Production (mln kWh)": 16.657, "Installed Capacity (MW)": 17356},
        2023: {"Net Production (mln kWh)": 19.607, "Installed Capacity (MW)": 21957},
        2024: {"Net Production (mln kWh)": 21.822, "Installed Capacity (MW)": 24772},
    }
}


def fetch_with_retry(url: str, max_retries: int = 3, delay: int = 2) -> dict:
    """
    Fetch URL with retry logic to handle connection issues
    
    Args:
        url: URL to fetch
        max_retries: Maximum number of retry attempts
        delay: Delay in seconds between retries
        
    Returns:
        JSON response as dictionary
    """
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"  Attempt {attempt + 1} failed: {e}")
                print(f"  Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                print(f"  All {max_retries} attempts failed!")
                raise
    return None


def fetch_energy_source_data(source_key: str, source_name: str) -> pd.DataFrame:
    """
    Fetch data for a specific energy source
    
    Args:
        source_key: CBS energy source key (e.g., 'E006590 ')
        source_name: Human-readable name (e.g., 'Solar')
        
    Returns:
        DataFrame with Year as index and columns for capacity and production
    """
    print(f"\nFetching data for {source_name}...")
    
    # Build URL with filter for specific energy source
    url = f"{BASE_URL}/TypedDataSet?$filter=EnergySourcesTechniques eq '{source_key}'"
    
    # Fetch data with retry logic
    data = fetch_with_retry(url)
    
    if not data or 'value' not in data:
        raise ValueError(f"No data returned for {source_name}")
    
    # Convert to DataFrame
    df = pd.DataFrame(data['value'])
    print(f"  Retrieved {len(df)} records")
    
    # Extract year from Periods column (format: "YYYYJJ00")
    df['Year'] = df['Periods'].str.extract(r'(\d{4})').astype(int)
    
    # Select and rename relevant columns
    # NetProductionOfElectricity_3 contains the actual net production values (in mln kWh as integers)
    # ElectricalCapacityEndOfYear_8 contains the capacity values (in MW)
    result_df = df[['Year', 'NetProductionOfElectricity_3', 'ElectricalCapacityEndOfYear_8']].copy()
    result_df.columns = ['Year', 'Net Production (mln kWh)', 'Installed Capacity (MW)']
    
    # Convert production from integer mln kWh to float billion kWh format (divide by 1000)
    result_df['Net Production (mln kWh)'] = result_df['Net Production (mln kWh)'] / 1000.0
    
    # Filter for years from 1990 onwards
    result_df = result_df[result_df['Year'] >= 1990]
    
    # Set Year as index and sort
    result_df = result_df.set_index('Year').sort_index()
    
    print(f"  Year range: {result_df.index.min()} - {result_df.index.max()}")
    
    return result_df


def fetch_all_renewable_data() -> Dict[str, pd.DataFrame]:
    """
    Fetch renewable energy data for all three sources
    
    Returns:
        Dictionary with sheet names as keys and DataFrames as values
    """
    print("="*80)
    print("CBS Renewable Energy Data Retrieval")
    print("="*80)
    
    results = {}
    
    for source_key, sheet_name in ENERGY_SOURCES.items():
        try:
            df = fetch_energy_source_data(source_key, sheet_name)
            results[sheet_name] = df
        except Exception as e:
            print(f"  ERROR: Failed to fetch {sheet_name}: {e}")
            continue
    
    return results


def export_to_excel(data_dict: Dict[str, pd.DataFrame], filename: str = OUTPUT_FILE):
    """
    Export data to Excel with separate sheets
    
    Args:
        data_dict: Dictionary with sheet names as keys and DataFrames as values
        filename: Output Excel filename
    """
    print(f"\n{'='*80}")
    print(f"Exporting data to {filename}...")
    print("="*80)
    
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        for sheet_name, df in data_dict.items():
            df.to_excel(writer, sheet_name=sheet_name)
            print(f"  ✓ Created sheet: {sheet_name}")
    
    print(f"\n✓ Excel file created successfully: {filename}")


def verify_against_reference(data_dict: Dict[str, pd.DataFrame]):
    """
    Verify fetched data against reference values from CBS_Ref.pdf
    
    Args:
        data_dict: Dictionary with sheet names as keys and DataFrames as values
    """
    print(f"\n{'='*80}")
    print("VERIFICATION: Comparing Fetched Data with CBS_Ref.pdf")
    print("="*80)
    
    comparison_rows = []
    
    for source_name in ["Solar", "Onshore Wind", "Offshore Wind"]:
        if source_name not in data_dict:
            print(f"\nWarning: {source_name} not found in fetched data")
            continue
        
        df = data_dict[source_name]
        
        # Get reference years for this source
        ref_years = REFERENCE_DATA.get(source_name, {})
        
        for year in sorted(ref_years.keys()):
            if year not in df.index:
                print(f"\nWarning: Year {year} not found in {source_name} data")
                continue
            
            # Get fetched values
            row_data = df.loc[year]
            fetched_production = row_data['Net Production (mln kWh)']
            fetched_capacity = row_data['Installed Capacity (MW)']
            
            # Get reference values
            ref_production = ref_years[year]['Net Production (mln kWh)']
            ref_capacity = ref_years[year]['Installed Capacity (MW)']
            
            # Compare production
            production_match = abs(fetched_production - ref_production) < 0.01
            comparison_rows.append({
                'Source': source_name,
                'Year': year,
                'Metric': 'Net Production (mln kWh)',
                'Fetched': f"{fetched_production:.2f}",
                'Reference': f"{ref_production:.3f}",
                'Match': '✓' if production_match else '✗'
            })
            
            # Compare capacity
            capacity_match = abs(fetched_capacity - ref_capacity) < 1
            comparison_rows.append({
                'Source': source_name,
                'Year': year,
                'Metric': 'Installed Capacity (MW)',
                'Fetched': f"{fetched_capacity:.0f}",
                'Reference': f"{ref_capacity}",
                'Match': '✓' if capacity_match else '✗'
            })
    
    # Create comparison DataFrame
    comparison_df = pd.DataFrame(comparison_rows)
    
    # Print formatted table
    print("\n" + comparison_df.to_string(index=False))
    print("\n" + "="*80)
    
    # Summary
    total = len(comparison_df)
    matches = len(comparison_df[comparison_df['Match'] == '✓'])
    print(f"\nVerification Summary: {matches}/{total} values match ({100*matches/total:.1f}%)")
    
    if matches == total:
        print("✓ All values verified successfully!")
    else:
        print("⚠ Some discrepancies found - please review the table above")
    
    print("="*80)


def main():
    """Main execution function"""
    
    # Step 1: Fetch all renewable energy data
    renewable_data = fetch_all_renewable_data()
    
    if not renewable_data:
        print("\nERROR: No data was fetched. Exiting.")
        return
    
    # Step 2: Export to Excel
    export_to_excel(renewable_data, OUTPUT_FILE)
    
    # Step 3: Verify against reference values
    verify_against_reference(renewable_data)
    
    print(f"\n{'='*80}")
    print("Script completed successfully!")
    print("="*80)


if __name__ == "__main__":
    main()
