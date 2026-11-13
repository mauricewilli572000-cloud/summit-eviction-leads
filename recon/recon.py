import json, re, io, zipfile, csv, subprocess, os
from curl_cffi import requests
S = requests.Session(impersonate="chrome")
def out(t, o): print(f"@@{t}@@ " + json.dumps(o, default=str)[:3800], flush=True)
def get(u, **kw):
    try: return S.get(u, timeout=kw.pop("timeout", 300), **kw)
    except Exception as e: return str(e)[:200]
F = "https://apps.franklincountyauditor.com/Outside_User_Files/2026/2026-10-15%20Appraisal/"
r = get(F); out("franklin_appr_raw", r.text[:2500] if not isinstance(r, str) else r)
d = get("https://www.arcgis.com/sharing/rest/content/items/8e00e957fcc04a81aac77e8bfc17b2dc/data", timeout=600)
open("/tmp/a.zip", "wb").write(d.content)
zipfile.ZipFile("/tmp/a.zip").extractall("/tmp/a")
mdb = "/tmp/a/" + os.listdir("/tmp/a")[0]
tables = subprocess.run(["mdb-tables", "-1", mdb], capture_output=True, text=True).stdout.split("\n")
out("lucas_tables", tables)
for t in tables:
    if not t: continue
    o = subprocess.run(f"mdb-export '{mdb}' '{t}' | head -3", shell=True, capture_output=True, text=True).stdout
    n = subprocess.run(f"mdb-export '{mdb}' '{t}' | wc -l", shell=True, capture_output=True, text=True).stdout.strip()
    out("lucas_t", {"t": t, "rows": n, "head": o[:1500]})
r = get("https://cagis.org/Opendata/Quarterly_GIS_Data/Hamilton%20County%20Parcels%20July%202026.csv", stream=True, timeout=120)
if not isinstance(r, str):
    lines = []
    for chunk in r.iter_lines():
        lines.append(chunk.decode("latin-1")); 
        if len(lines) >= 3: break
    out("cagis_csv", lines)
