"""Tiny ArcGIS REST client: paged queries and batched IN-list lookups."""
from __future__ import annotations

import logging
import time

from curl_cffi import requests

log = logging.getLogger(__name__)
_S = requests.Session(impersonate="chrome")


class ServerError(RuntimeError):
    """The server answered with an ArcGIS error (bad query etc.): retrying won't help."""


def _get(url: str, params: dict) -> dict:
    params = {**params, "f": "json"}
    for attempt in range(4):
        try:
            # POST: long IN (...) lists overflow the URL limit
            r = _S.post(url, data=params, timeout=120) if url.endswith("/query") else \
                _S.get(url, params=params, timeout=120)
            j = r.json()
        except Exception as e:  # network / server hiccup: back off and retry
            log.warning("query %s failed (%s), attempt %d", url[-60:], e, attempt + 1)
            time.sleep(10 * (attempt + 1))
            continue
        if "error" in j:
            if (j["error"].get("code") or 0) >= 500 and attempt < 3:
                time.sleep(10 * (attempt + 1))
                continue
            raise ServerError(j["error"])
        return j
    raise RuntimeError(f"ArcGIS query failed: {url}")


def layer_info(layer_url: str) -> dict:
    return _get(layer_url, {})


def _by_ids(layer_url: str, where: str, fields: str) -> list[dict]:
    """For layers without pagination: fetch object IDs, then the rows in chunks."""
    ids = sorted(_get(layer_url + "/query", {"where": where, "returnIdsOnly": "true"}).get("objectIds") or [])
    out = []
    for i in range(0, len(ids), 500):
        out += [f["attributes"] for f in _get(layer_url + "/query", {
            "objectIds": ",".join(map(str, ids[i:i + 500])), "outFields": fields,
            "returnGeometry": "false"}).get("features", [])]
    return out


def query_all(layer_url: str, where: str, fields: str, page: int = 1000, order: str = "") -> list[dict]:
    out, offset = [], 0
    while True:
        p = {"where": where, "outFields": fields, "returnGeometry": "false",
             "resultOffset": offset, "resultRecordCount": page}
        if order:
            p["orderByFields"] = order
        try:
            feats = _get(layer_url + "/query", p).get("features", [])
        except ServerError as e:
            if "pagination" in str(e).lower() and offset == 0:
                return _by_ids(layer_url, where, fields)
            raise
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
