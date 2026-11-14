"""Self checks for fingerprint_files.py. Run: python3 test_fingerprint.py"""
import csv, gzip, hashlib, json, os, sys, tempfile, zipfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fingerprint_files as ff

results = []
def check(name, ok, detail=""):
    results.append(ok)
    print(("PASS" if ok else "FAIL"), "|", name, "|", detail)

d = tempfile.mkdtemp()
def P(n): return os.path.join(d, n)

# a csv with a quoted newline inside a field: 3 records, 5 physical lines
with open(P("a.csv"), "w", newline="") as f:
    w = csv.writer(f); w.writerow(["h1", "h2"]); w.writerow(["x", "line one\nline two"]); w.writerow(["y", "z"]); w.writerow(["q", "r"])
check("T1 csv counts records, not lines, and skips the header", ff.count_rows(P("a.csv"))[0] == 3, f"{ff.count_rows(P('a.csv'))[0]}")

with gzip.open(P("b.csv.gz"), "wt", newline="") as f:
    w = csv.writer(f); w.writerow(["h"]); [w.writerow([i]) for i in range(10)]
check("T2 gzipped csv", ff.count_rows(P("b.csv.gz"))[0] == 10)

with zipfile.ZipFile(P("c.zip"), "w") as z:
    z.writestr("one.csv", "h\n1\n2\n3\n"); z.writestr("two.csv", "h\n1\n2\n"); z.writestr("readme.txt", "ignore me")
n, note, members = ff.count_rows(P("c.zip"))
check("T3 zip sums csv members only and lists them", n == 5 and len(members) == 2, f"rows={n} members={members}")

with open(P("d.jsonl"), "w") as f:
    f.write('{"a":1}\n\n{"a":2}\n{"a":3}\n')
check("T4 jsonl ignores blank lines", ff.count_rows(P("d.jsonl"))[0] == 3)

try:
    import pyarrow as pa, pyarrow.parquet as pq
    pq.write_table(pa.table({"x": list(range(1234))}), P("e.parquet"))
    check("T5 parquet row count from the footer", ff.count_rows(P("e.parquet"))[0] == 1234)
except ImportError:
    check("T5 parquet (skipped, pyarrow missing)", True, "skipped")

open(P("f.bin"), "wb").write(b"abc")
r = ff.count_rows(P("f.bin"))
check("T6 unknown format gives no count and a note", r[0] is None and "not recognised" in r[1])

open(P("g.csv"), "wb").write(b"")
check("T7 empty csv counts zero", ff.count_rows(P("g.csv"))[0] == 0)

check("T8 sha256 matches the standard library", ff.sha256_of(P("f.bin")) == hashlib.sha256(b"abc").hexdigest())

out = P("m")
ff.main([d, "--out", out, "--download-date", "2026-11-10", "--source", "test", "--role", "D1"])
m = json.load(open(out + ".json"))
names = sorted(e["file"] for e in m["files"])
check("T9 manifest lists every file with its role, source and date",
      len(m["files"]) >= 7 and m["role"] == "D1" and m["download_date"] == "2026-11-10" and "a.csv" in names,
      f"{len(m['files'])} files")
check("T10 manifest records the tool's own fingerprint", len(m["tool_sha256"]) == 64)

secret = "SECRET_VALUE_123"
open(P("h.csv"), "w").write("h\n" + secret + "\n")
import io, contextlib
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    ff.main([P("h.csv"), "--out", P("m2")])
check("T11 no value from a file is printed or stored", secret not in buf.getvalue() and secret not in open(P("m2.json")).read() and secret not in open(P("m2.csv")).read())

open(P("bad.zip"), "wb").write(b"not a zip")
r = ff.count_rows(P("bad.zip"))
check("T12 a damaged file is reported, not hidden", r[0] is None and "could not count" in r[1], r[1][:50])

print(f"\n{sum(results)} of {len(results)} checks passed")
sys.exit(0 if all(results) else 1)
