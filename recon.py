import json, re, urllib.parse
from curl_cffi import requests as cr
S = cr.Session(impersonate="chrome")
def show(tag, obj): print(f"@@{tag}@@ " + json.dumps(obj, default=str)[:5000])
def info(tag, u):
    try:
        r = S.get(u, timeout=60)
    except Exception as e:
        show(tag, str(e)); return None
    t = r.text
    forms = re.findall(r"<form.*?</form>", t, re.S)
    show(tag, {"st": r.status_code, "url": str(r.url), "captcha": bool(re.search(r"recaptcha|g-recaptcha|hcaptcha|turnstile|awswaf|captcha", t, re.I)),
               "forms": [{"tag": re.search(r"<form[^>]*>", f).group(0), "inputs": re.findall(r"<(?:input|select)[^>]*>", f)[:20], "options": re.findall(r"<option[^>]*>([^<]*)", f)[:30]} for f in forms[:3]],
               "links": sorted({urllib.parse.urljoin(str(r.url), h) for h in re.findall(r'href="([^"#]+)"', t) if re.search(r"calendar|case|search|docket|schedule|evict|landlord", h, re.I)})[:40],
               "text": re.sub(r"<script.*?</script>|<style.*?</style>|<[^>]+>|\s+", " ", t)[:800]})
    return r
info("case_info", "https://courts.akronohio.gov/AkronCaseInformation")
info("courts_root", "https://courts.akronohio.gov/")
info("amc_site", "https://www.akronmunicipalcourt.org/")
info("amc_lt", "https://www.akronmunicipalcourt.org/case-types/landlord-tenants/")
