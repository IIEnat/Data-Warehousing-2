"""
clean.py

Reads raw.csv and writes cleaned.csv after applying manual data quality fixes.

Issues corrected:

1. City casing: "BRISTOL" was the only all-caps city in the raw data (for
   Tri-Cities Regional TN/VA Airport). Normalized to "Bristol" for consistency
   with the rest of the dataset.

2. Country errors: 29 airport names were found in the raw data with the same
   (name, city) listed under multiple countries (e.g. London Heathrow appearing
   under both United Kingdom and Canada). These were verified manually against
   public sources and reassigned to the correct country.

3. Self-loop: one row had departure airport == arrival airport (South Pacific
   Island Airways flying Iskandar Airport, Pangkalan Bun, Indonesia, to itself).
   South Pacific Island Airways is a defunct American Samoan carrier with no
   plausible Indonesian operation, so this was treated as a data error and
   dropped.

Legitimate same-name airports in different cities (e.g. Albany Airport in both
Albany, Australia and Albany, United States) are NOT modified here. They are
correctly preserved as distinct nodes by the composite (name, city, country)
key applied in etl.py.

The only issue not fixed here is the multiple aircraft per row. That is fixed 
directly in etl.py 
"""

import pandas as pd

df = pd.read_csv("raw.csv")

df.columns = [
    "airline_name", "airline_country",
    "dep_airport", "dep_city", "dep_country",
    "arr_airport", "arr_city", "arr_country",
    "planes"
]

# --- 1. Normalize stray uppercase city ---
df.loc[df["dep_city"] == "BRISTOL", "dep_city"] = "Bristol"
df.loc[df["arr_city"] == "BRISTOL", "arr_city"] = "Bristol"

# --- 2. Country fixes ---
# (airport_name, city) -> canonical country
COUNTRY_FIXES = {
    ("Alberto Carnevalli Airport", "Merida"): "Venezuela",
    ("Arturo Michelena International Airport", "Valencia"): "Venezuela",
    ("Atlas Brasil Cantanhede Airport", "Boa Vista"): "Brazil",
    ("Birmingham-Shuttlesworth International Airport", "Birmingham"): "United States",
    ("Charles M. Schulz Sonoma County Airport", "Santa Rosa"): "United States",
    ("Cheddi Jagan International Airport", "Georgetown"): "Guyana",
    ("Cibao International Airport", "Santiago"): "Dominican Republic",
    ("Cochin International Airport", "Kochi"): "India",
    ("Comodoro Arturo Merino Benitez International Airport", "Santiago"): "Chile",
    ("El Alto International Airport", "La Paz"): "Bolivia",
    ("Eugene F. Correira International Airport", "Georgetown"): "Guyana",
    ("F. D. Roosevelt Airport", "Oranjestad"): "Netherlands",
    ("Florence Regional Airport", "Florence"): "United States",
    ("Futuna Airport", "Futuna Island"): "Wallis and Futuna",
    ("General Jose Antonio Anzoategui International Airport", "Barcelona"): "Venezuela",
    ("JAGS McCartney International Airport", "Cockburn Town"): "Turks and Caicos Islands",
    ("London City Airport", "London"): "United Kingdom",
    ("London Gatwick Airport", "London"): "United Kingdom",
    ("London Heathrow Airport", "London"): "United Kingdom",
    ("London Luton Airport", "London"): "United Kingdom",
    ("London Stansted Airport", "London"): "United Kingdom",
    ("Luis Munoz Marin International Airport", "San Juan"): "Puerto Rico",
    ("Mayor Buenaventura Vivas International Airport", "Santo Domingo"): "Venezuela",
    ("Norman Manley International Airport", "Kingston"): "Jamaica",
    ("Norman Y. Mineta San Jose International Airport", "San Jose"): "United States",
    ("Northwest Florida Beaches International Airport", "Panama City"): "United States",
    ("Presidente Joao Batista Figueiredo Airport", "Sinop"): "Brazil",
    ("St Petersburg Clearwater International Airport", "St. Petersburg"): "United States",
    ("Sydney Kingsford Smith International Airport", "Sydney"): "Australia",
    ("Tri-Cities Regional TN/VA Airport", "Bristol"): "United States",
}


def fix_country(name, city, country):
    return COUNTRY_FIXES.get((name, city), country)


df["dep_country"] = df.apply(
    lambda r: fix_country(r["dep_airport"], r["dep_city"], r["dep_country"]), axis=1)
df["arr_country"] = df.apply(
    lambda r: fix_country(r["arr_airport"], r["arr_city"], r["arr_country"]), axis=1)

# --- 3. Drop self-loops (data errors) ---
before = len(df)
df = df[df["dep_airport"] != df["arr_airport"]].reset_index(drop=True)
dropped = before - len(df)

# Write back with the same column order/names as raw.csv
df.columns = [
    "Airline Name", "Airline Country",
    "Departure Airport Name", "Departure Airport City", "Departure Airport Country/Region",
    "Arrival Airport Name", "Arrival Airport City", "Arrival Airport Country/Region",
    "Plane Name"
]
df.to_csv("cleaned.csv", index=False)
print(f"cleaned.csv: {len(df)} rows ({dropped} self-loop row(s) dropped)")
print(f"Applied {len(COUNTRY_FIXES)} country fixes.")