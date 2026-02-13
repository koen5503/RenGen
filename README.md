# CBS Renewable Electricity Data Fetcher

Retrieve historical renewable energy data from the **CBS (Statistics Netherlands) Open Data Portal** and export it to Excel.

## Target Data

Dataset **[82610ENG](https://opendata.cbs.nl/statline/#/CBS/en/dataset/82610ENG)** — *Renewable electricity; production and capacity*

**Metrics** (yearly, from 1990 to latest available):

| Metric | Unit | CBS Column |
|---|---|---|
| Electrical capacity end of year | MW | `ElectricalCapacityEndOfYear_8` |
| Net production of electricity | mln kWh | `NetProductionOfElectricity_3` |

> Production figures use **"Production without normalisation"** — not the normalised variant.

**Energy sources:**

| CBS Source | Excel Sheet |
|---|---|
| Solar photovoltaic | Solar |
| Wind energy: onshore | Onshore Wind |
| Wind energy: offshore | Offshore Wind |

## Output

`CBS_Renewable_Data.xlsx` — three sheets ("Solar", "Onshore Wind", "Offshore Wind"), each with `Year` as index and two columns: `Net Production (mln kWh)` and `Installed Capacity (MW)`.

## Requirements

```
pip install pandas requests openpyxl urllib3
```

## Usage

```bash
python fetch_cbs_renewable.py
```

## Design Notes

- **Direct HTTP with retry** — The `cbsodata` library lacks retry logic and the CBS API frequently drops connections. This script uses `requests` + `urllib3.Retry` with exponential backoff (5 attempts, 2 s base).
- **Data-driven key discovery** — Instead of querying the slow `EnergySourcesTechniques` metadata endpoint, source keys are identified by matching 2023 reference values against fetched data (`E006637` = Onshore Wind, `E006638` = Offshore Wind, `E006590` = Solar PV).
- **`$select` filtering** — Only the 4 needed columns are requested from the OData API, reducing payload size.

## Verification

The script prints a comparison table against reference values from `CBS_Ref.pdf` (2022–2024):

```
Source          Year  Metric                          Fetched  Reference  Status
Onshore Wind    2022  Net Production (mln kWh)         13,134     13,134  ✓ PASS
Onshore Wind    2022  Installed Capacity (MW)           6,131      6,131  ✓ PASS
Onshore Wind    2023  Net Production (mln kWh)         17,482     17,482  ✓ PASS
Onshore Wind    2023  Installed Capacity (MW)           6,692      6,692  ✓ PASS
Onshore Wind    2024  Net Production (mln kWh)         17,657     17,657  ✓ PASS
Onshore Wind    2024  Installed Capacity (MW)           6,955      6,955  ✓ PASS
Offshore Wind   2022  Net Production (mln kWh)          7,936      7,936  ✓ PASS
Offshore Wind   2022  Installed Capacity (MW)           2,570      2,570  ✓ PASS
Offshore Wind   2023  Net Production (mln kWh)         11,553     11,553  ✓ PASS
Offshore Wind   2023  Installed Capacity (MW)           4,110      4,110  ✓ PASS
Offshore Wind   2024  Net Production (mln kWh)         15,182     15,182  ✓ PASS
Offshore Wind   2024  Installed Capacity (MW)           4,748      4,748  ✓ PASS
Solar           2022  Net Production (mln kWh)         16,657     16,657  ✓ PASS
Solar           2022  Installed Capacity (MW)          17,356     17,356  ✓ PASS
Solar           2023  Net Production (mln kWh)         19,607     19,607  ✓ PASS
Solar           2023  Installed Capacity (MW)          21,957     21,957  ✓ PASS
Solar           2024  Net Production (mln kWh)         21,822     21,822  ✓ PASS
Solar           2024  Installed Capacity (MW)          24,772     24,772  ✓ PASS
Overall: ALL PASS ✓
```

All **18 values** (3 sources × 3 years × 2 metrics) match. Each sheet contains **35 years** of data (1990–2024).

---

> This repository was fully created by **Claude Opus 4.6 (Thinking)** without user intervention, other than requesting a full comparison against all data in `CBS_Ref.pdf`.
