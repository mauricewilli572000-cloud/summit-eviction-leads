import json, collections
from curl_cffi import requests
S = requests.Session(impersonate="chrome")
def out(t, o): print(f"@@{t}@@ " + json.dumps(o, default=str)[:5000], flush=True)
def get(u, **p):
    p.setdefault("f", "json")
    try: return S.get(u, params=p, timeout=120).json()
    except Exception as e: return {"error": str(e)[:200]}
L = "https://lcaudgis.co.lucas.oh.us/gisaudserver/rest/services/"
for fo in ["Tyler", "TylerProduction", "LucasCountyAuditorGIS", "FeatureServices", "OtherRealEstate", "Requests", "Cadastre", "LucasCountyCommissioners"]:
    out("folder", {"f": fo, "s": [(s["name"], s["type"]) for s in get(L + fo).get("services", [])]})
# freshness / content of the general collections
G = L + "Hosted/AREIS_GENERAL_COLLECTIONS/FeatureServer/0/query"
st = get(G, where="1=1", outStatisticFieldName="x", outStatistics=json.dumps([{"statisticType": "count", "onStatisticField": "objectid_1", "outStatisticFieldName": "n"}, {"statisticType": "sum", "onStatisticField": "taxdue", "outStatisticFieldName": "due"}, {"statisticType": "max", "onStatisticField": "certyr", "outStatisticFieldName": "maxcert"}]))
out("gc_stats", st)
out("gc_cert", get(G, where="taxdue>0", groupByFieldsForStatistics="certyr", outStatistics=json.dumps([{"statisticType": "count", "onStatisticField": "objectid_1", "outStatisticFieldName": "n"}])))
s = get(G, where="taxdue>5000 and class='R'", outFields="parcel,owner,streetnumber,direction,address,adrsuf,city,state,zip,certyr,taxdue,balance,collect,priorge1,total,landuse", resultRecordCount=3, returnGeometry="false")
out("gc_sample", [f["attributes"] for f in s.get("features", [])])
# cityworks request types (2026)
C = "https://gis.toledo.oh.gov/arcgis/rest/services/Public/CityWorks_ServiceRequest_2022/MapServer/1/query"
out("cw_types", get(C, where="1=1", groupByFieldsForStatistics="DESCRIPTION", outStatistics=json.dumps([{"statisticType": "count", "onStatisticField": "REQUEST_ID", "outStatisticFieldName": "n"}])))
out("cw_range", get(C, where="1=1", outStatistics=json.dumps([{"statisticType": "min", "onStatisticField": "INIT_DATE", "outStatisticFieldName": "mn"}, {"statisticType": "max", "onStatisticField": "INIT_DATE", "outStatisticFieldName": "mx"}])))
s = get(C, where="DESCRIPTION LIKE '%Structure%' OR DESCRIPTION LIKE '%Blight%'", outFields="*", resultRecordCount=4, orderByFields="INIT_DATE DESC")
out("cw_sample", [f["attributes"] for f in s.get("features", [])])
M = "https://gis.toledo.oh.gov/arcgis/rest/services/Grass_Mowing_Program/MapServer/0/query"
out("mow", get(M, where="1=1", groupByFieldsForStatistics="Funding_Source,Active_Inactive", outStatistics=json.dumps([{"statisticType": "count", "onStatisticField": "OBJECTID", "outStatisticFieldName": "n"}])))
out("mow_cy", get(M, where="1=1", groupByFieldsForStatistics="ContractYear,Managed_By", outStatistics=json.dumps([{"statisticType": "count", "onStatisticField": "OBJECTID", "outStatisticFieldName": "n"}])))
D = "https://gis.toledo.oh.gov/arcgis/rest/services/Demolition_Map_MIL1/MapServer/0/query"
s = get(D, where="1=1", outFields="PARCEL,ADDRESS,Status_2,OWNER_S__O,OWNER_S__T,ORDER_D_R_,TEARDOWN_D,On_Active_", resultRecordCount=4, returnGeometry="false")
out("demo", s)
