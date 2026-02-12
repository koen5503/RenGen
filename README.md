# CBS Renewable Energy Data Retrieval

Python script to retrieve historical renewable energy data from **CBS (Statistics Netherlands) Open Data Portal** and verify against reference specifications.

## Overview

This project fetches yearly historical data (from 1990 to present) for three renewable energy sources in the Netherlands:

- **Solar Power** (Solar photovoltaic)
- **Onshore Wind Energy**
- **Offshore Wind Energy**

The script retrieves two key metrics for each source:

1. **Installed Capacity**: Electrical capacity at end of year (MW)
2. **Electricity Production**: Net production of electricity without normalization (mln kWh)

## Requirements

### Dataset

- **Source**: CBS Open Data Portal
- **Dataset ID**: `82610ENG` ("Renewable electricity; production and capacity")
- **API**: Direct HTTP requests to CBS OData API
- **Time Range**: 1990 to latest available year

### Python Dependencies

```bash
pip install requests pandas openpyxl pdfplumber
```

### Output Specifications

- **Excel File**: `CBS_Renewable_Data.xlsx`
- **Structure**: Three separate sheets named:
  - "Solar"
  - "Onshore Wind"
  - "Offshore Wind"
- **Format**: Years as index, columns for capacity and production

### Verification

The script automatically compares fetched values against reference data in `CBS_Ref.pdf` for years 2022-2024 and prints a comparison table.

## Usage

Run the script from the project directory:

```bash
python3 fetch_cbs_renewable_data.py
```

### Output

The script will:

1. Fetch data from CBS Open Data Portal for all three energy sources
2. Generate `CBS_Renewable_Data.xlsx` with three sheets
3. Print a verification table comparing against reference values
4. Display match confirmation

Example output:

```
================================================================================
CBS Renewable Energy Data Retrieval
================================================================================

Fetching data for Solar...
  Retrieved 35 records
  Year range: 1990 - 2024

Fetching data for Onshore Wind...
  Retrieved 35 records
  Year range: 1990 - 2024

Fetching data for Offshore Wind...
  Retrieved 35 records
  Year range: 1990 - 2024

================================================================================
VERIFICATION: Comparing Fetched Data with CBS_Ref.pdf
================================================================================

Verification Summary: 18/18 values match (100.0%)
✓ All values verified successfully!
```

## Implementation Details

### Technical Approach

**API Access**:

- Uses direct HTTP requests to CBS OData API with retry logic
- Handles connection instability with automatic retries (3 attempts, 2-second delay)

**Energy Source Keys**:

- Solar Photovoltaic: `E006590`
- Onshore Wind: `E006637`
- Offshore Wind: `E006638`

**Data Columns**:

- Production: `NetProductionOfElectricity_3` (mln kWh, converted to billion kWh)
- Capacity: `ElectricalCapacityEndOfYear_8` (MW)

### Key Features

- **Robust Error Handling**: Retry logic for API connection issues
- **Data Validation**: Automatic verification against reference values
- **Clean Output**: Properly formatted Excel file with separate sheets per source
- **Complete History**: Data from 1990 to latest available year (currently 2024)

## Verification Results

All reference values verified with **100% accuracy**:

| Source | Year | Net Production (mln kWh) | Installed Capacity (MW) |
|--------|------|--------------------------|-------------------------|
| Solar | 2022 | 16.66 ✓ | 17,356 ✓ |
| Solar | 2023 | 19.61 ✓ | 21,957 ✓ |
| Solar | 2024 | 21.82 ✓ | 24,772 ✓ |
| Onshore Wind | 2022 | 13.13 ✓ | 6,131 ✓ |
| Onshore Wind | 2023 | 17.48 ✓ | 6,692 ✓ |
| Onshore Wind | 2024 | 17.66 ✓ | 6,955 ✓ |
| Offshore Wind | 2022 | 7.94 ✓ | 2,570 ✓ |
| Offshore Wind | 2023 | 11.55 ✓ | 4,110 ✓ |
| Offshore Wind | 2024 | 15.18 ✓ | 4,748 ✓ |

## Sample Data

### Solar Energy Growth (1990-2024)

| Year | Net Production (mln kWh) | Installed Capacity (MW) |
|------|--------------------------|-------------------------|
| 1990 | 0.000 | 1 |
| 2000 | 0.007 | 12 |
| 2010 | 0.044 | 85 |
| 2020 | 8.568 | 11,108 |
| 2021 | 11.304 | 14,823 |
| 2022 | 16.657 | 17,356 |
| 2023 | 19.607 | 21,957 |
| 2024 | 21.822 | 24,772 |

## Project Structure

```
RenGen2/
├── README.md                      # This file
├── FSD.txt                        # Functional specification
├── CBS_Ref.pdf                    # Reference values for verification
├── fetch_cbs_renewable_data.py    # Main script
└── CBS_Renewable_Data.xlsx        # Generated output (3 sheets)
```

## Data Source

**CBS (Statistics Netherlands)**  
Dataset: 82610ENG - "Renewable electricity; production and capacity"  
URL: <https://opendata.cbs.nl/>

Dataset contains definite figures until 2023 and revised provisional figures for 2024.

## Development

This project was fully developed by **Claude Sonnet 4.5 (Thinking)** without user intervention, other than the initial request to implement the functional specification and a follow-up request to compare against all data in the `CBS_Ref.pdf` file (not just 2023).

The autonomous development process included:

- API exploration and metadata analysis
- Identification of correct data columns and energy source keys
- Implementation of retry logic for connection stability
- PDF extraction for reference values
- Complete verification system with 100% accuracy

## License

Data source: CBS (Statistics Netherlands)  
Script: Generated for data retrieval and analysis purposes

## Notes

- Production values are "Net production of electricity" under "Production without normalisation"
- Capacity values are "Electrical capacity end of year"
- Years are extracted from CBS period format (YYYYJJ00)
- Data verified against official CBS reference documentation
