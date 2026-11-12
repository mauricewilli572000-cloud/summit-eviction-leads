import json, re
from curl_cffi import requests
S = requests.Session(impersonate="chrome")
B = "https://go.mcohio.org/applications/treasurer/search/"
r = S.get(B + "filedownloads.cfm", timeout=40)
t = r.text
print("@@len@@", len(t))
for m in list(re.finditer(r"(?i)popup|window\.open|<script", t))[:12]:
    print("@@ctx@@", json.dumps(t[max(0, m.start()-300): m.start()+500]))
