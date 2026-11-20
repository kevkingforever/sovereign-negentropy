"""Sample baseline report on public Ethereum data (D2). Tests no hypothesis.

Shows the format of a per window delay report: percentiles by hour of day, by day, the unresolved
share and the slowest windows. Uses the engine's log bins (1 ms to 1000 s, 40 per decade), the
engine's suppression rule (groups under 50 are not reported) and the S1 reader (s1.adapters).
Arrival is the first time the observer saw the transaction. Completion is the inclusion block time.
Only two timestamps exist in this dataset, so this is an end to end figure, not a stage figure.
Aggregates only. No row level output.
"""
from __future__ import annotations
import argparse, json, math, os, sys
import numpy as np

W = 300.0          # window seconds, as fixed in Amendment A3
K_MIN = 50         # suppression threshold, as in the engine
LO, HI, PER_DEC = 1e-3, 1e3, 40
NB = int(round(math.log10(HI / LO) * PER_DEC))   # 240 bins
KK = PER_DEC / math.log(10.0)


def bin_index(x):
    x = np.clip(x, LO, HI)
    i = (np.log(x / LO) * KK).astype(np.int64)
    return np.minimum(i, NB - 1)


def centre(i):
    return LO * 10.0 ** ((i + 0.5) / PER_DEC)


def quantile(hist, q):
    n = int(hist.sum())
    if n < K_MIN:
        return None
    c = np.cumsum(hist)
    i = int(np.searchsorted(c, q * n, side="left"))
    return float(centre(min(i, NB - 1)))


