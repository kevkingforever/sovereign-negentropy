"""Engine cross check on real data. Tests the streaming engine, not any hypothesis.

Each resolved Ethereum transaction is fed to telemetry.pipeline.Pipeline as five events: received at the
arrival time, then the four later stage events all at the inclusion time. Only the END TO END delay is
meaningful here. The stage figures are placeholders and are discarded.
The engine's end to end histogram for every window is compared with an independent numpy calculation
using the same bins and the same booking rule (a delay is booked in the window of its completion time).
Completion before arrival plus 1 ms is set to arrival plus 1 ms, as in Amendment A1.1.
Unresolved transactions are never completed, and the engine counts them as expired.
"""
import argparse, json, math, os, sys, time
import numpy as np

W, LO, HI, PER_DEC = 300.0, 1e-3, 1e3, 40
NB = int(round(math.log10(HI / LO) * PER_DEC)); KK = PER_DEC / math.log(10.0)


def bin_index(x):
    return np.minimum((np.log(np.clip(x, LO, HI) / LO) * KK).astype(np.int64), NB - 1)


def run(folder, manifest_path, out, repo, days):
    sys.path.insert(0, repo)
    from s1.adapters import read_d2_day, verify_manifest
    from telemetry.pipeline import Pipeline, LAST_CODE
    man = json.load(open(manifest_path))
    bad = verify_manifest(folder, man)
    if bad:
        raise SystemExit(f"Manifest check failed for: {bad}. Stop.")
    os.makedirs(out, exist_ok=True)
    files = man["files"][:days] if days else man["files"]
    p = Pipeline(window_s=W, k_min=50)
    ind = {}            # window id -> histogram from the independent calculation
    n_unres_ind = 0
    next_id = 0
    t_start = time.time(); events = 0
    for e in files:
        r = read_d2_day(os.path.join(folder, e["file"]))
        arr, comp = r["arr"], r["comp"]
        ok = ~np.isnan(comp)
        comp = np.where(ok, np.maximum(comp, arr + LO), comp)
        n = len(arr)
        ids = np.arange(next_id, next_id + n); next_id += n
        n_unres_ind += int((~ok).sum())
        # independent histograms, booked at completion window
        d = np.maximum(comp[ok] - arr[ok], LO)
        wid = np.floor(comp[ok] / W).astype(np.int64)
        b = bin_index(d)
        for w in np.unique(wid):
            m = wid == w
            ind.setdefault(int(w), np.zeros(NB, dtype=np.int64))
            ind[int(w)] += np.bincount(b[m], minlength=NB)
        # events for the engine
        ts = np.concatenate([arr] + [comp[ok]] * 4)
        code = np.concatenate([np.zeros(n, dtype=np.int64)] + [np.full(int(ok.sum()), c, dtype=np.int64) for c in (1, 2, 3, 4)])
        tid = np.concatenate([ids] + [ids[ok]] * 4)
        order = np.lexsort((code, ts))
        for t_, c_, i_ in zip(ts[order].tolist(), code[order].tolist(), tid[order].tolist()):
            p.process(i_, c_, t_)
        events += len(order)
        print(f"{e['file']}: {n} transactions fed, {events:,} events, {time.time()-t_start:.0f} s", flush=True)
    p.advance_watermark(p._max_ts + 2 * 86400.0)   # expire what never completed
    # compare
    eng = {w: np.array(p._windows[w].hist[LAST_CODE]) for w in p.window_ids()}
    ws = sorted(set(eng) | set(ind))
    exact = 0; diffs = []; tot_diff = 0
    for w in ws:
        a = eng.get(w, np.zeros(NB, dtype=np.int64)); c = ind.get(w, np.zeros(NB, dtype=np.int64))
        dd = int(np.abs(a - c).sum())
        if dd == 0:
            exact += 1
        else:
            diffs.append((w, dd, int(a.sum()), int(c.sum()))); tot_diff += dd
    n_eng = int(sum(h.sum() for h in eng.values())); n_ind = int(sum(h.sum() for h in ind.values()))
    unres_eng = p.unresolved_total
    res = dict(files=len(files), windows_compared=len(ws), windows_identical=exact,
               windows_different=len(diffs), total_count_difference=tot_diff,
               engine_completed=n_eng, independent_completed=n_ind,
               engine_unresolved=int(unres_eng), independent_unresolved=n_unres_ind,
               events_processed=events, anomalies=int(p.anomalies), reasons=p.reasons,
               seconds=round(time.time() - t_start, 1), worst_windows=sorted(diffs, key=lambda x: -x[1])[:10])
    json.dump(res, open(os.path.join(out, "engine_crosscheck.json"), "w"), indent=1)
    verdict = ("MATCH: the engine's end to end histograms equal the independent calculation in every window."
               if (len(diffs) == 0 and n_eng == n_ind and unres_eng == n_unres_ind) else
               "DIFFERENCES FOUND. See worst_windows. Send this file to Claude. Do not edit anything.")
    open(os.path.join(out, "engine_crosscheck.txt"), "w").write(json.dumps(res, indent=1) + "\n\n" + verdict + "\n")
    print(json.dumps(res, indent=1)); print(verdict)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--folder", required=True); ap.add_argument("--manifest", required=True)
    ap.add_argument("--out", required=True); ap.add_argument("--repo", required=True)
    ap.add_argument("--days", type=int, default=0)
    a = ap.parse_args(); run(a.folder, a.manifest, a.out, a.repo, a.days)
