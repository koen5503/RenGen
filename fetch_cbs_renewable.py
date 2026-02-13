#!/usr/bin/env python3
"""
Fetch historical renewable electricity data from CBS Open Data Portal
(dataset 82610ENG) and export to CBS_Renewable_Data.xlsx.

Sources: Solar PV, Onshore Wind, Offshore Wind
Topics:  Net production of electricity (mln kWh)
         Electrical capacity end of year (MW)

Uses direct HTTP requests with retry logic to work around CBS API
connection instability. Discovers source keys by matching 2023
reference values (avoids the very slow metadata endpoint).
"""

import re
import sys
import time
from pathlib import Path

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ── Configuration ────────────────────────────────────────────────────────────

DATASET_ID = "82610ENG"
BASE_URL = f"https://opendata.cbs.nl/ODataApi/odata/{DATASET_ID}"
OUTPUT_FILE = Path(__file__).parent / "CBS_Renewable_Data.xlsx"

# Topic column keys (from dataset metadata — verified via DataProperties)
COL_PRODUCTION = "NetProductionOfElectricity_3"      # mln kWh
COL_CAPACITY   = "ElectricalCapacityEndOfYear_8"     # MW

# Reference values from CBS_Ref.pdf (all available years)
# Used both for verification AND for discovering source keys (via 2023 row)
REFERENCE = {
    # sheet_name: {year: (production_mln_kwh, capacity_mw)}
    "Onshore Wind": {
        2022: (13134, 6131),
        2023: (17482, 6692),
        2024: (17657, 6955),
    },
    "Offshore Wind": {
        2022: (7936,  2570),
        2023: (11553, 4110),
        2024: (15182, 4748),
    },
    "Solar": {
        2022: (16657, 17356),
        2023: (19607, 21957),
        2024: (21822, 24772),
    },
}

# ── HTTP session with retry ──────────────────────────────────────────────────

