import pandas as pd

df = pd.read_csv("cleaned.csv")

df.columns = [
    "airline_name", "airline_country",
    "dep_airport", "dep_city", "dep_country",
    "arr_airport", "arr_city", "arr_country",
    "planes"
]

# --- Deduplicate routes on (airline, dep, arr), union aircraft across duplicate rows ---
def union_planes(series):
    all_planes = set()
    for val in series:
        if pd.notna(val):
            for p in val.split(";"):
                p = p.strip()
                if p:
                    all_planes.add(p)
    return ";".join(sorted(all_planes))

routes = df.groupby(
    ["airline_name", "dep_airport", "arr_airport"],
    as_index=False
).agg(
    airline_country=("airline_country", "first"),
    dep_city=("dep_city", "first"),
    dep_country=("dep_country", "first"),
    arr_city=("arr_city", "first"),
    arr_country=("arr_country", "first"),
    planes=("planes", union_planes)
)

routes.insert(0, "route_id", range(1, len(routes) + 1))

# --- airlines.csv ---
airlines = routes[["airline_name", "airline_country"]].drop_duplicates().reset_index(drop=True)
airlines.to_csv("airlines.csv", index=False)
print(f"airlines.csv:  {len(airlines)} rows")

# --- airports.csv ---
dep = routes[["dep_airport", "dep_city", "dep_country"]].rename(
    columns={"dep_airport": "airport_name", "dep_city": "city", "dep_country": "country"})
arr = routes[["arr_airport", "arr_city", "arr_country"]].rename(
    columns={"arr_airport": "airport_name", "arr_city": "city", "arr_country": "country"})
airports = pd.concat([dep, arr]).drop_duplicates(subset=["airport_name", "city", "country"]).reset_index(drop=True)
airports.to_csv("airports.csv", index=False)
print(f"airports.csv:  {len(airports)} rows")

# --- aircraft.csv ---
all_planes = set()
for val in routes["planes"]:
    for p in val.split(";"):
        p = p.strip()
        if p:
            all_planes.add(p)
aircraft = pd.DataFrame(sorted(all_planes), columns=["aircraft_name"])
aircraft.to_csv("aircraft.csv", index=False)
print(f"aircraft.csv:  {len(aircraft)} rows")

# --- routes.csv ---
routes[["route_id", "dep_airport", "arr_airport", "airline_name"]].to_csv("routes.csv", index=False)
print(f"routes.csv:    {len(routes)} rows")

# --- rel_operates.csv: (airline)-[:OPERATES]->(route) ---
routes[["airline_name", "route_id"]].to_csv("rel_operates.csv", index=False)
print(f"rel_operates.csv: {len(routes)} rows")

# --- rel_departs.csv: (route)-[:DEPARTS_FROM]->(airport) ---
routes[["route_id", "dep_airport", "dep_city", "dep_country"]].to_csv("rel_departs.csv", index=False)
print(f"rel_departs.csv:  {len(routes)} rows")

# --- rel_arrives.csv: (route)-[:ARRIVES_AT]->(airport) ---
routes[["route_id", "arr_airport", "arr_city", "arr_country"]].to_csv("rel_arrives.csv", index=False)
print(f"rel_arrives.csv:  {len(routes)} rows")

# --- rel_uses.csv: (route)-[:USES]->(aircraft) ---
uses_rows = []
for _, row in routes.iterrows():
    for p in row["planes"].split(";"):
        p = p.strip()
        if p:
            uses_rows.append({"route_id": row["route_id"], "aircraft_name": p})
rel_uses = pd.DataFrame(uses_rows)
rel_uses.to_csv("rel_uses.csv", index=False)
print(f"rel_uses.csv:     {len(rel_uses)} rows")

print("\nDone. Upload all CSVs to GitHub and use raw URLs in Neo4j LOAD CSV.")
