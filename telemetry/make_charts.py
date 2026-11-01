"""Draw the two validation charts from results/*.json. Run: python3 make_charts.py"""
import json, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
here = os.path.dirname(os.path.abspath(__file__))
res = os.path.join(here, "results")
d = json.load(open(os.path.join(res, "locks_raw.json")))
sc = json.load(open(os.path.join(res, "scaling.json")))
INK, MUTE, GRID = "#1f2933", "#6b7785", "#e3e7eb"
COL = {"baseline": "#8a96a3", "pipeline": "#0b7a75", "blocking_control": "#c2410c"}
LAB = {"baseline": "No pipeline", "pipeline": "Read only pipeline", "blocking_control": "Deliberate lock (control)"}
plt.rcParams.update({"font.family": "DejaVu Sans", "text.color": INK, "axes.edgecolor": GRID})

fig, ax = plt.subplots(figsize=(7.2, 4.2), dpi=200)
for i, c in enumerate(["baseline", "pipeline", "blocking_control"]):
    v = [r["p99_ms"] for r in d["runs"] if r["condition"] == c]
    ax.scatter([i] * len(v), v, s=46, color=COL[c], zorder=3)
    m = sorted(v)[len(v) // 2]
    ax.hlines(m, i - 0.28, i + 0.28, color=COL[c], lw=2.2, zorder=2)
    ax.annotate(f"{m:.1f} ms", (i + 0.3, m), va="center", fontsize=10, color=INK)
ax.set_yscale("log"); ax.set_ylim(1, 400)
ax.set_xticks(range(3)); ax.set_xticklabels([LAB[c] for c in COL], fontsize=10)
ax.set_xlim(-0.6, 2.9)
ax.set_ylabel("99th percentile write latency (ms, log scale)", fontsize=10, color=MUTE)
ax.grid(axis="y", color=GRID, zorder=0)
for s in ("top", "right"): ax.spines[s].set_visible(False)
ax.set_title("Five repetitions of 30 seconds at 800 transactions per second", fontsize=11, loc="left", color=INK)
fig.tight_layout(); fig.savefig(os.path.join(res, "chart_locks.png")); plt.close(fig)

fig, ax = plt.subplots(figsize=(7.2, 3.6), dpi=200)
x = [r["events"] for r in sc]; y = [r["us_per_event"] for r in sc]
ax.plot(x, y, color=COL["pipeline"], lw=2.2, marker="o", ms=6, zorder=3)
ax.set_xscale("log"); ax.set_ylim(0, 1.0)
ax.set_xlabel("Events processed so far (log scale)", fontsize=10, color=MUTE)
ax.set_ylabel("Microseconds per event", fontsize=10, color=MUTE)
ax.grid(color=GRID, zorder=0)
for s in ("top", "right"): ax.spines[s].set_visible(False)
ax.set_title("Cost per event stays flat as history grows 64 times", fontsize=11, loc="left", color=INK)
fig.tight_layout(); fig.savefig(os.path.join(res, "chart_scaling.png")); plt.close(fig)
print("ok")
