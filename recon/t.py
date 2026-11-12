from curl_cffi import requests
S = requests.Session(impersonate="chrome")
U = "https://gis.toledo.oh.gov/arcgis/rest/services/Public/CityWorks_ServiceRequest_2022/MapServer/1/query"
tests = {
 "date": "INIT_DATE >= DATE '2026-05-16'",
 "ts": "INIT_DATE >= TIMESTAMP '2026-05-16 00:00:00'",
 "like": "DESCRIPTION LIKE 'Structure%'",
 "eq_paren": "DESCRIPTION = 'Structure Concern (Property Maintenance, Vehicles)'",
 "eq_plain": "DESCRIPTION = 'High Grass Concern'",
 "in2": "DESCRIPTION IN ('High Grass Concern','Drug Activity or Drug House Concern')",
 "drug": "DESCRIPTION LIKE 'Drug%'",
}
for k, w in tests.items():
    for extra in ({}, {"resultOffset": 0, "resultRecordCount": 5, "orderByFields": "REQUEST_ID"}):
        r = S.get(U, params={"where": w, "outFields": "REQUEST_ID", "returnGeometry": "false", "f": "json", **extra}, timeout=40)
        print("@@t@@", k, bool(extra), r.status_code, r.text[:90].replace("\n", " "))
