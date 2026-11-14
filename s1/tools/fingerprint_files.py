"""Fingerprint and count the files for registered test S1 (step 4 of the run plan).

What it does
    For every file it is given, it records the file name, size in bytes, SHA256, and the
    number of data rows. It writes a manifest as JSON and CSV.

What it does not do
    It never prints, stores or analyses any value from the files. Row counting only counts
    records. No timestamps, latencies or outcomes are read, so running it does not count as
    looking at the data under the pre registration.

Row counting by format
    .csv, .tsv           records after the header, using the csv module (quoted newlines are safe)
    .csv.gz, .tsv.gz     the same, through gzip
    .zip                 every csv or tsv member inside, counted and summed, member names listed
    .jsonl, .ndjson      non empty lines
    .parquet             the row count stored in the file footer (needs pyarrow); no rows are read
    anything else        row_count is left empty and a note says why

Usage
    python3 fingerprint_files.py PATH [PATH ...] --out manifest --download-date 2026-11-10 \\
        --source "huggingface dataset revision <commit hash>" --role D1

Licence: MIT. Standard library only, except optional pyarrow for parquet.
"""
from __future__ import annotations

import argparse
import csv
import datetime
import gzip
import hashlib
import io
import json
import os
import sys
import zipfile

VERSION = "1.0"
CHUNK = 1024 * 1024


def sha256_of(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(CHUNK)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def _count_csv(stream, delimiter: str) -> int:
    text = io.TextIOWrapper(stream, encoding="utf-8", newline="", errors="replace")
    reader = csv.reader(text, delimiter=delimiter)
    n = -1  # the first record is the header
    for _ in reader:
        n += 1
    return max(n, 0)


def _count_lines(stream) -> int:
    n = 0
    for line in stream:
        if line.strip():
            n += 1
    return n


def count_rows(path: str):
    """Return (row_count or None, note, members or None)."""
    low = path.lower()
    try:
        if low.endswith((".csv", ".tsv")):
            with open(path, "rb") as f:
                return _count_csv(f, "\t" if low.endswith(".tsv") else ","), "", None
        if low.endswith((".csv.gz", ".tsv.gz")):
            with gzip.open(path, "rb") as f:
                return _count_csv(f, "\t" if low.endswith(".tsv.gz") else ","), "", None
        if low.endswith((".jsonl", ".ndjson")):
            with open(path, "rb") as f:
                return _count_lines(f), "", None
        if low.endswith((".jsonl.gz", ".ndjson.gz")):
            with gzip.open(path, "rb") as f:
                return _count_lines(f), "", None
        if low.endswith(".zip"):
            total, members = 0, []
            with zipfile.ZipFile(path) as z:
                for info in z.infolist():
                    name = info.filename
                    ln = name.lower()
                    if info.is_dir() or not ln.endswith((".csv", ".tsv")):
                        continue
                    with z.open(info) as f:
                        n = _count_csv(f, "\t" if ln.endswith(".tsv") else ",")
                    members.append({"member": name, "rows": n})
                    total += n
            if not members:
                return None, "zip holds no csv or tsv member", []
            return total, "", members
        if low.endswith(".parquet"):
            try:
                import pyarrow.parquet as pq
            except ImportError:
                return None, "pyarrow not installed; run: pip install pyarrow", None
            return int(pq.ParquetFile(path).metadata.num_rows), "", None
    except Exception as e:  # a damaged file must be reported, not hidden
        return None, f"could not count rows: {type(e).__name__}: {e}", None
    return None, "format not recognised for row counting", None


def collect(paths):
    out = []
    for p in paths:
        if os.path.isdir(p):
            for root, _dirs, files in os.walk(p):
                for name in sorted(files):
                    out.append(os.path.join(root, name))
        elif os.path.isfile(p):
            out.append(p)
        else:
            raise SystemExit(f"not found: {p}")
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("paths", nargs="+", help="files or folders")
    ap.add_argument("--out", default="manifest", help="output name without extension")
    ap.add_argument("--download-date", default=None, help="date the files were downloaded, YYYY-MM-DD")
    ap.add_argument("--source", default="", help="where the files came from, including any revision hash")
    ap.add_argument("--role", default="", help="D1 or D2")
    a = ap.parse_args(argv)

    files = collect(a.paths)
    base = os.path.commonpath([os.path.dirname(os.path.abspath(f)) for f in files]) if files else "."
    me = os.path.abspath(__file__)
    manifest = {
        "tool": "fingerprint_files.py",
        "tool_version": VERSION,
        "tool_sha256": sha256_of(me),
        "created_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "download_date": a.download_date or "",
        "role": a.role,
        "source": a.source,
        "note": "Counts only. No value in any file was read, printed or stored.",
        "files": [],
    }
    for f in files:
        rows, note, members = count_rows(f)
        entry = {
            "file": os.path.relpath(os.path.abspath(f), base),
            "bytes": os.path.getsize(f),
            "sha256": sha256_of(f),
            "rows": rows,
            "note": note,
        }
        if members is not None:
            entry["members"] = members
        manifest["files"].append(entry)
        print(f"{entry['file']}  bytes={entry['bytes']}  rows={rows}  sha256={entry['sha256'][:16]}...  {note}")

    with open(a.out + ".json", "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2)
    with open(a.out + ".csv", "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["file", "bytes", "rows", "sha256", "note", "role", "source", "download_date"])
        for e in manifest["files"]:
            w.writerow([e["file"], e["bytes"], "" if e["rows"] is None else e["rows"], e["sha256"],
                        e["note"], a.role, a.source, a.download_date or ""])
    print(f"wrote {a.out}.json and {a.out}.csv for {len(files)} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
