import json, re, time, pathlib
from curl_cffi import requests
S = requests.Session(impersonate="chrome")
B = "https://go.mcohio.org/applications/probate/prodcfm/"
O = pathlib.Path("recon/out"); O.mkdir(exist_ok=True)
def out(t, o): print(f"@@{t}@@ " + json.dumps(o)[:3000], flush=True)
r = S.get(B + "casesearch.cfm", timeout=40); (O / "form.html").write_text(r.text); out("form", {"s": r.status_code, "len": len(r.text)})
def search(nbr, year="2026"):
    time.sleep(2)
    r = S.post(B + "casesearch_actionx.cfm", data={"caseyear": year, "casenbr": f"{nbr:05d}", "SEARCH": "GO"}, timeout=40)
    return r.text
for n in [2090, 2095, 2100, 2110, 1500, 1200]:
    h = search(n); (O / f"search_{n}.html").write_text(h)
    links = re.findall(r'href="(casesearchresultx\.cfm\?[^"]+)"', h)
    out("search", {"n": n, "links": links})
    for i, l in enumerate(links[:3]):
        time.sleep(2)
        d = S.get(B + l.replace("&amp;", "&"), timeout=40); (O / f"detail_{n}_{i}.html").write_text(d.text)
        out("detail", {"n": n, "i": i, "len": len(d.text), "sub": sorted(set(re.findall(r'href="([^"]+)"', d.text)))[:15]})
