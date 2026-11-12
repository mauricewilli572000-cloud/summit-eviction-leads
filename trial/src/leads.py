"""Turn Lucas County Auditor rows into filtered, flagged, scored tax delinquent leads."""
from __future__ import annotations

import re

import config
from src.property_type import classify

# Owners that are not motivated sellers: government, churches, land banks, banks, HOAs.
# (Patterns shared with the Montgomery scraper, plus Lucas County's own land bank / forfeited land.)
SKIP_OWNER = re.compile(
    r"\b(CITY OF|VILLAGE OF|COUNTY|STATE OF OHIO|STATE OF|TOWNSHIP|TWP TRUSTEES|BOARD OF|"
    r"BOARD OF EDUCATION|SCHOOL|UNITED STATES|SECRETARY OF|HOUSING AUTHORITY|METROPOLITAN HOUSING|"
    r"LAND BANK|LAND REUTILIZATION|FORFEITED LAND|TOLEDO LUCAS COUNTY|PORT AUTHORITY|MIAMI CONSERVANCY|FIVE RIVERS METROPARKS|METROPARKS|"
    r"CHURCH|MINISTR(Y|IES)|BAPTIST|METHODIST|LUTHERAN|PRESBYTERIAN|CATHOLIC|DIOCESE|ARCHDIOCESE|"
    r"TEMPLE|SYNAGOGUE|CONGREGATION|MOSQUE|ISLAMIC|KINGDOM HALL|JEHOVAH|TABERNACLE|APOSTOLIC|PENTECOSTAL|"
    r"FEDERAL NATIONAL MORTGAGE|FEDERAL HOME LOAN|FANNIE MAE|FREDDIE MAC|BANK N ?A|NATIONAL ASSOCIATION|"
    r"HOMEOWNERS? ASS|CONDOMINIUM ASS|OWNERS ASS|COMMUNITY ASS|RAILROAD|RAILWAY|CEMETERY)\b")
COMPANY = re.compile(r"\b(LLC|L L C|INC|CORP|CORPORATION|LTD|LP|LLP|CO|COMPANY|PROPERTIES|"
                     r"INVESTMENTS?|HOLDINGS?|ENTERPRISES?|GROUP|PARTNERS|REALTY|VENTURES?)\b")
TRUST = re.compile(r"\b(TR|TRS|TRUST|TRUSTEE|TRUSTEES)\b")
ESTATE = re.compile(r"\b(ESTATE OF|EST OF|DECEASED|DEC'D)\b|\bEST$")
CITY_ST_ZIP = re.compile(r"^(.*?)\s+([A-Z]{2})\s+(\d{5})(?:[ -]?(\d{4}))?$")




def num(v) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def clean(s) -> str:
    return re.sub(r"\s+", " ", str(s or "")).strip()


def split_address(full: str) -> dict:
    """'2540 MONROE ST # 107C, TOLEDO OH 43620-1234' -> street / city / state / zip."""
    full = clean(full).upper()
    out = {"street": full, "city": "", "state": "", "zip": ""}
    if "," in full:
        street, rest = full.rsplit(",", 1)
        m = CITY_ST_ZIP.match(rest.strip().replace(",", ""))
        if m:
            out.update(street=street.strip(), city=m[1].strip(), state=m[2], zip=m[3])
    return out


def _words(name: str) -> list[str]:
    name = re.sub(r"\(.*?\)", " ", (name or "").upper())
    return re.sub(r"[^A-Z ]", " ", name).split()


def same_owner(snapshot: str, current: str) -> bool:
    """Owner on the tax snapshot is still the owner today (first two name words agree)."""
    a, b = _words(snapshot), _words(current)
    return bool(a and b) and a[:2] == b[:2]


def street_key(addr: str) -> str:
    words = re.sub(r"[^A-Z0-9 ]", " ", (addr or "").upper()).split()
    if not words:
        return ""
    rest = [w for w in words[1:] if not w.isdigit() and w not in ("N", "S", "E", "W")]
    return f"{words[0]} {rest[0] if rest else ''}".strip()


