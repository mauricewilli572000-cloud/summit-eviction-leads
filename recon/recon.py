import json, re, io, zipfile
from curl_cffi import requests
from openpyxl import load_workbook
S = requests.Session(impersonate="chrome")
def out(t, o): print(f"@@{t}@@ " + json.dumps(o, default=str)[:3800], flush=True)
F = "https://apps.franklincountyauditor.com/Outside_User_Files/2026/2026-10-15%20Appraisal/"
html = S.get(F, timeout=60).text
out("franklin_files", re.findall(r'(\d+) <A HREF="[^"]+">([^<]+)</A>', html))
for name in ["Sales010.xlsx", "Dwelling.xlsx", "Parcel.xlsx"]:
    b = S.get(F + name, timeout=900).content
    wb = load_workbook(io.BytesIO(b), read_only=True)
    ws = wb[wb.sheetnames[0]]
    rows = []
    for i, r in enumerate(ws.iter_rows(values_only=True)):
        rows.append(r)
        if i >= 2: break
    out("franklin_" + name, {"sheets": wb.sheetnames, "rows": rows})
