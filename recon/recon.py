import json, re, html
from curl_cffi import requests
S = requests.Session(impersonate="chrome")
B = "https://franklin.oh.publicsearch.us"
def out(t, o): print(f"@@{t}@@ " + json.dumps(o)[:7000], flush=True)
def txt(s): return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", s, flags=re.S|re.I)))).strip()
for path in ["/robots.txt", "/", "/terms", "/terms-of-use", "/tos"]:
    try:
        r = S.get(B + path, timeout=40)
        out("page", {"path": path, "status": r.status_code, "len": len(r.text), "text": (r.text[:1500] if path == "/robots.txt" else txt(r.text)[:1500]),
                     "links": sorted(set(re.findall(r'(?:href|src)="([^"]+)"', r.text)))[:40]})
    except Exception as e:
        out("page", {"path": path, "err": str(e)[:200]})
# JS bundle: look for terms text and API endpoints
try:
    r = S.get(B + "/", timeout=40)
    for js in re.findall(r'src="([^"]+\.js)"', r.text)[:4]:
        u = js if js.startswith("http") else B + js
        j = S.get(u, timeout=60).text
        out("js", {"u": u, "len": len(j), "api": sorted(set(re.findall(r'["\'](/api/[a-zA-Z0-9/_-]+)', j)))[:60],
                   "terms": [j[max(0, m.start()-200): m.start()+400] for m in re.finditer(r"(?i)automated|scrap|robot|bulk", j)][:6]})
except Exception as e:
    out("js", {"err": str(e)[:200]})
