import json, re, io, zipfile, csv
from curl_cffi import requests
S = requests.Session(impersonate="chrome")
def out(t, o): print(f"@@{t}@@ " + json.dumps(o, default=str)[:3800], flush=True)
def get(u, **kw):
    try: return S.get(u, timeout=kw.pop("timeout", 90), **kw)
    except Exception as e: return str(e)[:200]
for u in ["https://apps.franklincountyauditor.com/Outside_User_Files/", "https://apps.franklincountyauditor.com/Outside_User_Files/2026/", "https://cagis.org/Opendata/Quarterly_GIS_Data/"]:
    r = get(u); t = r if isinstance(r, str) else r.text
    out("dir", {"u": u, "items": re.findall(r'(?i)(?:href=["\']?)([^"\'>\s]+\.(?:zip|txt|csv|xlsx?|gdb|shp)|[^"\'>\s]+/)', t)[:150]})
r = get("https://fiscaloffice.summitoh.net/data-downloads")
out("summit", sorted(set(re.findall(r'href="([^"]+\.(?:zip|csv|txt|xlsx?))"', r.text)))) if not isinstance(r, str) else out("summit", r)
# Lucas: every folder/service with sale in name
L = "https://lcaudgis.co.lucas.oh.us/gisaudserver/rest/services/"
root = get(L + "?f=json").json()
found = []
for fo in root.get("folders", []):
    try:
        for s in get(L + fo + "?f=json").json().get("services", []):
            if re.search(r"sale|transfer|conv|deed|market", s["name"], re.I): found.append(s["name"] + ":" + s["type"])
    except Exception: pass
out("lucas_sales", found)
# Montgomery GIS candidates
for u in ["https://gis.mcohio.org/arcgis/rest/services", "https://gis.mcohio.org/server/rest/services", "https://mcgis.mcohio.org/arcgis/rest/services", "https://services.arcgis.com/search"]:
    r = get(u, params={"f": "json"}); out("mont", {"u": u, "r": r if isinstance(r, str) else r.text[:400]})
j = get("https://www.arcgis.com/sharing/rest/search", params={"q": "montgomery county ohio parcels", "num": 15, "f": "json"}).json()
out("mont_agol", [(x.get("title"), x.get("type"), x.get("owner"), x.get("url")) for x in j.get("results", [])])
j = get("https://www.arcgis.com/sharing/rest/search", params={"q": "lucas county ohio sales", "num": 15, "f": "json"}).json()
out("lucas_agol", [(x.get("title"), x.get("type"), x.get("owner"), x.get("url")) for x in j.get("results", [])])
j = get("https://www.arcgis.com/sharing/rest/search", params={"q": "summit county ohio parcels", "num": 15, "f": "json"}).json()
out("summit_agol", [(x.get("title"), x.get("type"), x.get("owner"), x.get("url")) for x in j.get("results", [])])
# Montgomery taxroll header only (stream first line)
B = "https://go.mcohio.org/applications/treasurer/search/"
h = get(B + "fdpopup.cfm?dtype=TR").text
p = max(l.replace("\\", "/") for l in re.findall(r"href=[\"']?(data[\\/][^\"'\s>]+\.zip)", h, re.I))
z = zipfile.ZipFile(io.BytesIO(get(B + p, timeout=600).content))
rd = csv.reader(io.TextIOWrapper(z.open(z.namelist()[0]), encoding="latin-1"))
hdr = [x.strip() for x in next(rd)]; row = [x.strip() for x in next(rd)]
out("mont_hdr", dict(zip(hdr, row)))