def _session() -> requests.Session:
    s = requests.Session()
    retries = Retry(
        total=5,
        backoff_factor=2,
        status_forcelist=[500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    s.mount("https://", HTTPAdapter(max_retries=retries))
    s.headers["Accept"] = "application/json"
    return s


def _get_json(session: requests.Session, url: str) -> list[dict]:
    """Fetch all pages from a CBS OData endpoint."""
    results = []
    page = 0
    while url:
        for attempt in range(5):
            try:
                r = session.get(url, timeout=90)
                r.raise_for_status()
                data = r.json()
                break
            except (requests.ConnectionError, requests.Timeout) as e:
                wait = 2 ** (attempt + 1)
                print(f"    Connection error (attempt {attempt + 1}/5), "
                      f"retrying in {wait}s … ({e.__class__.__name__})")
                time.sleep(wait)
        else:
            raise RuntimeError(f"Failed to fetch {url} after 5 attempts")

        batch = data.get("value", [])
        results.extend(batch)
        next_link = data.get("odata.nextLink")
        if next_link:
            page += 1
            print(f"    Page {page} ({len(results)} rows so far) …")
        url = next_link
    return results


# ── Core logic ───────────────────────────────────────────────────────────────

def year_from_period(period: str) -> int | None:
    """Extract a 4-digit year from a CBS Periods string like '2023JJ00'."""
    m = re.match(r"(\d{4})JJ\d+", str(period).strip())
    return int(m.group(1)) if m else None


def fetch_data() -> pd.DataFrame:
    """Download the full dataset with pagination."""
    print("Fetching dataset (this may take a minute) …")
    session = _session()
    select = f"EnergySourcesTechniques,Periods,{COL_PRODUCTION},{COL_CAPACITY}"
    url = f"{BASE_URL}/TypedDataSet?$format=json&$select={select}"
    records = _get_json(session, url)
    df = pd.DataFrame(records)
    df["Year"] = df["Periods"].apply(year_from_period)
    df = df.dropna(subset=["Year"])
    df["Year"] = df["Year"].astype(int)
    print(f"  Retrieved {len(df)} yearly rows")
    return df


def discover_source_keys(df: pd.DataFrame) -> dict[str, str]:
    """
    Find the CBS EnergySourcesTechniques key for each source by matching
    the 2023 production and capacity values against reference data.
    """
    print("Discovering source keys via 2023 reference matching …")
    key_to_sheet: dict[str, str] = {}
    df2023 = df[df["Year"] == 2023]

    for sheet_name, year_data in REFERENCE.items():
        ref_prod, ref_cap = year_data[2023]
        match = df2023[
            (df2023[COL_PRODUCTION] == ref_prod) &
            (df2023[COL_CAPACITY] == ref_cap)
        ]
        if len(match) == 1:
            key = match.iloc[0]["EnergySourcesTechniques"]
            key_to_sheet[key] = sheet_name
            print(f"  {sheet_name}: key = {key!r}")
        elif len(match) == 0:
            print(f"  WARNING: No 2023 match for {sheet_name} "
                  f"(prod={ref_prod}, cap={ref_cap})")
        else:
            print(f"  WARNING: Multiple 2023 matches for {sheet_name}")

    if len(key_to_sheet) != 3:
        print(f"WARNING: expected 3 source matches, got {len(key_to_sheet)}")
    return key_to_sheet


def build_source_df(df: pd.DataFrame, source_key: str) -> pd.DataFrame:
    """Filter and pivot one energy source into a clean Year-indexed frame."""
    subset = df[df["EnergySourcesTechniques"] == source_key].copy()
    result = subset[["Year", COL_PRODUCTION, COL_CAPACITY]].copy()
    result = result.rename(columns={
        COL_PRODUCTION: "Net Production (mln kWh)",
        COL_CAPACITY:   "Installed Capacity (MW)",
    })
    result = result.set_index("Year").sort_index()
    return result


def verify(frames: dict[str, pd.DataFrame]) -> bool:
    """Print comparison table for all reference values. Returns True if all match."""
    header = (f"{'Source':<15} {'Year':>4}  {'Metric':<28} "
              f"{'Fetched':>10} {'Reference':>10}  {'Status'}")
    sep = "─" * len(header)
    print(f"\n{sep}")
    print("VERIFICATION against CBS_Ref.pdf")
    print(sep)
    print(header)
    print(sep)

    all_pass = True
    for sheet_name in ["Onshore Wind", "Offshore Wind", "Solar"]:
        year_data = REFERENCE[sheet_name]
        df = frames.get(sheet_name)

        for year in sorted(year_data):
            ref_prod, ref_cap = year_data[year]
            if df is None or year not in df.index:
                print(f"{sheet_name:<15} {year:>4}  "
                      f"{'— data missing':<28} {'':>10} {'':>10}  ✗ FAIL")
                all_pass = False
                continue

            row = df.loc[year]
            for metric, fetched_val, ref_val in [
                ("Net Production (mln kWh)",
                 row["Net Production (mln kWh)"], ref_prod),
                ("Installed Capacity (MW)",
                 row["Installed Capacity (MW)"], ref_cap),
            ]:
                fetched = int(fetched_val) if pd.notna(fetched_val) else None
                ok = fetched == ref_val
                status = "✓ PASS" if ok else "✗ FAIL"
                if not ok:
                    all_pass = False
                f_str = (f"{fetched:>10,}" if fetched is not None
                         else f"{'N/A':>10}")
                print(f"{sheet_name:<15} {year:>4}  {metric:<28} "
                      f"{f_str} {ref_val:>10,}  {status}")

    print(sep)
    print(f"Overall: {'ALL PASS ✓' if all_pass else 'SOME FAILURES ✗'}")
    print(sep)
    return all_pass


def main():
    # 1. Fetch full dataset
    df = fetch_data()

    # 2. Discover source keys by matching 2023 reference values
    key_to_sheet = discover_source_keys(df)

    # 3. Build per-source DataFrames
    frames: dict[str, pd.DataFrame] = {}
    for source_key, sheet_name in key_to_sheet.items():
        frames[sheet_name] = build_source_df(df, source_key)
        print(f"  {sheet_name}: {len(frames[sheet_name])} years "
              f"({frames[sheet_name].index.min()}–"
              f"{frames[sheet_name].index.max()})")

    # 4. Write Excel
    print(f"\nWriting {OUTPUT_FILE} …")
    with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as writer:
        for sheet_name in ["Solar", "Onshore Wind", "Offshore Wind"]:
            if sheet_name in frames:
                frames[sheet_name].to_excel(writer, sheet_name=sheet_name)
    print("  Done.")

    # 5. Verify against reference
    ok = verify(frames)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
