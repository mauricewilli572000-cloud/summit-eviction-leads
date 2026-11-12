import json, re, html
from curl_cffi import requests
S = requests.Session(impersonate="chrome")
def out(t, o): print(f"@@{t}@@ " + json.dumps(o)[:5000], flush=True)
def txt(s): return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", s, flags=re.S|re.I)))).strip()
r = S.get("https://go.mcohio.org/applications/treasurer/filedownloads.cfm", timeout=40)
out("downloads", {"status": r.status_code, "text": txt(r.text)[:2500], "links": sorted(set(re.findall(r'href="([^"]+)"', r.text)))[:60]})
r = S.post("https://go.mcohio.org/applications/probate/prodcfm/casesearch_actionx.cfm", data={"caseyear": "2026", "casenbr": "00650", "SEARCH": "GO"}, timeout=40)
out("probate", {"status": r.status_code, "url": r.url, "text": txt(r.text)[:3000], "links": sorted(set(re.findall(r'href="([^"]+)"', r.text)))[:30]})
for u in ["https://engineer.gomvo.org/arcgis/rest/services/WMAS/MCEO_Parcels/MapServer?f=json", "https://engineer.gomvo.org/arcgis/rest/services?f=json"]:
    try:
        d = S.get(u, timeout=40).json()
        out("gis", {"u": u, "layers": [(x.get("id"), x.get("name")) for x in d.get("layers", [])][:20], "services": [x.get("name") for x in d.get("services", [])][:40], "folders": d.get("folders")})
    except Exception as e: out("gis", {"u": u, "err": str(e)[:200]})
