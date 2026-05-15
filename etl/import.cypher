// ============================================================
// STEP 1: Constraints (run these first, one at a time)
// ============================================================

CREATE CONSTRAINT airline_name IF NOT EXISTS
FOR (a:Airline) REQUIRE a.name IS UNIQUE;

CREATE CONSTRAINT airport_name IF NOT EXISTS
FOR (a:Airport) REQUIRE a.name IS UNIQUE;

CREATE CONSTRAINT aircraft_name IF NOT EXISTS
FOR (a:Aircraft) REQUIRE a.name IS UNIQUE;

CREATE CONSTRAINT route_id IF NOT EXISTS
FOR (r:Route) REQUIRE r.route_id IS UNIQUE;

// ============================================================
// STEP 2: Import Airline nodes
// ============================================================

LOAD CSV WITH HEADERS
FROM 'https://raw.githubusercontent.com/IIEnat/Data-Warehousing-2/refs/heads/main/csv/airlines.csv' AS row
MERGE (a:Airline {name: row.airline_name})
SET a.country = row.airline_country;

// ============================================================
// STEP 3: Import Airport nodes
// ============================================================

LOAD CSV WITH HEADERS
FROM 'https://raw.githubusercontent.com/IIEnat/Data-Warehousing-2/refs/heads/main/csv/airports.csv' AS row
MERGE (a:Airport {name: row.airport_name})
SET a.city = row.city,
    a.country = row.country;

// ============================================================
// STEP 4: Import Aircraft nodes
// ============================================================

LOAD CSV WITH HEADERS
FROM 'https://raw.githubusercontent.com/IIEnat/Data-Warehousing-2/refs/heads/main/csv/aircraft.csv' AS row
MERGE (a:Aircraft {name: row.aircraft_name});

// ============================================================
// STEP 5: Import Route nodes
// ============================================================

LOAD CSV WITH HEADERS
FROM 'https://raw.githubusercontent.com/IIEnat/Data-Warehousing-2/refs/heads/main/csv/routes.csv' AS row
MERGE (r:Route {route_id: toInteger(row.route_id)})
SET r.dep_airport = row.dep_airport,
    r.arr_airport = row.arr_airport,
    r.airline_name = row.airline_name;

// ============================================================
// STEP 6: Import relationships
// Run each block separately — relationships after all nodes
// ============================================================

// (Airline)-[:OPERATES]->(Route)
LOAD CSV WITH HEADERS
FROM 'https://raw.githubusercontent.com/IIEnat/Data-Warehousing-2/refs/heads/main/csv/rel_operates.csv' AS row
MATCH (a:Airline {name: row.airline_name})
MATCH (r:Route {route_id: toInteger(row.route_id)})
MERGE (a)-[:OPERATES]->(r);

// (Route)-[:DEPARTS_FROM]->(Airport)
LOAD CSV WITH HEADERS
FROM 'https://raw.githubusercontent.com/IIEnat/Data-Warehousing-2/refs/heads/main/csv/rel_departs.csv' AS row
MATCH (r:Route {route_id: toInteger(row.route_id)})
MATCH (a:Airport {name: row.dep_airport})
MERGE (r)-[:DEPARTS_FROM]->(a);

// (Route)-[:ARRIVES_AT]->(Airport)
LOAD CSV WITH HEADERS
FROM 'https://raw.githubusercontent.com/IIEnat/Data-Warehousing-2/refs/heads/main/csv/rel_arrives.csv' AS row
MATCH (r:Route {route_id: toInteger(row.route_id)})
MATCH (a:Airport {name: row.arr_airport})
MERGE (r)-[:ARRIVES_AT]->(a);

// (Route)-[:USES]->(Aircraft)
LOAD CSV WITH HEADERS
FROM 'https://raw.githubusercontent.com/IIEnat/Data-Warehousing-2/refs/heads/main/csv/rel_uses.csv' AS row
MATCH (r:Route {route_id: toInteger(row.route_id)})
MATCH (a:Aircraft {name: row.aircraft_name})
MERGE (r)-[:USES]->(a);

// ============================================================
// STEP 7: Verify import
// ============================================================

MATCH (n) RETURN labels(n) AS label, count(n) AS count;