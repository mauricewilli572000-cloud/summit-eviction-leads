import json, re, urllib.parse
from curl_cffi import requests as cr
S = cr.Session(impersonate="chrome")
def show(tag, obj): print(f"@@{tag}@@ " + json.dumps(obj, default=str)[:3000])
r = S.get("https://www.akronmunicipalcourt.org/fines-case-search/", timeout=60)
show("fines_case_search_links", sorted({urllib.parse.urljoin(str(r.url), h) for h in re.findall(r'href="([^"#]+)"', r.text) if not re.search(r"akronmunicipalcourt\.org/(case-types|programs|general|court-info|media/\d+/(?!.*evict))", h)})[-40:])
for u in ["https://courts.akronohio.gov/AkronCaseInformation", "http://courts.akronohio.gov/AkronCaseInformation", "https://courts.akronohio.gov/AkronCaseInformation/Home/CourtCalendar"]:
    for imp in ["chrome", "safari"]:
        try:
            s2 = cr.Session(impersonate=imp); x = s2.get(u, timeout=120)
            show(f"{u} {imp}", [x.status_code, re.sub(r"<[^>]+>|\s+", " ", x.text)[:500]]); break
        except Exception as e:
            show(f"{u} {imp}", str(e)[:200])
import socket
try: show("dns", socket.gethostbyname_ex("courts.akronohio.gov"))
except Exception as e: show("dns", str(e))
