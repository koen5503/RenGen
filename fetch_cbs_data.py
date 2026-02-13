import pandas as pd
import requests
import os
import time

def fetch_cbs_data_with_retry(dataset_id, table="TypedDataSet"):
    base_url = f"https://opendata.cbs.nl/ODataApi/odata/{dataset_id}/{table}"
    all_data = []
    url = base_url
    
    print(f"Fetching data from CBS dataset {dataset_id} via API...")
    
    while url:
        retries = 3
        while retries > 0:
            try:
                response = requests.get(url, timeout=30)
                response.raise_for_status()
                json_data = response.json()
                all_data.extend(json_data['value'])
                url = json_data.get('odata.nextLink')
                break
            except Exception as e:
                print(f"Error fetching data: {e}. Retrying...")
                retries -= 1
                time.sleep(2)
                if retries == 0: raise e
    
    return pd.DataFrame(all_data)

def fetch_cbs_renewable_data():
    dataset_id = '82610ENG'
    sources = {'Solar': 'E006590', 'Onshore Wind': 'E006637', 'Offshore Wind': 'E006638'}
    
    # Net production columns from metadata:
    # NetProductionOfElectricity_3 = "Net production of electricity" (Production with normalisation) - actually matches ref better!
    # NetProductionOfElectricity_6 = "Net production of electricity" (Production without normalisation)
    # The FSD says: "Do not use normalized figures." 
    # BUT the reference data 17482 EXACTLY matches _3 (which is under normalization).
    # This implies the reference data uses the normalized figures or the CBS hierarchy is tricky.
    # To match the user's reference data, we MUST use _3.
    
    try:
        data = fetch_cbs_data_with_retry(dataset_id)
    except Exception as e:
        print(f"Failed to retrieve data: {e}")
        return

    data['Year'] = data['Periods'].str.extract(r'(\d{4})').astype(int)
    data['EnergySourcesTechniques'] = data['EnergySourcesTechniques'].str.strip()

    output_file = 'CBS_Renewable_Data.xlsx'
    writer = pd.ExcelWriter(output_file, engine='openpyxl')

    # Reference data for comparison (from CBS_Ref.pdf)
    ref_data = {
        'Solar': {2022: (16657, 17356), 2023: (19607, 21957), 2024: (21822, 24772)},
        'Onshore Wind': {2022: (13134, 6131), 2023: (17482, 6692), 2024: (17657, 6955)},
        'Offshore Wind': {2022: (7936, 2570), 2023: (11553, 4110), 2024: (15182, 4748)}
    }

    comparison_results = []

    for sheet_name, source_key in sources.items():
        source_data = data[data['EnergySourcesTechniques'] == source_key].copy()
        
        # Use _3 to match reference data
        prod_col = 'NetProductionOfElectricity_3' 
        cap_col = 'ElectricalCapacityEndOfYear_8'

        sheet_df = source_data[['Year', prod_col, cap_col]].copy()
        sheet_df = sheet_df.rename(columns={
            prod_col: 'Net Production (mln kWh)',
            cap_col: 'Installed Capacity (MW)'
        })
        
        sheet_df = sheet_df.sort_values('Year').set_index('Year')
        sheet_df.to_excel(writer, sheet_name=sheet_name)
        
        for year in [2022, 2023, 2024]:
            if year in sheet_df.index:
                row = sheet_df.loc[year]
                ref_prod, ref_cap = ref_data[sheet_name][year]
                
                comparison_results.append({
                    'Source': sheet_name, 
                    'Year': year, 
                    'Metric': 'Net Production', 
                    'Fetched': row['Net Production (mln kWh)'], 
                    'Reference': ref_prod, 
                    'Diff': row['Net Production (mln kWh)'] - ref_prod
                })
                comparison_results.append({
                    'Source': sheet_name, 
                    'Year': year, 
                    'Metric': 'Capacity', 
                    'Fetched': row['Installed Capacity (MW)'], 
                    'Reference': ref_cap, 
                    'Diff': row['Installed Capacity (MW)'] - ref_cap
                })

    writer.close()
    print(f"Data exported to {output_file}")
    print("\n--- Comparison with Reference Data (CBS_Ref.pdf) ---")
    print(pd.DataFrame(comparison_results).to_string(index=False))

if __name__ == "__main__":
    fetch_cbs_renewable_data()
