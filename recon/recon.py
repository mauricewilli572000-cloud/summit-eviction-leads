import re, time, pathlib
from curl_cffi import requests
S = requests.Session(impersonate="chrome")
B = "https://go.mcohio.org/applications/probate/prodcfm/"
O = pathlib.Path("recon/out"); O.mkdir(exist_ok=True)
for n in [1500, 2089, 2091]:
    time.sleep(2)
    h = S.post(B + "casesearch_actionx.cfm", data={"caseyear": "2026", "casenbr": f"{n:05d}", "SEARCH": "GO"}, timeout=40).text
    for l in re.findall(r'href="(casesearchresultx\.cfm\?[^"]+)"', h)[:1]:
        time.sleep(2); d = S.get(B + l, timeout=40).text; (O / f"detail_{n}_0.html").write_text(d)
        for k in re.findall(r'href="(CASESEARCH_DOCKETx\.cfm\?[^"]+)"', d)[:1]:
            time.sleep(2); (O / f"docket_{n}.html").write_text(S.get(B + k, timeout=40).text)
    print("@@n@@", n, "found" if "casesearchresultx" in h else "none")
