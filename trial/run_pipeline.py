"""Toledo code enforcement leads: resident complaints about neglected property, parcels the city
mows for the owner, and the city's demolition list, joined to the Lucas County Auditor's owner and
mailing address. One lead per property; daily."""
from __future__ import annotations

import csv
import json
import logging
import re
from datetime import date, datetime, timedelta, timezone

import config
from src import arcgis

log = logging.getLogger("toledo-code")

GOV = re.compile(r"\b(CITY OF|COUNTY|STATE OF|BOARD OF|SCHOOL|UNITED STATES|HOUSING AUTHORITY|METROPOLITAN HOUSING|"
                 r"LAND REUTILIZATION|LAND BANK|FORFEITED LAND|PORT AUTHORITY|METROPARKS|CHURCH|MINISTR|"
                 r"BAPTIST|CATHOLIC|DIOCESE|CONGREGATION|TEMPLE|TABERNACLE|CEMETERY|RAILROAD|RAILWAY)\b")
ENTITY = re.compile(r"\b(LLC|L L C|INC|CORP|CORPORATION|LTD|LP|LLP|CO|COMPANY|PROPERTIES|INVESTMENTS?|"
                    r"HOLDINGS?|ENTERPRISES?|GROUP|PARTNERS|REALTY|VENTURES?|TRUST|TR|TRS|TRUSTEE)\b")
INSTITUTION = re.compile(r"\b(BANK|MORTGAGE|FEDERAL NATIONAL|FANNIE|FREDDIE|SFR|PORTFOLIO|HOME PARTNERS|"
                         r"PROGRESS RESIDENTIAL|INVITATION HOMES|AMHERST|VINEBROOK|MAIN STREET RENEWAL)\b")
SUFFIX = {"STREET": "ST", "AVENUE": "AVE", "DRIVE": "DR", "ROAD": "RD", "COURT": "CT", "LANE": "LN",
          "PLACE": "PL", "BOULEVARD": "BLVD", "PARKWAY": "PKWY", "CIRCLE": "CIR", "TERRACE": "TER"}


def clean(s) -> str:
    return re.sub(r"\s+", " ", str(s or "")).strip().upper()


def addr_key(street: str) -> str:
    """'1057 King Street' -> '1057 KING ST' (number + street, suffix abbreviated, no unit)."""
    s = re.sub(r"[.,#]", " ", clean(street))
    s = re.sub(r"\s+(APT|UNIT|STE|LOT)\s*\S+$", "", s)
    w = s.split()
    if len(w) > 2:
        w[-1] = SUFFIX.get(w[-1], w[-1])
    for i in range(1, len(w) - 1):                 # '411 3 ST' -> '411 3RD ST' (Auditor spelling)
        if w[i].isdigit():
            n = int(w[i])
            w[i] += "TH" if 10 <= n % 100 <= 20 else {1: "ST", 2: "ND", 3: "RD"}.get(n % 10, "TH")
    return " ".join(w)


def split_location(loc: str) -> tuple[str, str]:
    """'1057 KING ST,  TOLEDO,  OH,  43607' -> ('1057 KING ST', '43607')."""
    parts = [p.strip() for p in clean(loc).split(",")]
    zip_ = next((p[:5] for p in reversed(parts) if re.fullmatch(r"\d{5}(-\d{4})?", p)), "")
    return parts[0] if parts else "", zip_


def iso(ms) -> str:
    try:
        return datetime.fromtimestamp(ms / 1000, timezone.utc).date().isoformat() if ms else ""
    except (TypeError, ValueError, OSError):
        return ""


def owner_class(owner: str) -> str:
    if not owner:
        return "unknown"
    if GOV.search(owner):
        return "government"
    if INSTITUTION.search(owner):
        return "institutional"
    return "entity" if ENTITY.search(owner) else "individual"


