import json, re, io, zipfile, csv
from curl_cffi import requests
S = requests.Session(impersonate="chrome")
def out(t, o): print(f"@@{t}@@ " + json.dumps(o, default=str)[:3800], flush=True)
def get(u, **kw):
    try: return S.get(u, timeout=kw.pop("timeout", 300), **kw)
    except Exception as e: return str(e)[:200]
F = "https://apps.franklincountyauditor.com/Outside_User_Files/2026/2026-10-15%20Appraisal/"
r = get(F); out("franklin_appr", re.findall(r'href="([^"]+)"', r.text) if not isinstance(r, str) else r)
r = get("https://cagis.org/Opendata/Quarterly_GIS_Data/OpenData_Layer_List.txt"); out("cagis_layers", r.text[:3000] if not isinstance(r, str) else r)
def zhead(url, maxfiles=3):
    r = get(url)
    if isinstance(r, str): return r
    z = zipfile.ZipFile(io.BytesIO(r.content)); res = {"size": len(r.content), "files": z.namelist()[:10]}
    for n in z.namelist()[:maxfiles]:
        with z.open(n) as f:
            lines = [f.readline().decode("latin-1").rstrip() for _ in range(3)]
        res[n] = lines
    return res
SUM = "https://fiscaloffice.summitoh.net/sites/default/files/assets/forms/"
for n in ["SC706_SALES_5.zip", "SC710_DWELL_5.zip", "SC705_PARDAT_4.zip"]:
    out("summit_" + n, zhead(SUM + n))
j = get("https://services3.arcgis.com/3Ukh5HzAdI6WZ3KP/arcgis/rest/services/TaxParcelSales_public/FeatureServer/0", params={"f": "json"}).json()
out("summit_sales_layer", {"fields": [f["name"] for f in j.get("fields", [])], "edit": j.get("editingInfo")})
s = get("https://services3.arcgis.com/3Ukh5HzAdI6WZ3KP/arcgis/rest/services/TaxParcelSales_public/FeatureServer/0/query", params={"where": "1=1", "outFields": "*", "resultRecordCount": 2, "returnGeometry": "false", "f": "json", "orderByFields": "OBJECTID DESC"}).json()
out("summit_sales_sample", [f["attributes"] for f in s.get("features", [])])
j = get("https://www.arcgis.com/sharing/rest/search", params={"q": 'owner:JasonClay AREIS', "num": 20, "f": "json"}).json()
items = [(x.get("id"), x.get("title"), x.get("type"), x.get("modified"), x.get("size")) for x in j.get("results", [])]
out("lucas_areis", items)
for iid, title, typ, *_ in items:
    if "2025" in (title or "") or "2026" in (title or ""):
        d = get(f"https://www.arcgis.com/sharing/rest/content/items/{iid}/data", timeout=300)
        out("lucas_areis_data", {"t": title, "s": getattr(d, "status_code", d), "ct": getattr(d, "headers", {}).get("content-type") if not isinstance(d, str) else "", "len": len(d.content) if not isinstance(d, str) else 0})
        if not isinstance(d, str) and d.content[:2] == b"PK":
            z = zipfile.ZipFile(io.BytesIO(d.content)); out("lucas_areis_zip", {n: z.getinfo(n).file_size for n in z.namelist()[:40]})
            for n in z.namelist():
                if re.search(r"sale", n, re.I):
                    with z.open(n) as f: out("lucas_sales_head", {"n": n, "l": [f.readline().decode("latin-1").rstrip() for _ in range(3)]})
