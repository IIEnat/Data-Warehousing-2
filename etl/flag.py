"""
flag.py

Standalone data quality scanner for the raw aviation dataset.

Reads raw.csv and runs a series of checks designed to surface every issue we
identified during ETL development. Each check prints a header followed by
either a clean result or the offending rows. Nothing is modified; this script
is read-only and exists to document the data quality assessment process.

Checks performed:
  1. Null / missing values per column
  2. Leading or trailing whitespace in any string column
  3. Case inconsistencies (same value in different casing, e.g. BRISTOL vs Bristol)
  4. Airlines listed under multiple countries
  5. Empty or unusually-delimited plane fields
  6. Self-loop routes (departure airport == arrival airport)
  7. Airport names appearing under multiple (city, country) combinations
     -- distinguishes legitimate same-name collisions from data errors
  8. Duplicate (airline, dep_airport, arr_airport) rows requiring aircraft union
  9. Semicolon-delimited plane field (structural ETL concern, not a data error)

Run with:
    python flag.py
"""

import pandas as pd

df = pd.read_csv("raw.csv")
df.columns = [
    "airline_name", "airline_country",
    "dep_airport", "dep_city", "dep_country",
    "arr_airport", "arr_city", "arr_country",
    "planes"
]

print(f"Loaded raw.csv with {len(df)} rows and {len(df.columns)} columns.\n")


def header(n, title):
    print("=" * 70)
    print(f"CHECK {n}: {title}")
    print("=" * 70)


# --- 1. Nulls ---
header(1, "Null / missing values per column")
nulls = df.isnull().sum()
total_nulls = nulls.sum()
if total_nulls == 0:
    print("  OK: no nulls in any column.")
else:
    print(nulls[nulls > 0].to_string())
print()

# --- 2. Whitespace ---
header(2, "Leading or trailing whitespace")
ws_found = False
for col in df.columns:
    if df[col].dtype == "object":
        has_ws = (df[col].astype(str).str.strip() != df[col].astype(str)).sum()
        if has_ws > 0:
            print(f"  {col}: {has_ws} row(s) with leading/trailing whitespace")
            ws_found = True
if not ws_found:
    print("  OK: no whitespace issues.")
print()

# --- 3. Case inconsistencies ---
header(3, "Case inconsistencies (same value, different casing)")
case_found = False
for col in ["airline_name", "airline_country", "dep_airport", "arr_airport",
            "dep_city", "arr_city", "dep_country", "arr_country"]:
    vals = df[col].dropna().unique()
    lower_map = {}
    for v in vals:
        key = v.lower().strip()
        lower_map.setdefault(key, set()).add(v)
    dupes = {k: v for k, v in lower_map.items() if len(v) > 1}
    if dupes:
        case_found = True
        print(f"  {col}: {len(dupes)} group(s) with inconsistent casing")
        for k, v in dupes.items():
            print(f"    {sorted(v)}")
if not case_found:
    print("  OK: all string values have consistent casing.")
print()

# --- 4. Airlines under multiple countries ---
header(4, "Airlines listed under multiple countries")
airline_countries = df.groupby("airline_name")["airline_country"].nunique()
multi = airline_countries[airline_countries > 1]
if len(multi) == 0:
    print("  OK: every airline has a single country.")
else:
    print(f"  {len(multi)} airline(s) listed under more than one country:")
    for nm in multi.index:
        cs = df[df["airline_name"] == nm]["airline_country"].value_counts()
        print(f"    {nm}: {dict(cs)}")
print()

# --- 5. Plane field issues ---
header(5, "Empty or unusually-delimited plane fields")
empty_planes = df["planes"].isnull().sum() + (df["planes"].astype(str).str.strip() == "").sum()
if empty_planes == 0:
    print("  OK: no empty plane fields.")
else:
    print(f"  {empty_planes} row(s) with empty plane field.")
# Aircraft names legitimately contain '/' (e.g. BN-2A/B Islander), but ',' or '|'
# would suggest an alternative delimiter mistakenly used in place of ';'.
unusual_delim = df["planes"].astype(str).apply(
    lambda x: ("," in x) or ("|" in x)).sum()