# --------------------------------------------------------------------------- collect
def collect(today: date) -> list[dict]:
    """Every signal as {key: parcel or address, source, label, points, date, open, parcel, address, zip, ...}."""
    sig = []
    since = (today - timedelta(days=config.LOOKBACK_DAYS)).isoformat()
    # One single-condition query per type: the city's firewall (403) rejects compound
    # where-clauses (AND / IN lists), so the date window is applied here instead.
    reqs = []
    for t in config.REQUEST_TYPES:
        prefix = " ".join(t.split()[:2]).replace("'", "''")
        reqs += [r for r in arcgis.query_all(
            config.SERVICE_REQUESTS, f"DESCRIPTION LIKE '{prefix}%'",
            "REQUEST_ID,DESCRIPTION,INIT_DATE,CLOSED_DATE,STATUS,RESOLUTION,LOCATION,PROBZIP",
            order="REQUEST_ID") if r.get("DESCRIPTION") == t and iso(r.get("INIT_DATE")) >= since]
    log.info("service requests: %d", len(reqs))
    recent = (today - timedelta(days=config.OPEN_DAYS)).isoformat()
    for r in reqs:
        street, zip_ = split_location(r.get("LOCATION"))
        if not re.match(r"^\d+\s+\S", street):          # intersections / blocks: not a property
            continue
        if any(x in clean(r.get("RESOLUTION")) for x in config.DISMISSED):   # unfounded or duplicate
            continue
        label, pts = config.REQUEST_TYPES[r["DESCRIPTION"]]
        opened = iso(r.get("INIT_DATE"))
        is_open = clean(r.get("STATUS")) != "CLOSED"
        sig.append({"source": "request", "label": label, "points": pts, "date": opened,
                    "open": is_open or opened >= recent, "id": f"SR{r['REQUEST_ID']}",
                    "address": addr_key(street), "zip": zip_ or str(r.get("PROBZIP") or ""), "parcel": "",
                    "status": clean(r.get("STATUS")), "note": clean(r.get("RESOLUTION"))})
    mow = [m for m in arcgis.query_all(config.MOWING, "Funding_Source = 'Code Enforcement'",
                                       "Parcel_No,PARCELADDR,Address,OWNERNAME,LastMowDate,Comments,AssetID,Active_Inactive",
                                       order="OBJECTID") if m.get("Active_Inactive") == "Active"]
    log.info("city-mowed parcels: %d", len(mow))
    for m in mow:
        street, zip_ = split_location(m.get("PARCELADDR") or m.get("Address"))
        sig.append({"source": "mowing", "label": "City mows it (owner neglect)", "points": config.MOWING_POINTS,
                    "date": iso(m.get("LastMowDate")), "open": True, "id": m.get("AssetID") or "",
                    "address": addr_key(street), "zip": zip_, "parcel": clean(m.get("Parcel_No")),
                    "status": "ACTIVE", "note": clean(m.get("Comments"))})
    demos = arcgis.query_all(config.DEMOS, "1=1", "PARCEL,ADDRESS,ZIP,Status_2,On_Active_")
    log.info("demolition list: %d", len(demos))
    for d in demos:
        sig.append({"source": "demolition", "label": "City demolition list", "points": config.DEMO_POINTS,
                    "date": "", "open": True, "id": f"DEMO{clean(d.get('PARCEL'))}",
                    "address": addr_key(d.get("ADDRESS")), "zip": str(d.get("ZIP") or "")[:5],
                    "parcel": re.sub(r"\D", "", str(d.get("PARCEL") or "")).zfill(7) if d.get("PARCEL") else "",
                    "status": clean(d.get("Status_2")), "note": ""})
    return [s for s in sig if s["address"] or s["parcel"]]


# --------------------------------------------------------------------------- enrich
def parcel_rows(signals: list[dict]) -> tuple[dict, dict]:
    """Auditor parcel-address rows indexed by parcel and by 'NUM STREET|ZIP'."""
    by_pid, by_addr = {}, {}

    def add(rows):
        for r in rows:
            pid = clean(r.get("PARID"))
            by_pid[pid] = r
            street, rest = (clean(r.get("PROPERTY_ADDRESS")).rsplit(",", 1) + [""])[:2]
            m = re.search(r"(\d{5})", rest)
            by_addr.setdefault(f"{addr_key(street)}|{m[1] if m else ''}", r)
            by_addr.setdefault(f"{addr_key(street)}|", r)

    fields = "PARID,OWNER,PROPERTY_ADDRESS,MAILING_ADDRESS,CLASS,LUC"
    add(arcgis.query_in(config.PARCEL_ADDR, "PARID", [s["parcel"] for s in signals if s["parcel"]], fields))
    # Addresses: the Auditor stores 'NUM STREET SUF, TOLEDO OH ZIP'; match on the street part with LIKE.
    need = sorted({s["address"] for s in signals if not s["parcel"]})
    for i in range(0, len(need), 60):
        ors = " OR ".join("PROPERTY_ADDRESS LIKE '" + a.replace("'", "''") + ",%'" for a in need[i:i + 60])
        add(arcgis.query_all(config.PARCEL_ADDR, ors, fields))
    return by_pid, by_addr


