import json, re, html
from curl_cffi import requests
S = requests.Session(impersonate="chrome")
def out(t, o): print(f"@@{t}@@ " + json.dumps(o)[:4000], flush=True)
def txt(s): return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", s, flags=re.S|re.I)))).strip()
for host in ["https://pro.mcohio.org", "https://go.mcohio.org", "https://www.mcohio.org", "https://www.mctreas.org", "https://www.mcrealestate.org", "https://www.daytonohio.gov"]:
    try:
        r = S.get(host + "/robots.txt", timeout=30); out("robots", {"host": host, "status": r.status_code, "text": r.text[:600]})
    except Exception as e: out("robots", {"host": host, "err": str(e)[:150]})
try:
    r = S.get("https://pro.mcohio.org/", timeout=40); t = txt(r.text)
    i = t.find("Restriction"); out("pro", {"status": r.status_code, "restriction": t[max(0, i-300): i+1500], "links": sorted(set(re.findall(r'href="([^"]+)"', r.text)))[:40]})
except Exception as e: out("pro", {"err": str(e)[:200]})
# open data search on ArcGIS for Dayton / Montgomery
for q in ["Dayton code enforcement", "Dayton nuisance", "Dayton housing violations", "Montgomery County Ohio parcels", "Dayton demolition"]:
    try:
        r = S.get("https://www.arcgis.com/sharing/rest/search", params={"q": q, "f": "json", "num": 10}, timeout=40).json()
        out("arcgis", {"q": q, "hits": [(x.get("title"), x.get("owner"), x.get("type"), x.get("id"), x.get("modified")) for x in r.get("results", [])]})
    except Exception as e: out("arcgis", {"q": q, "err": str(e)[:150]})