if unusual_delim == 0:
    print("  OK: no unusual delimiters (comma or pipe) in plane field.")
else:
    print(f"  {unusual_delim} row(s) contain ',' or '|' in plane field.")
print()

# --- 6. Self-loops ---
header(6, "Self-loop routes (dep_airport == arr_airport)")
loops = df[df["dep_airport"] == df["arr_airport"]]
if len(loops) == 0:
    print("  OK: no self-loops.")
else:
    print(f"  {len(loops)} self-loop row(s):")
    print(loops[["airline_name", "dep_airport", "dep_city", "dep_country"]].to_string(index=False))
print()

# --- 7. Airport name appearing under multiple (city, country) ---
header(7, "Airports under multiple (city, country) combinations")
dep = df[["dep_airport", "dep_city", "dep_country"]].rename(
    columns={"dep_airport": "name", "dep_city": "city", "dep_country": "country"})
arr = df[["arr_airport", "arr_city", "arr_country"]].rename(
    columns={"arr_airport": "name", "arr_city": "city", "arr_country": "country"})
all_ap = pd.concat([dep, arr], ignore_index=True)

triplet_counts = all_ap.groupby(["name", "city", "country"]).size().reset_index(name="occurrences")
multi_triplet = triplet_counts.groupby("name").size().reset_index(name="n_variants")
multi_triplet = multi_triplet[multi_triplet["n_variants"] > 1]

if len(multi_triplet) == 0:
    print("  OK: every airport name maps to a single (city, country).")
else:
    print(f"  {len(multi_triplet)} airport name(s) appear under multiple (city, country) combinations.")
    print("  These fall into two real-world categories that cannot be distinguished")
    print("  programmatically and require manual review:")
    print("    (a) DATA ERRORS: same airport tagged with the wrong country in some rows")
    print("        (e.g. London Heathrow listed as both UK and Canada)")
    print("    (b) LEGITIMATE COLLISIONS: genuinely different airports sharing a name")
    print("        (e.g. Albany Airport exists in both Albany, AU and Albany, US)")
    print()
    print("  Full list for manual review:")
    for nm in multi_triplet["name"]:
        sub = triplet_counts[triplet_counts["name"] == nm].sort_values("occurrences", ascending=False)
        print(f"    {nm}")
        for _, s in sub.iterrows():
            print(f"      {s['city']}, {s['country']}: {s['occurrences']} occurrence(s)")
print()

# --- 8. Duplicate (airline, dep, arr) rows ---
header(8, "Duplicate (airline, dep_airport, arr_airport) rows")
key_cols = ["airline_name", "dep_airport", "arr_airport"]
group_sizes = df.groupby(key_cols).size().reset_index(name="n")
dupes = group_sizes[group_sizes["n"] > 1]
if len(dupes) == 0:
    print("  OK: no duplicate (airline, dep, arr) keys.")
else:
    total_dupe_rows = (dupes["n"] - 1).sum()
    print(f"  {len(dupes)} key(s) appear more than once.")
    print(f"  Total rows that will be collapsed during ETL: {total_dupe_rows}")
    print(dupes.to_string(index=False))
print()

# --- 9. Multi-valued plane field ---
header(9, "Semicolon-delimited plane field")
plane_counts = df["planes"].astype(str).apply(lambda x: len([p for p in x.split(";") if p.strip()]))
multi_plane = (plane_counts > 1).sum()
max_planes = plane_counts.max()
total_pairs = plane_counts.sum()
print(f"  Rows with >1 aircraft type: {multi_plane} of {len(df)}")
print(f"  Max aircraft per row: {max_planes}")
print(f"  Total (row, aircraft) pairs after expansion: {total_pairs}")
print("  NOTE: this is a structural format issue, not a data error. The")
print("  field is serialized as 'aircraft1;aircraft2;...' and must be split")
print("  into individual (Route)-[:USES]->(Aircraft) relationships in ETL.")
print()

print("=" * 70)
print("Scan complete.")
print("=" * 70)