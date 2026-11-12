import json, re, html, time, ssl, socket
from curl_cffi import requests
S = requests.Session(impersonate="chrome")
B = "https://go.mcohio.org/applications/probate/prodcfm/"
def out(t, o): print(f"@@{t}@@ " + json.dumps(o)[:6000], flush=True)
def txt(s): return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", s, flags=re.S|re.I)))).strip()
r = S.get("https://go.mcohio.org/applications/treasurer/search/filedownloads.cfm", timeout=40)
out("downloads", {"status": r.status_code, "text": txt(r.text)[:2000], "links": sorted(set(re.findall(r'href="([^"]+)"', r.text)))[:60]})
def find(nbr):
    time.sleep(2)
    r = S.post(B + "casesearch_actionx.cfm", data={"caseyear": "2026", "casenbr": f"{nbr:05d}", "SEARCH": "GO"}, timeout=40)
    links = re.findall(r'href="(casesearchresultx\.cfm\?[^"]+)"', r.text)
    return links[0] if links else None
lo, hi = 650, 6000
while hi - lo > 1:
    mid = (lo + hi) // 2
    if find(mid): lo = mid
    else: hi = mid
out("newest", {"newest": lo})
for n in [lo, 650]:
    link = find(n)
    if link:
        time.sleep(2)
        d = S.get(B + link, timeout=40)
        rows = [[txt(c) for c in re.findall(r"<t[hd][^>]*>(.*?)</t[hd]>", rw, re.S)] for rw in re.findall(r"<tr[^>]*>(.*?)</tr>", d.text, re.S)]
        out("detail", {"n": n, "text": txt(d.text)[:3000], "rows": [x for x in rows if any(x)][:50], "links": sorted(set(re.findall(r'href="([^"]+)"', d.text)))[:20]})
# GIS certificate chain
try:
    ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
    with socket.create_connection(("engineer.gomvo.org", 443), timeout=20) as sock:
        with ctx.wrap_socket(sock, server_hostname="engineer.gomvo.org") as ss:
            c = ss.getpeercert(binary_form=True)
    from cryptography import x509
    cert = x509.load_der_x509_certificate(c)
    aia = [str(a.access_location.value) for a in cert.extensions.get_extension_for_class(x509.AuthorityInformationAccess).value]
    out("cert", {"subject": cert.subject.rfc4514_string(), "issuer": cert.issuer.rfc4514_string(), "aia": aia})
except Exception as e: out("cert", {"err": str(e)[:300]})
