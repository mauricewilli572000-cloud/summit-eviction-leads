"""Tiny ArcGIS REST client: paged queries and batched IN-list lookups."""
from __future__ import annotations

import logging
import time

from curl_cffi import requests

log = logging.getLogger(__name__)
_S = requests.Session(impersonate="chrome")


def _get(url: str, params: dict) -> dict:
    params = {**params, "f": "json"}
    for attempt in range(4):
        try:
            j = _S.get(url, params=params, timeout=120).json()
            if "error" in j:
                raise RuntimeError(j["error"])
            return j
        except Exception as e:  # network / server hiccup: back off and retry
            log.warning("query %s failed (%s), attempt %d", url[-60:], e, attempt + 1)
            time.sleep(10 * (attempt + 1))
    raise RuntimeError(f"ArcGIS query failed: {url}")


def layer_info(layer_url: str) -> dict:
    return _get(layer_url, {})


def query_all(layer_url: str, where: str, fields: str, page: int = 2000, order: str = "") -> list[dict]:
    out, offset = [], 0
    while True:
        p = {"where": where, "outFields": fields, "returnGeometry": "false",
             "resultOffset": offset, "resultRecordCount": page}
        if order:
            p["orderByFields"] = order
        feats = _get(layer_url + "/query", p).get("features", [])
        out += [f["attributes"] for f in feats]
        if len(feats) < page:
            return out
        offset += page


def query_in(layer_url: str, field: str, values: list[str], fields: str, batch: int = 150) -> list[dict]:
    out = []
    vals = sorted(set(v for v in values if v))
    for i in range(0, len(vals), batch):
        chunk = ",".join("'" + v.replace("'", "''") + "'" for v in vals[i:i + batch])
        out += query_all(layer_url, f"{field} IN ({chunk})", fields)
    return out
