import json
from curl_cffi import requests
S = requests.Session(impersonate="chrome")
def out(t, o): print(f"@@{t}@@ " + json.dumps(o, default=str)[:4000], flush=True)
def get(u, **p):
    p.setdefault("f", "json")
    try: return S.get(u, params=p, timeout=120).json()
    except Exception as e: return {"error": str(e)[:200]}
L = "https://lcaudgis.co.lucas.oh.us/gisaudserver/rest/services/"
PA = L + "LandUse_Zoning/Parcels_Addresses_Generalized_Land_Use_Classification/MapServer"
out("pa_svc", [(l["id"], l["name"]) for l in get(PA).get("layers", [])])
for lid in (0, 1):
    m = get(f"{PA}/{lid}")
    out("pa", {"lid": lid, "name": m.get("name"), "fields": [f["name"] for f in m.get("fields") or []], "max": m.get("maxRecordCount"),
               "count": get(f"{PA}/{lid}/query", where="1=1", returnCountOnly="true").get("count")})
ids = ["0100044", "0100054", "1422791", "1112614"]
w = "parid IN (%s)" % ",".join(f"'{i}'" for i in ids)
out("pa_rows", [f["attributes"] for f in get(f"{PA}/1/query", where=w, outFields="*", returnGeometry="false").get("features", [])])
G = L + "Hosted/AREIS_GENERAL_COLLECTIONS/FeatureServer/0/query"
out("gc_rows", [f["attributes"] for f in get(G, where="parcel IN (%s)" % ",".join(f"'{i}'" for i in ids), outFields="parcel,owner,streetnumber,direction,address,adrsuf,city,state,zip,certyr,taxdue,landuse,class", returnGeometry="false").get("features", [])])
TP = "https://services3.arcgis.com/T8dczfwPixv79EgZ/arcgis/rest/services/Lucas_County_TaxParcels/FeatureServer/0/query"
out("tp_rows", [f["attributes"] for f in get(TP, where="PARCELID IN (%s)" % ",".join(f"'{i}'" for i in ids), outFields="PARCELID,SITEADDRESS,SITECITY,SITEZIP,OWNERNME1,USEDC,TOTALVALUE,RESYRBLT,COND_DESC", returnGeometry="false").get("features", [])])
# how many delinquent >=1000 & certyr<=2024, non-exempt
out("gc_n", get(G, where="taxdue>=1000 AND certyr>0 AND certyr<=2024 AND class<>'E'", returnCountOnly="true"))
out("gc_n_all", get(G, where="taxdue>=1000 AND class<>'E'", returnCountOnly="true"))
out("gc_max", get(L + "Hosted/AREIS_GENERAL_COLLECTIONS/FeatureServer/0").get("maxRecordCount"))