def run(folder, manifest_path, out, adapters):
    sys.path.insert(0, adapters)
    from s1.adapters import read_d2_day, verify_manifest
    man = json.load(open(manifest_path))
    bad = verify_manifest(folder, man)
    if bad:
        raise SystemExit(f"Manifest check failed for: {bad}. Stop.")
    os.makedirs(out, exist_ok=True)
    first = read_d2_day(os.path.join(folder, man["files"][0]["file"]))
    w0 = int(np.floor(first["arr"].min() / W))
    nw = 28 * 288 + 1200
    H = np.zeros((nw, NB), dtype=np.int64)
    n_all = np.zeros(nw, dtype=np.int64)
    n_unres = np.zeros(nw, dtype=np.int64)
    rows = resolved = clipped = 0
    for e in man["files"]:
        r = read_d2_day(os.path.join(folder, e["file"]))
        arr, comp = r["arr"], r["comp"]
        w = np.floor(arr / W).astype(np.int64) - w0
        keep = (w >= 0) & (w < nw)
        arr, comp, w = arr[keep], comp[keep], w[keep]
        ok = ~np.isnan(comp)
        d = comp[ok] - arr[ok]
        clipped += int((d < LO).sum())
        d = np.maximum(d, LO)
        rows += len(arr); resolved += int(ok.sum())
        n_all += np.bincount(w, minlength=nw)
        n_unres += np.bincount(w[~ok], minlength=nw)
        H += np.bincount(w[ok] * NB + bin_index(d), minlength=nw * NB).reshape(nw, NB)
        print("read", e["file"], len(arr), flush=True)
    nres = H.sum(axis=1)
    starts = (np.arange(nw) + w0) * W
    day = ((starts - starts[nres > 0].min()) // 86400).astype(int)
    hod = ((starts % 86400) // 3600).astype(int)
    day0 = float(starts[nres > 0].min())

    def pooled(mask):
        h = H[mask].sum(axis=0)
        n = int(h.sum())
        return dict(n=n, p50=quantile(h, .5), p90=quantile(h, .9), p99=quantile(h, .99))

    overall = pooled(nres > 0)
    overall.update(rows=rows, resolved=resolved, unresolved=rows - resolved,
                   unresolved_share=(rows - resolved) / rows, clipped=clipped, clipped_share=clipped / resolved)
    by_day = []
    for d in range(int(day.max()) + 1):
        m = (day == d) & (nres > 0)
        if m.sum() == 0:
            continue
        p = pooled(m)
        tot = int(n_all[m].sum()); un = int(n_unres[m].sum())
        p.update(day=d + 1, arrivals=tot, unresolved_share=un / tot if tot else None)
        by_day.append(p)
    by_hour = []
    for h in range(24):
        m = (hod == h) & (nres > 0)
        p = pooled(m); p["hour_utc"] = h
        tot = int(n_all[m].sum()); un = int(n_unres[m].sum())
        p["unresolved_share"] = un / tot if tot else None
        by_hour.append(p)
    wins = []
    for i in np.where(nres >= K_MIN)[0]:
        wins.append(dict(window_start_utc_seconds=float(starts[i]), n=int(nres[i]), p99=quantile(H[i], .99), p50=quantile(H[i], .5)))
    wins.sort(key=lambda x: -x["p99"])
    result = dict(window_seconds=W, k_min=K_MIN, windows_reported=len(wins), windows_total=int((nres > 0).sum()),
                  overall=overall, by_day=by_day, by_hour=by_hour, slowest_windows=wins[:10],
                  day_one_start_utc_seconds=day0)
    json.dump(result, open(os.path.join(out, "sample_report_data.json"), "w"), indent=1)
    import csv
    for name, rows_, cols in (("by_hour", by_hour, ["hour_utc", "n", "p50", "p90", "p99", "unresolved_share"]),
                              ("by_day", by_day, ["day", "n", "p50", "p90", "p99", "unresolved_share"])):
        with open(os.path.join(out, f"sample_report_{name}.csv"), "w", newline="") as f:
            wr = csv.writer(f); wr.writerow(cols)
            for r_ in rows_:
                wr.writerow([r_[c] for c in cols])
    charts(result, H.sum(axis=0), out)
    write_md(result, out)
    print("done", out)


def charts(res, hist, out):
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    navy, teal, grey = "#1f3a5f", "#2a9d8f", "#8a8f98"
    h = res["by_hour"]
    fig, ax = plt.subplots(figsize=(7.5, 3.6), dpi=160)
    xs = [r["hour_utc"] for r in h]
    for k, c, lab in (("p50", teal, "Median"), ("p90", navy, "90th percentile"), ("p99", grey, "99th percentile")):
        ax.plot(xs, [r[k] for r in h], color=c, lw=2, label=lab)
    ax.set_yscale("log"); ax.set_xlabel("Hour of day (UTC)"); ax.set_ylabel("Delay, seconds")
    ax.set_title("Arrival to inclusion delay by hour of day, 28 days pooled"); ax.legend(frameon=False)
    ax.spines[["top", "right"]].set_visible(False); fig.tight_layout(); fig.savefig(os.path.join(out, "chart_by_hour.png")); plt.close(fig)
    d = res["by_day"]
    fig, ax = plt.subplots(figsize=(7.5, 3.6), dpi=160)
    ax.bar([r["day"] for r in d], [r["p99"] for r in d], color=navy)
    ax.set_xlabel("Day of the 28 day period"); ax.set_ylabel("99th percentile delay, seconds")
    ax2 = ax.twinx(); ax2.plot([r["day"] for r in d], [100 * r["unresolved_share"] for r in d], color=teal, lw=2)
    ax2.set_ylabel("Unresolved share, percent")
    ax.set_title("Daily 99th percentile delay and unresolved share")
    ax.spines[["top"]].set_visible(False); ax2.spines[["top"]].set_visible(False)
    fig.tight_layout(); fig.savefig(os.path.join(out, "chart_by_day.png")); plt.close(fig)
    fig, ax = plt.subplots(figsize=(7.5, 3.6), dpi=160)
    cs = [centre(i) for i in range(NB)]
    ax.bar(cs, hist / hist.sum(), width=[c * 0.057 for c in cs], color=navy)
    ax.set_xscale("log"); ax.set_xlabel("Delay, seconds"); ax.set_ylabel("Share of resolved transactions")
    ax.set_title("Distribution of arrival to inclusion delay")
    ax.spines[["top", "right"]].set_visible(False); fig.tight_layout(); fig.savefig(os.path.join(out, "chart_distribution.png")); plt.close(fig)


def f(x, nd=1):
    return "suppressed" if x is None else f"{x:,.{nd}f}"


def write_md(res, out):
    o = res["overall"]
    L = []
    L.append("# Sample baseline report: Ethereum public mempool data, 28 days\n")
    L.append("This report shows the format an operator would receive. It tests no hypothesis. The data are public. Arrival is the time the observer first saw a transaction. Completion is the inclusion block time. Only two timestamps exist, so this is an end to end figure. Stage durations, retries, webhooks and queues are not in this dataset and are what a pilot would add.\n")
    L.append("## Headline figures\n")
    L.append(f"| Item | Value |\n|:---|---:|\n| Transactions observed | {o['rows']:,} |\n| Resolved (included) | {o['resolved']:,} |\n| Unresolved share | {100*o['unresolved_share']:.2f} percent |\n| Median delay | {f(o['p50'])} s |\n| 90th percentile delay | {f(o['p90'])} s |\n| 99th percentile delay | {f(o['p99'])} s |\n| Windows reported (300 s, at least 50 resolved) | {res['windows_reported']:,} of {res['windows_total']:,} |\n| Rows with completion before arrival plus 1 ms, set to 1 ms | {100*o['clipped_share']:.2f} percent |\n")
    L.append("## By hour of day (UTC)\n\n| Hour | Resolved | Median s | 90th s | 99th s | Unresolved share |\n|---:|---:|---:|---:|---:|---:|")
    for r in res["by_hour"]:
        L.append(f"| {r['hour_utc']:02d} | {r['n']:,} | {f(r['p50'])} | {f(r['p90'])} | {f(r['p99'])} | {100*r['unresolved_share']:.2f} percent |")
    L.append("\n## By day\n\n| Day | Resolved | Median s | 90th s | 99th s | Unresolved share |\n|---:|---:|---:|---:|---:|---:|")
    for r in res["by_day"]:
        L.append(f"| {r['day']} | {r['n']:,} | {f(r['p50'])} | {f(r['p90'])} | {f(r['p99'])} | {100*r['unresolved_share']:.2f} percent |")
    L.append("\n## Ten slowest windows by 99th percentile\n\n| Window start (seconds since 1 January 1970 UTC) | Resolved | Median s | 99th s |\n|---:|---:|---:|---:|")
    for r in res["slowest_windows"]:
        L.append(f"| {r['window_start_utc_seconds']:.0f} | {r['n']:,} | {f(r['p50'])} | {f(r['p99'])} |")
    L.append("\n## Reading notes\n\n1. Delays are measured on a log scale with 40 bins per decade, so each figure is the centre of its bin, accurate to about 3 percent.\n2. Groups with fewer than 50 resolved transactions are suppressed.\n3. Ethereum blocks are produced on a fixed cadence, so inclusion delays cluster around block times. An operator's stage delays will have their own shape.\n4. Unresolved transactions are counted and excluded from delay figures.\n")
    open(os.path.join(out, "sample_report.md"), "w").write("\n".join(L))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--folder", required=True); ap.add_argument("--manifest", required=True)
    ap.add_argument("--out", required=True); ap.add_argument("--adapters", required=True)
    a = ap.parse_args(); run(a.folder, a.manifest, a.out, a.adapters)
