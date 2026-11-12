import json, re, html
from curl_cffi import requests
S = requests.Session(impersonate="chrome")
def out(t, o): print(f"@@{t}@@ " + json.dumps(o)[:6000], flush=True)
def txt(s): return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", s, flags=re.S|re.I)))).strip()
for u in ["https://clerkweb.summitoh.net/RecordsSearch/Disclaimer.asp?toPage=SelectDivision.asp",
          "https://clerkweb.summitoh.net/RecordsSearch/SelectDivision.asp"]:
    try:
        r = S.get(u, timeout=40)
        out("try", {"u": u, "status": r.status_code, "final": r.url, "text": txt(r.text)[:3500],
                    "forms": [f[:1500] for f in re.findall(r"<form.*?</form>", r.text, re.S|re.I)[:2]]})
    except Exception as e:
        out("try", {"u": u, "err": str(e)[:200]})
