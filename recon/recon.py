import json, re, html
from curl_cffi import requests
S = requests.Session(impersonate="chrome")
B = "https://go.mcohio.org/applications/treasurer/search/"
def out(t, o): print(f"@@{t}@@ " + json.dumps(o)[:5000], flush=True)
def txt(s): return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", s, flags=re.S|re.I)))).strip()
r = S.get(B + "filedownloads.cfm", timeout=40)
out("js", {"fdpopup": re.findall(r"function fdpopup.*?\}", r.text, re.S)[:1]})
for code in ["DQ", "TR", "MS"]:
    for page in [f"fdpopup.cfm?type={code}", f"filedownloadpopup.cfm?type={code}", f"filedownloads_popup.cfm?type={code}"]:
        try:
            p = S.get(B + page, timeout=40)
            if p.status_code == 200 and "Error Occurred" not in p.text:
                out("popup", {"code": code, "page": page, "text": txt(p.text)[:1500], "links": sorted(set(re.findall(r'href="([^"]+)"', p.text)))[:30]})
                break
        except Exception as e:
            out("popup", {"code": code, "page": page, "err": str(e)[:150]})
