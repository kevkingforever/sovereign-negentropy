"""Adapters: provider files to Rows (arrival, completion). Amendments A1, A1.1 and A2.

D2 (Ethereum, Flashbots Mempool Dumpster): arrival is timestamp_ms, completion is
included_block_timestamp_ms (A1 section 3.4). A transaction with no inclusion time is unresolved
(completion nan). Times are in seconds. Only these two columns are read.
"""
from __future__ import annotations

import hashlib
import json
import os
import zipfile

import numpy as np
import pandas as pd

ARRIVAL_COL = "timestamp_ms"
COMPLETION_COL = "included_block_timestamp_ms"
EXPECTED_HEADER = ("timestamp_ms,hash,chain_id,from,to,value,nonce,gas,gas_price,gas_tip_cap,gas_fee_cap,"
                   "data_size,data_4bytes,sources,included_at_block_height,included_block_timestamp_ms,"
                   "inclusion_delay_ms,tx_type")


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def verify_manifest(folder: str, manifest: dict) -> list:
    """Return the list of files that are missing or whose SHA256 differs from the manifest."""
    bad = []
    for e in manifest["files"]:
        p = os.path.join(folder, e["file"])
        if not os.path.exists(p) or sha256_file(p) != e["sha256"]:
            bad.append(e["file"])
    return bad


def read_d2_day(path: str) -> dict:
    """One daily zip. Returns arrival and completion in seconds, plus counts of how the
    inclusion field was filled (empty, zero or negative, or a time)."""
    with zipfile.ZipFile(path) as z:
        names = [n for n in z.namelist() if n.lower().endswith(".csv")]
        if len(names) != 1:
            raise ValueError(f"{path}: expected one csv member, found {len(names)}")
        with z.open(names[0]) as f:
            df = pd.read_csv(f, usecols=[ARRIVAL_COL, COMPLETION_COL],
                             dtype={ARRIVAL_COL: "int64", COMPLETION_COL: "float64"})
    arr = df[ARRIVAL_COL].to_numpy(dtype=float) / 1000.0
    inc = df[COMPLETION_COL].to_numpy(dtype=float)
    empty = np.isnan(inc)
    nonpos = (~empty) & (inc <= 0)
    comp = np.where(empty | nonpos, np.nan, inc / 1000.0)
    return dict(arr=arr, comp=comp, n=int(len(df)), n_empty=int(empty.sum()), n_nonpositive=int(nonpos.sum()))


def load_d2(folder: str, manifest: dict) -> dict:
    """All files in manifest order. The caller must have verified the manifest first."""
    arrs, comps, per_file = [], [], []
    for e in manifest["files"]:
        r = read_d2_day(os.path.join(folder, e["file"]))
        arrs.append(r["arr"]); comps.append(r["comp"])
        per_file.append(dict(file=e["file"], n=r["n"], n_empty=r["n_empty"], n_nonpositive=r["n_nonpositive"]))
    return dict(arr=np.concatenate(arrs), comp=np.concatenate(comps), per_file=per_file)
