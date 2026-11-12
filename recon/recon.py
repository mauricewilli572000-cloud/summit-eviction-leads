import json
from curl_cffi import requests
S = requests.Session(impersonate="chrome")
def out(t, o): print(f"@@{t}@@ " + json.dumps(o, default=str)[:3500], flush=True)
def get(u, **p):
    p.setdefault("f", "json")
    try: return S.get(u, params=p, timeout=90).json()
    except Exception as e: return {"error": str(e)[:200]}
L = "https://lcaudgis.co.lucas.oh.us/gisaudserver/rest/services/Hosted/"
T = "https://gis.toledo.oh.gov/arcgis/rest/services/"
O = "https://services.arcgis.com/2snQ88YUjP9CNEbe/arcgis/rest/services/"
svcs = [L + "AREIS_GENERAL_COLLECTIONS/FeatureServer", L + "AREIS_GENERAL_COLLECTIONS/MapServer", L + "Vacant_Delinquent___100/FeatureServer",
        L + "Sheriff_Sale_Q3/FeatureServer", T + "Demolition_Map_MIL1/MapServer", T + "Grass_Mowing_Program/MapServer",
        T + "Public/CityWorks_ServiceRequest_2022/MapServer", T + "Public/Pro_Codes_Areis/MapServer", T + "Public/For_Sale_Data/MapServer",
        O + "DemoCandidates/FeatureServer", O + "Rental_Registry_SEPT_2025/FeatureServer", O + "Inspectors/FeatureServer", O + "CED/FeatureServer"]
for base in svcs:
    meta = get(base)
    if "error" in meta and not meta.get("layers"):
        out("svc", {"u": base, "err": meta.get("error")}); continue
    lyrs = meta.get("layers", []) + meta.get("tables", [])
    out("svc", {"u": base, "layers": [(l["id"], l["name"]) for l in lyrs]})
    for l in lyrs[:3]:
        m = get(f"{base}/{l['id']}")
        c = get(f"{base}/{l['id']}/query", where="1=1", returnCountOnly="true")
        s = get(f"{base}/{l['id']}/query", where="1=1", outFields="*", resultRecordCount=2, returnGeometry="false")
        out("layer", {"u": f"{base}/{l['id']}", "name": m.get("name"), "edited": (m.get("editingInfo") or {}).get("lastEditDate"), "count": c.get("count"), "fields": [f["name"] for f in m.get("fields") or []], "sample": [f["attributes"] for f in s.get("features", [])]})
