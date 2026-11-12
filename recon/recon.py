import json, re
from curl_cffi import requests
S = requests.Session(impersonate="chrome")
def out(t, o): print(f"@@{t}@@ " + json.dumps(o)[:3000], flush=True)
for u in ["http://clerk.summitoh.net/RecordsSearch/SelectDivision.asp", "https://clerk.summitoh.net/",
          "https://clerkweb.summitoh.net/", "https://newcivilfilings.summitoh.net/"]:
    try:
        r = S.get(u, timeout=40)
        out("try", {"u": u, "status": r.status_code, "final": r.url, "len": len(r.text),
                    "records_links": sorted(set(re.findall(r'href="([^"]*(?:Records|records|Search|search)[^"]*)"', r.text)))[:20]})
    except Exception as e:
        out("try", {"u": u, "err": str(e)[:200]})
