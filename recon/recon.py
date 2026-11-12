import json, re, html
from curl_cffi import requests
S = requests.Session(impersonate="chrome")
B = "https://go.mcohio.org/applications/treasurer/search/"
def out(t, o): print(f"@@{t}@@ " + json.dumps(o)[:3000], flush=True)
def txt(s): return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", s, flags=re.S|re.I)))).strip()
for code in ["DQ", "TR"]:
    p = S.get(B + f"fdpopup.cfm?dtype={code}", timeout=40)
    links = sorted(set(re.findall(r'href="([^"]+)"', p.text)))
    out("popup", {"code": code, "text": txt(p.text)[300:1800], "links": [l for l in links if not l.startswith("http") or "mcohio" in l][:30]})
    files = [l for l in links if re.search(r"\.(zip|txt|csv|dat|xlsx?)$", l, re.I)]
    if files:
        u = files[0] if files[0].startswith("http") else B + files[0].replace("\\", "/")
        h = S.head(u.replace(" ", "%20"), timeout=40)
        out("file", {"code": code, "u": u, "status": h.status_code, "len": h.headers.get("content-length"), "type": h.headers.get("content-type")})
