# CBS Renewable Energy Data Fetcher

## Role & Objective

This project implements a Python script to retrieve historical renewable energy data from the **CBS (Statistics Netherlands) Open Data Portal** using the official API (`cbsodata`) or a robust OData fallback.

The goal is to fetch, process, and verify key renewable energy metrics for analysis.

## Target Data

The script retrieves **yearly** historical data (from 1990 to the most recent available year) for:

1. **Installed Capacity:** `Electrical capacity end of year` (Unit: MW).
2. **Electricity Production:** `Net production of electricity` (Unit: mln kWh).

### Energy Sources

- **Solar Power** (Solar photovoltaic)
- **Onshore Wind** (Wind energy: onshore)
- **Offshore Wind** (Wind energy: offshore)

## Implementation Details

The `fetch_cbs_data.py` script performs the following steps:

1. **Data Fetching**:
    - Attempts to use the `cbsodata` library (Dataset `82610ENG`).
    - **Robust Fallback**: Automatically switches to a **manual OData fetch** using `requests` if the library fails due to connection/SSL issues.
    - **Protocol Handling**: Uses `HTTP` and `UntypedDataSet` to bypass strict HTTPS configuration on the CBS server.
    - **Pagination**: Handles OData pagination (`@odata.nextLink`) to ensure all data is retrieved.

2. **Data Processing**:
    - **Column Mapping**: Dynamically identifies the correct columns for "Net Production" and "Installed Capacity".
    - **Source Mapping**: Maps CBS codes (e.g., `E006590`) and labels to readable names: "Solar", "Onshore Wind", "Offshore Wind".
    - **Cleaning**: Extracts integer Years from the Period column and converts numeric data types.

3. **Excel Export**:
    - Generates `CBS_Renewable_Data.xlsx` with three separate sheets (Solar, Onshore Wind, Offshore Wind).

4. **Verification**:
    - Compares the fetched data for **2022, 2023, and 2024** against reference values.

## Usage

### Prerequisites

- Python 3.x
- `pandas`
- `cbsodata`
- `openpyxl`
- `requests`

### Running the Script

```bash
python3 fetch_cbs_data.py
```

## Verification Results

The script successfully verifies all data points against the reference.

### Console Output Snapshot

```text
Fetching data from CBS...
cbsodata library failed (...). Switching to manual fetch...
Attempting manual fetch from http://opendata.cbs.nl/ODataApi/odata/82610ENG/UntypedDataSet...
Fetching http://opendata.cbs.nl/ODataApi/odata/82610ENG/UntypedDataSet...
Data fetched. ...
...
--- Verification Table ---
Year   Source          Metric             Fetched  Reference       Diff Status    
-------------------------------------------------------------------------------------
...
2023   Onshore Wind    Capacity              6692       6692          0 OK        
2023   Onshore Wind    Production           17482      17482          0 OK        
...
2024   Solar           Production           21822      21822          0 OK        

Successfully generated CBS_Renewable_Data.xlsx
```

## Output Files

- `fetch_cbs_data.py`: The main script.
- `CBS_Renewable_Data.xlsx`: The output data file.

## Note

This project was fully implemented by **Gemini 3 Pro** without user intervention, other than a request to perform a full comparison with all data in the `CBS_Ref.pdf` file.
