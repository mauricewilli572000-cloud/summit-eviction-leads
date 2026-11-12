import json, re
from curl_cffi import requests
S = requests.Session(impersonate="chrome")
B = "https://go.mcohio.org/applications/treasurer/search/"
def out(t, o): print(f"@@{t}@@ " + json.dumps(o)[:6000], flush=True)
r = S.get(B + "filedownloads.cfm", timeout=40)
scripts = re.findall(r"<script[^>]*>(.*?)</script>", r.text, re.S | re.I)
srcs = re.findall(r'<script[^>]+src="([^"]+)"', r.text, re.I)
out("scripts", {"inline": [s.strip()[:1500] for s in scripts if "fdpopup" in s or "popup" in s.lower()][:3], "srcs": srcs})
for s in srcs:
    u = s if s.startswith("http") else B + s
    try:
        j = S.get(u, timeout=40).text
        i = j.find("fdpopup")
        if i >= 0: out("srcjs", {"u": u, "code": j[max(0, i-200): i+1500]})
    except Exception as e: out("srcjs", {"u": u, "err": str(e)[:100]})
