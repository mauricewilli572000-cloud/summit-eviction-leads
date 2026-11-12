from datetime import date

import run_pipeline as rp


def test_address_helpers():
    assert rp.split_location("1057 KING ST,  TOLEDO,  OH,  43607") == ("1057 KING ST", "43607")
    assert rp.addr_key("1057 King Street Apt 2") == "1057 KING ST"
    assert rp.owner_class("CITY OF TOLEDO") == "government"
    assert rp.owner_class("SMITH HOMES LLC") == "entity"
    assert rp.owner_class("RIPARIAN VPC OHIO SFR PORTFOLIO LLC") == "institutional"
    assert rp.owner_class("DEVOE KENNETH") == "individual"


def sig(**kw):
    base = {"source": "request", "label": "High grass", "points": 10, "date": "2026-10-01", "open": True,
            "id": "SR1", "address": "707 PALMWOOD AVE", "zip": "43604", "parcel": "", "status": "IP", "note": ""}
    return {**base, **kw}


def test_build_groups_by_parcel():
    row = {"PARID": "0100044", "OWNER": "DEVOE KENNETH", "PROPERTY_ADDRESS": "707 PALMWOOD AVE, TOLEDO OH 43604",
           "MAILING_ADDRESS": "2540 MONROE ST # 107C, TOLEDO OH 43620", "LUC": "510"}
    by_pid = {"0100044": row}
    by_addr = {"707 PALMWOOD AVE|43604": row, "707 PALMWOOD AVE|": row}
    signals = [sig(), sig(id="SR2", label="Vacant house (trespassing)", points=30),
               sig(source="mowing", label="City mows it (owner neglect)", points=25, id="CE1", parcel="0100044")]
    leads = rp.build(signals, by_pid, by_addr, {}, date(2026, 11, 12))
    assert len(leads) == 1
    r = leads[0]
    assert r["lead_id"] == "P:0100044" and r["open_records"] == 3 and r["lead_types"][0] == "Vacant house (trespassing)"
    assert r["score"] == 30 + 20 + 5 + 10 + 10 and r["oldest_open_days"] == 42


def test_build_drops_government_and_closed():
    row = {"PARID": "1", "OWNER": "CITY OF TOLEDO", "PROPERTY_ADDRESS": "1 MAIN ST, TOLEDO OH 43604"}
    assert rp.build([sig(address="1 MAIN ST", parcel="1")], {"1": row}, {}, {}, date(2026, 11, 12)) == []
    assert rp.build([sig(open=False)], {}, {}, {}, date(2026, 11, 12)) == []
