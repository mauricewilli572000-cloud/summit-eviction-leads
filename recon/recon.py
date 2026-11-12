import json
from curl_cffi import requests
S = requests.Session(impersonate="chrome")
def out(t, o): print(f"@@{t}@@ " + json.dumps(o, default=str)[:6000], flush=True)
def get(u, **p):
    p.setdefault("f", "json")
    try: return S.get(u, params=p, timeout=60).json()
    except Exception as e: return {"error": str(e)[:200]}
L = "https://lcaudgis.co.lucas.oh.us/gisaudserver/rest/services/"
j = get(L + "Hosted"); out("lcaud", [s["name"][7:] for s in j.get("services", [])][70:])
out("lcaud_root", get(L))
for name in ["AREIS_GENERAL_COLLECTIONS", "Forfeited_Land_Sale_2026", "City_of_Toledo_Vacant_Parcels__CAMA", "Land_Bank"]:
    base = L + f"Hosted/{name}/FeatureServer"
    meta = get(base)
    for lyr in [l["id"] for l in meta.get("layers", [])][:2]:
        m = get(f"{base}/{lyr}")
        c = get(f"{base}/{lyr}/query", where="1=1", returnCountOnly="true")
        s = get(f"{base}/{lyr}/query", where="1=1", outFields="*", resultRecordCount=2, returnGeometry="false")
        out("layer", {"svc": name, "lyr": lyr, "name": m.get("name"), "edited": m.get("editingInfo"), "count": c.get("count"), "fields": [f["name"] for f in m.get("fields", [])], "sample": [f["attributes"] for f in s.get("features", [])]})
T = "https://gis.toledo.oh.gov/arcgis/rest/services/"
out("toledo_root", get(T)); out("toledo_public", [s["name"] for s in get(T + "Public").get("services", [])])
out("toledo_nh", [(l["id"], l["name"]) for l in get(T + "Public/NeighborhoodsAndHousingMapServiceHub/MapServer").get("layers", [])])
out("toledo_org", [s["name"] for s in get("https://services.arcgis.com/2snQ88YUjP9CNEbe/arcgis/rest/services").get("services", [])])
