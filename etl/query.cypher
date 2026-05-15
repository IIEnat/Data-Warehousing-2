// Queries are all present in the report too.

//3a
MATCH (a:Airline)
WHERE a.country = 'Australia'
RETURN DISTINCT a.name AS airline_name;

//3b
MATCH (r:Route)-[:DEPARTS_FROM]->(dep:Airport), (r)-[:ARRIVES_AT]->(arr:Airport)
RETURN
  SUM(CASE WHEN dep.country = arr.country THEN 1 ELSE 0 END) AS domestic,
  SUM(CASE WHEN dep.country <> arr.country THEN 1 ELSE 0 END) AS international;

//3c
MATCH (r:Route)-[:DEPARTS_FROM]->(dep:Airport), (r)-[:ARRIVES_AT]->(arr:Airport)
WITH
  CASE WHEN dep.name < arr.name THEN dep.name ELSE arr.name END AS airport1,
  CASE WHEN dep.name < arr.name THEN arr.name ELSE dep.name END AS airport2
WITH airport1, airport2, count(*) AS route_count
ORDER BY route_count DESC
LIMIT 1
RETURN airport1, airport2, route_count;

//3d
MATCH (r:Route)-[:DEPARTS_FROM]->(dep:Airport), (r)-[:ARRIVES_AT]->(arr:Airport), (r)-[:USES]->(ac:Aircraft)
WITH
  CASE WHEN dep.name < arr.name THEN dep.name ELSE arr.name END AS airport1,
  CASE WHEN dep.name < arr.name THEN arr.name ELSE dep.name END AS airport2,
  ac
WITH airport1, airport2, count(DISTINCT ac.name) AS distinct_aircraft
ORDER BY distinct_aircraft DESC
LIMIT 5
RETURN airport1, airport2, distinct_aircraft;

//3e
MATCH (beijing:Airport {name: 'Beijing Capital International Airport'}),
      (perth:Airport {name: 'Perth International Airport'})
MATCH path = (beijing)-[:DEPARTS_FROM|ARRIVES_AT*2..6]-(perth)
WITH [n IN nodes(path) WHERE n:Airport] AS airports
WITH DISTINCT airports
RETURN count(*) AS distinct_routes;

// 4a
MATCH (a:Airline)
WHERE a.country = 'Australia'
RETURN DISTINCT a.name AS airline_name;

// 4b
CALL apoc.meta.schema()
YIELD value
RETURN value;