def build(signals: list[dict], by_pid: dict, by_addr: dict, state: dict, today: date) -> list[dict]:
    groups: dict[str, dict] = {}
    for s in signals:
        p = by_pid.get(s["parcel"]) if s["parcel"] else None
        p = p or by_addr.get(f"{s['address']}|{s['zip']}") or by_addr.get(f"{s['address']}|")
        key = f"P:{clean(p['PARID'])}" if p else f"A:{s['address']}|{s['zip']}"
        g = groups.setdefault(key, {"parcel_row": p, "signals": []})
        g["signals"].append(s)

    leads = []
    for key, g in groups.items():
        sigs, p = g["signals"], g["parcel_row"] or {}
        opened = [s for s in sigs if s["open"]]
        if not opened:
            continue
        owner = clean(p.get("OWNER"))
        oc = owner_class(owner)
        if oc == "government":
            continue
        mailing = clean(p.get("MAILING_ADDRESS"))
        m = re.search(r",\s*.*?\s([A-Z]{2})\s+\d{5}", mailing)
        mail_state = m[1] if m else ""
        street, rest = (clean(p.get("PROPERTY_ADDRESS")).rsplit(",", 1) + [""])[:2] if p else (sigs[0]["address"], "")
        zm = re.search(r"(\d{5})", rest)
        zip_ = zm[1] if zm else sigs[0]["zip"]
        types = sorted({s["label"] for s in opened}, key=lambda t: -max(s["points"] for s in opened if s["label"] == t))
        score = max(s["points"] for s in opened)
        reasons = [f"{types[0]} (+{score})"]
        if len(types) > 1:
            score += 10 * min(len(types) - 1, 2); reasons.append(f"{len(types)} different signals (+{10 * min(len(types) - 1, 2)})")
        n_req = sum(1 for s in opened if s["source"] == "request")
        if n_req >= 2:
            score += min(5 * (n_req - 1), 15); reasons.append(f"{n_req} complaints (+{min(5 * (n_req - 1), 15)})")
        if mail_state and mail_state != "OH":
            score += 15; reasons.append("owner mails out of state (+15)")
        elif mailing and addr_key(mailing.split(",")[0]) != addr_key(street):
            score += 10; reasons.append("absentee owner (+10)")
        if oc == "individual":
            score += 10; reasons.append("individual owner (+10)")
        elif oc == "institutional":
            score -= 15; reasons.append("institutional owner (-15)")
        dates = sorted(s["date"] for s in opened if s["date"])
        first_seen = state.get(key) or today.isoformat()
        state[key] = first_seen
        pid = clean(p.get("PARID"))
        leads.append({
            "lead_id": key, "property_address": street.strip(), "city": "TOLEDO", "state": "OH", "zip": zip_,
            "parcel": pid, "owner_name": owner, "owner_is_entity": oc in ("entity", "institutional"),
            "owner_class": oc, "mailing_address": mailing, "out_of_state_owner": bool(mail_state) and mail_state != "OH",
            "land_use": clean(p.get("LUC")), "lead_types": types, "open_records": len(opened),
            "case_numbers": sorted({s["id"] for s in opened if s["id"]}),
            "cases_by_source": {src: sorted({s["id"] for s in opened if s["source"] == src})
                                for src in ("request", "mowing", "demolition")},
            "oldest_open_days": (today - date.fromisoformat(dates[0])).days if dates else None,
            "latest_date": dates[-1] if dates else "", "total_fines": 0,
            "notes": sorted({s["note"] for s in opened if s["note"]})[:3],
            "in_foreclosure": False, "score": max(0, min(100, score)), "score_reasons": reasons,
            "auditor_url": config.AUDITOR_URL.format(pin=pid) if pid else "",
            "added_date": first_seen, "last_seen": today.isoformat(),
        })
    leads.sort(key=lambda r: -r["score"])
    return leads


def export_ghl(leads: list[dict]) -> int:
    rows = [r for r in leads if r["owner_name"]]
    with config.GHL_CSV.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["First Name", "Last Name", "Owner Name", "Mailing Address", "Property Address", "Property City",
                    "Property Zip", "Parcel ID", "Signals", "Score", "Latest Date", "Auditor URL", "Tags"])
        for r in rows:
            o = r["owner_name"]
            if r["owner_is_entity"]:
                first, last = "", o.title()
            else:
                parts = re.sub(r"(\s+(AND|ET AL)\b|[&,]).*$", "", o).split()
                first, last = (parts[1].title(), parts[0].title()) if len(parts) > 1 else ("", o.title())
            tags = ["code violation", "toledo", "lucas county"] + [t.lower() for t in r["lead_types"]]
            if r["out_of_state_owner"]:
                tags.append("out of state owner")
            w.writerow([first, last, o.title(), r["mailing_address"], r["property_address"], "Toledo", r["zip"],
                        r["parcel"], "; ".join(r["lead_types"]), r["score"], r["latest_date"], r["auditor_url"],
                        ",".join(tags)])
    return len(rows)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    config.DATA.mkdir(exist_ok=True)
    today = date.today()
    try:
        state = json.loads(config.STATE_FILE.read_text())
    except (FileNotFoundError, ValueError):
        state = {}
    signals = collect(today)
    by_pid, by_addr = parcel_rows(signals)
    leads = build(signals, by_pid, by_addr, state, today)
    keep = {r["lead_id"] for r in leads}
    state = {k: v for k, v in state.items() if k in keep}
    config.STATE_FILE.write_text(json.dumps(state, separators=(",", ":")))
    with_owner = sum(1 for r in leads if r["owner_name"])
    meta = {"updated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"), "signals": len(signals),
            "leads": len(leads), "with_owner": with_owner,
            "by_source": {s: sum(1 for r in leads if r["cases_by_source"][s]) for s in ("request", "mowing", "demolition")}}
    config.DASHBOARD_JSON.write_text(json.dumps({"meta": meta, "leads": leads}, separators=(",", ":")))
    n = export_ghl(leads)
    log.info("Done: %d signals -> %d leads (%d with owner), %s, GHL rows %d",
             len(signals), len(leads), with_owner, meta["by_source"], n)


if __name__ == "__main__":
    main()
