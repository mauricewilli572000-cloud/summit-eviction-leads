import json, re, html
from curl_cffi import requests
S = requests.Session(impersonate="chrome")
def out(t, o): print(f"@@{t}@@ " + json.dumps(o)[:5000], flush=True)
def txt(s): return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", s, flags=re.S|re.I)))).strip()
r = S.get("https://pro.mcohio.org/", timeout=40)
js = re.findall(r"function openDisclaimer\(\).*?\}", r.text, re.S)
out("pro_disclaimer_fn", {"fn": js[:1], "scripts": re.findall(r'src="([^"]+\.js[^"]*)"', r.text)})
m = re.search(r'id="disclaimer[^"]*"[^>]*>(.*?)</div>\s*</div>', r.text, re.S|re.I)
d = re.search(r"(?is)disclaimer.{0,6000}", txt(r.text))
out("pro_text", {"len": len(r.text), "disclaimer": (txt(m.group(1)) if m else "")[:3000], "around": d.group(0)[:2500] if d else ""})
forms = re.findall(r"<(?:select|input)[^>]+>", r.text)
out("pro_inputs", {"inputs": forms[:80]})
for u in ["https://go.mcohio.org/applications/probate/prodcfm/casesearchx.cfm", "https://go.mcohio.org/applications/treasurer/search", "https://www.mcrealestate.org/"]:
    try:
        rr = S.get(u, timeout=40)
        out("page", {"u": u, "status": rr.status_code, "text": txt(rr.text)[:1500], "forms": [f[:1200] for f in re.findall(r"<form.*?</form>", rr.text, re.S|re.I)[:2]], "links": sorted(set(re.findall(r'href="([^"]+)"', rr.text)))[:50]})
    except Exception as e: out("page", {"u": u, "err": str(e)[:150]})
try:
    it = S.get("https://www.arcgis.com/sharing/rest/content/items/e4057ee9d25045b090036ce8685a2977/data", params={"f": "json"}, timeout=40).json()
    layers = [(l.get("title"), l.get("url")) for l in it.get("operationalLayers", [])]
    out("parcelmap", {"layers": layers})
    for title, url in layers[:4]:
        if url:
            info = S.get(url, params={"f": "json"}, timeout=40).json()
            out("layer", {"title": title, "url": url, "fields": [f["name"] for f in info.get("fields", [])][:80], "sublayers": [(x.get("id"), x.get("name")) for x in info.get("layers", [])][:20]})
except Exception as e: out("parcelmap", {"err": str(e)[:200]})
