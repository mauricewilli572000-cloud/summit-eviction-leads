from curl_cffi import requests
S = requests.Session(impersonate="chrome")
U = "https://gis.toledo.oh.gov/arcgis/rest/services/Public/CityWorks_ServiceRequest_2022/MapServer/1/query"
W = "DESCRIPTION LIKE 'Structure Concern%' AND INIT_DATE >= DATE '2026-05-16'"
F = "REQUEST_ID,DESCRIPTION,INIT_DATE,CLOSED_DATE,STATUS,RESOLUTION,LOCATION,PROBZIP"
for name, p in {
  "full": {"where": W, "outFields": F, "returnGeometry": "false", "resultOffset": 0, "resultRecordCount": 1000, "orderByFields": "REQUEST_ID"},
  "rc100": {"where": W, "outFields": F, "returnGeometry": "false", "resultOffset": 0, "resultRecordCount": 100, "orderByFields": "REQUEST_ID"},
  "noorder": {"where": W, "outFields": F, "returnGeometry": "false", "resultOffset": 0, "resultRecordCount": 1000},
  "star": {"where": W, "outFields": "*", "returnGeometry": "false"},
  "idonly": {"where": W, "outFields": "REQUEST_ID", "returnGeometry": "false", "resultOffset": 0, "resultRecordCount": 1000, "orderByFields": "REQUEST_ID"},
  "noresol": {"where": W, "outFields": "REQUEST_ID,DESCRIPTION,INIT_DATE,STATUS,LOCATION", "returnGeometry": "false", "resultOffset": 0, "resultRecordCount": 1000, "orderByFields": "REQUEST_ID"},
}.items():
    r = S.get(U, params={**p, "f": "json"}, timeout=60)
    print("@@t@@", name, r.status_code, len(r.text), r.text[:80].replace("\n", " "))
