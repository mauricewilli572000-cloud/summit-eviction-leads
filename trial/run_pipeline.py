"""Lucas County (Toledo) tax delinquent leads from the County Auditor's public GIS layers.

The tax balances are an annual Auditor snapshot; each weekly run re-checks today's owner and
mailing address so sold or forfeited parcels drop out.
"""
from __future__ import annotations

import argparse
import csv
import json
import logging
import re
from datetime import date, datetime, timedelta, timezone

import config
from collections import Counter

from src import arcgis, leads

log = logging.getLogger("lucas-tax")

GHL_COLUMNS = ["First Name", "Last Name", "Owner Name", "Owner Name 2", "Mailing Address", "Mailing City",
               "Mailing State", "Mailing Zip", "Property Address", "Property City", "Property Zip",
               "Property Category", "Property Type", "Lead Type", "Amount Owed", "Years Owed",
               "Condition", "Market Value", "Last Sale Date", "Score", "Tier", "Parcel ID",
               "Absentee", "Date Added", "Auditor URL", "Tags"]


def _load(path, default):
    try:
        return json.loads(path.read_text())
    except (FileNotFoundError, ValueError):
        return default


def split_name(owner: str) -> tuple[str, str]:
    """Auditor names are 'LAST FIRST M'. Companies go entirely in last name."""
    if leads.COMPANY.search(owner) or leads.TRUST.search(owner) or leads.ESTATE.search(owner):
        return "", owner.title()
    parts = re.sub(r"(\s+(AND|ET AL)\b|[&,]).*$", "", owner).split()
    if len(parts) < 2:
        return "", owner.title()
    return parts[1].title(), parts[0].title()


def export_ghl(records: list[dict]) -> int:
    rows = sorted((r for r in records if r["status"] == "active" and r["property_address"]),
                  key=lambda r: -r["score"])
    with config.GHL_CSV.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(GHL_COLUMNS)
        for r in rows:
            first, last = split_name(r["owner_name"])
            tags = ["tax delinquent", "lucas county", r["tier"].lower(), r["property_category"].lower()]
            tags += [t for t, on in (("absentee", r["absentee_owner"]), ("llc", r["company_owner"]),
                                     ("vacant land", r["vacant"]), ("rental", r["rental_registered"])) if on]
            w.writerow([first, last, r["owner_name"].title(), r["owner_name_2"].title(),
                        r["mailing_address"] or r["property_address"],
                        (r["mailing_city"] or r["property_city"]).title(), r["mailing_state"] or "OH",
                        r["mailing_zip"] or r["property_zip"], r["property_address"],
                        r["property_city"].title(), r["property_zip"], r["property_category"],
                        r["property_type"], "Tax Delinquent", f"{r['amount_owed']:.2f}", r["years_owed"],
                        r["condition"], f"{r['market_value']:.0f}", r["last_sale_date"],
                        r["score"], r["tier"], r["doc_num"], "Yes" if r["absentee_owner"] else "No",
                        r["date_added"], r["auditor_url"], ",".join(tags)])
    return len(rows)


def main(force: bool = False) -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    config.DATA.mkdir(exist_ok=True)
    state = _load(config.STATE_FILE, {})
    info = arcgis.layer_info(config.COLLECTIONS)
    edited = (info.get("editingInfo") or {}).get("lastEditDate") or 0
    snap = datetime.fromtimestamp(edited / 1000, timezone.utc).date() if edited else date.today()
    snapshot_year = snap.year
    log.info("Auditor tax-balance snapshot: %s", snap)

    where = f"taxdue >= {config.MIN_OWED:.0f} AND certyr > 0 AND certyr <= {snapshot_year - config.MIN_YEARS + 1}"
    rows = arcgis.query_all(config.COLLECTIONS, where,
                            "parcel,owner,class,landuse,certyr,taxdue,total", order="objectid_1")
    log.info("Delinquent parcels in snapshot (filtered): %d", len(rows))
    pids = [str(r["parcel"]).strip() for r in rows]
    pa = {r["PARID"]: r for r in arcgis.query_in(
        config.PARCEL_ADDR, "PARID", pids, "PARID,OWNER,PROPERTY_ADDRESS,MAILING_ADDRESS,CLASS,LUC")}
    cama = {r["PARCELID"]: r for r in arcgis.query_in(
        config.CAMA, "PARCELID", pids, "PARCELID,SITECITY,SITEZIP,TOTALVALUE,RESYRBLT,COND_DESC")}
    rentals = {str(r.get("PARID") or r.get("Parcel_No") or "").strip() for r in arcgis.query_all(
        config.RENTALS, "1=1", "PARID,Parcel_No")}
    log.info("Live owner rows %d, CAMA rows %d, rentals %d", len(pa), len(cama), len(rentals))

    today = date.today().isoformat()
    old = {r["doc_num"]: r for r in _load(config.RECORDS_FILE, [])}
    fresh, skipped = {}, Counter()
    for g in rows:
        pid = str(g["parcel"]).strip()
        lead, why = leads.build(g, pa.get(pid, {}), cama.get(pid, {}), pid in rentals, snapshot_year)
        if lead is None:
            skipped[why] += 1
            continue
        prev = old.get(pid, {})
        lead["date_added"] = prev.get("date_added") if prev.get("status") == "active" else today
        lead.update(last_seen=today, status="active", removed_date="")
        fresh[pid] = lead
    log.info("Skipped: %s", dict(skipped))

    cutoff = (date.today() - timedelta(days=config.REMOVED_KEEP_DAYS)).isoformat()
    removed = 0
    for pid, r in old.items():
        if pid in fresh:
            continue
        if r["status"] == "active":           # paid, sold or forfeited since the last run
            r.update(status="removed", removed_date=today)
            removed += 1
        if r["removed_date"] >= cutoff:
            fresh[pid] = r
    records = sorted(fresh.values(), key=lambda r: (r["status"] != "active", -r["score"]))
    active = [r for r in records if r["status"] == "active"]

    config.RECORDS_FILE.write_text(json.dumps(records, separators=(",", ":")))
    meta = {"county": "Lucas", "lead_type": "Tax Delinquent", "source": config.COLLECTIONS,
            "snapshot": snap.isoformat(),
            "generated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
            "active": len(active), "hot": sum(r["tier"] == "Hot" for r in active),
            "warm": sum(r["tier"] == "Warm" for r in active), "tax_foreclosure": 0,
            "removed": removed, "filtered_out": sum(skipped.values()), "skipped": dict(skipped),
            "added_this_run": sum(r["date_added"] == today for r in active),
            "filters": f"${config.MIN_OWED:,.0f}+ owed, {config.MIN_YEARS}+ years behind, owner unchanged "
                       "since the Auditor snapshot; no government, church, bank or land bank owners"}
    config.DASHBOARD_JSON.write_text(json.dumps({"meta": meta, "records": records}, separators=(",", ":")))
    n = export_ghl(records)
    state.update(snapshot=snap.isoformat(), run=today)
    config.STATE_FILE.write_text(json.dumps(state, indent=1))
    log.info("Done: %d active (hot %d, warm %d), %d filtered out, %d removed, GHL rows %d",
             meta["active"], meta["hot"], meta["warm"], meta["filtered_out"], removed, n)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="(kept for the workflow input; every run is full)")
    main(ap.parse_args().force)
