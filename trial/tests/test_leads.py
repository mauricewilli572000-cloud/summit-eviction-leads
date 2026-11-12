from src import leads
from run_pipeline import split_name

G = {"parcel": "0100044", "owner": "DEVOE KENNETH", "class": "R", "landuse": "510", "certyr": 2018,
     "taxdue": 15255.62, "total": 30000}
PA = {"PARID": "0100044", "OWNER": "DEVOE KENNETH", "PROPERTY_ADDRESS": "707 PALMWOOD AVE, TOLEDO OH 43604",
      "MAILING_ADDRESS": "2540 MONROE ST # 107C, TOLEDO OH 43620", "CLASS": "R", "LUC": "510"}
CAMA = {"TOTALVALUE": 30000, "RESYRBLT": 1910, "COND_DESC": "POOR", "SITECITY": "TOLEDO", "SITEZIP": "43604"}


def make(g=None, pa=None, cama=None, rental=False):
    return leads.build({**G, **(g or {})}, {**PA, **(pa or {})} if pa != {} else {}, {**CAMA, **(cama or {})}, rental, 2025)


def test_good_lead():
    r, why = make(rental=True)
    assert not why and r["years_owed"] == 8 and r["absentee_owner"] and r["condition"] == "Poor"
    assert r["mailing_address"] == "2540 MONROE ST # 107C" and r["mailing_zip"] == "43620"
    assert r["property_address"] == "707 PALMWOOD AVE" and r["tier"] == "Hot"


def test_filters():
    assert make(g={"taxdue": 900})[1] == "small balance"
    assert make(g={"certyr": 2025})[1] == "under 2 years behind"
    assert make(pa={"OWNER": "MALONE DARIUS"})[1] == "owner changed since snapshot"
    assert make(g={"owner": "LUCAS COUNTY LAND REUTILIZATION CORP"},
                pa={"OWNER": "LUCAS COUNTY LAND REUTILIZATION CORP"})[1] == "government / church / bank owner"
    assert make(pa={"CLASS": "E"})[1] == "exempt / utility"
    assert make(pa={})[1] == "parcel retired"


def test_flags():
    r, _ = make(pa={"MAILING_ADDRESS": "707 PALMWOOD AVE, TOLEDO OH 43604"})
    assert not r["absentee_owner"]
    r, _ = make(pa={"MAILING_ADDRESS": "1025 CATHEDRAL ST # 513, BALTIMORE MD 21201"})
    assert r["out_of_state"]
    r, _ = make(pa={"LUC": "500"}, g={"landuse": "500"})
    assert r["vacant"] and r["tier"] != "Hot"
    assert leads.same_owner("GOEL PUNEET & NEENA (ORSURVTC)", "GOEL PUNEET & NEENA")


def test_split_name():
    assert split_name("DEVOE KENNETH") == ("Kenneth", "Devoe")