def build(g: dict, pa: dict, cama: dict, rental: bool, snapshot_year: int) -> tuple[dict | None, str]:
    """g = collections row, pa = live parcel-address row, cama = CAMA row. Returns (lead, skip reason)."""
    owed = num(g.get("taxdue"))
    cls = clean(pa.get("CLASS") or g.get("class"))
    cert = int(num(g.get("certyr")))
    if owed < config.MIN_OWED:
        return None, "small balance"
    if cls in config.SKIP_CLASSES:
        return None, "exempt / utility"
    if not pa:
        return None, "parcel retired"
    owner = clean(pa.get("OWNER"))
    if not same_owner(g.get("owner", ""), owner):
        return None, "owner changed since snapshot"
    if not owner or SKIP_OWNER.search(owner.upper()):
        return None, "government / church / bank owner"
    years = snapshot_year - cert + 1 if cert > 1900 else 0
    if years < config.MIN_YEARS:
        return None, "under 2 years behind"

    luc = clean(pa.get("LUC") or g.get("landuse"))
    category, ptype = classify(luc)
    if category == "Exempt/Government":
        return None, "exempt / utility"
    prop = split_address(pa.get("PROPERTY_ADDRESS"))
    mail = split_address(pa.get("MAILING_ADDRESS"))
    market = num(cama.get("TOTALVALUE")) or num(g.get("total"))
    out_of_state = bool(mail["state"]) and mail["state"] != "OH"
    absentee = bool(mail["street"]) and street_key(mail["street"]) != street_key(prop["street"])
    cond = clean(cama.get("COND_DESC")).upper()
    yb = int(num(cama.get("RESYRBLT")))
    pid = clean(pa.get("PARID") or g.get("parcel"))
    rec = {
        "doc_num": pid, "owner_name": owner, "owner_name_2": "",
        "mailing_address": mail["street"], "mailing_city": mail["city"], "mailing_state": mail["state"],
        "mailing_zip": mail["zip"],
        "property_address": prop["street"], "property_city": prop["city"] or clean(cama.get("SITECITY")),
        "property_zip": prop["zip"] or clean(cama.get("SITEZIP")),
        "amount_owed": round(owed, 2), "delinquent_amount": None, "years_owed": float(years),
        "tax_year": str(cert) if cert else "", "advertised_years": [], "tax_foreclosure_filed": "",
        "absentee_owner": absentee, "out_of_state": out_of_state, "company_owner": bool(COMPANY.search(owner)),
        "vacant": category == "Vacant Land",
        "rental_registered": rental, "on_contract": False,
        "market_value": market, "last_sale_date": "", "last_sale_amount": 0.0,
        "property_category": category, "property_type": ptype, "land_use": luc,
        "year_built": str(yb) if yb else "", "condition": cond.title() if cond and cond != "N/A" else "",
        "auditor_url": config.AUDITOR_URL,
    }
    rec.update(score_lead(rec))
    return rec, ""


def score_lead(r: dict) -> dict:
    """Same weights as Montgomery. Lucas has no sale dates, so building condition stands in
    for the 'owned 20+ years' bump: a poor-condition house plus back taxes is a classic tired owner."""
    yrs, owed, market, owner, category = r["years_owed"], r["amount_owed"], r["market_value"], \
        r["owner_name"], r["property_category"]
    score, flags = 25, []
    if yrs >= 10:
        score += 15
    elif yrs >= 4:
        score += 12
    elif yrs >= 2:
        score += 8
    if yrs:
        flags.append(f"~{yrs:.0f} years owed")
    if r["tax_year"]:
        flags.append(f"Delinquent since {r['tax_year']}")
    if owed >= 15000:
        score += 12; flags.append("$15k+ owed")
    elif owed >= 5000:
        score += 8; flags.append("$5k+ owed")
    else:
        score += 3
    if market >= 20000 and owed / market >= 0.2:
        score += 5; flags.append(f"Owes {owed / market:.0%} of value")
    if r["absentee_owner"]:
        score += 8; flags.append("Absentee owner")
    if r["out_of_state"]:
        score += 5; flags.append("Out-of-state owner")
    if r["condition"] in ("Poor", "Very Poor", "Unsound"):
        score += 12; flags.append(f"{r['condition']} condition")
    elif r["condition"] == "Fair":
        score += 4; flags.append("Fair condition")
    if ESTATE.search(owner):
        score += 10; flags.append("Estate")
    if TRUST.search(owner):
        flags.append("Trust")
    if r["company_owner"]:
        flags.append("LLC / company")
    if r["rental_registered"]:
        flags.append("Registered rental")
    if category in ("Single Family", "Multi-Family (2-4)", "Condo", "Mobile/Manufactured"):
        score += 8
    flags.append(category)
    if r["vacant"]:
        flags.append("Vacant land")
        score = min(score - 10, 69)
    score = max(0, min(100, score))
    return {"flags": flags, "score": score, "tier": "Hot" if score >= 80 else "Warm" if score >= 60 else "Cold"}
