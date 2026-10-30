"""Numerical checks for the Sovereign Negentropy paper (edition October 2026).

WHAT THIS IS
A short program that tests the mathematical statements made in the paper on concrete
numbers and on random samples. For each statement it computes both sides and prints
PASS or FAIL with the numbers behind the result. It uses no network and no AI.

WHAT IT IS NOT
It does not read the paper, and it is not a proof. The formulas are retyped here by
hand, so a reader should compare them with the paper (see VERIFICATION.md for the
line by line map). Examples and random samples can show that a statement is not
obviously wrong; the proofs in the paper are what establish the statements, and a
mathematician should read those. Exact algebra is checked separately in
verify_symbolic.py.

HOW TO RUN
    pip install numpy scipy
    python3 verify_checks.py

Each check label shows the paper statement it supports, for example
[Prop 3] means Proposition 3 as numbered in the paper.
"""
import math
import re
import numpy as np
from scipy import integrate, optimize

results = []


PAPER_REF = {
    1: "Abstract; Sec 3.1 net effective value",
    2: "Prop 1 Velocity Friction Core",
    3: "Prop 3 Retention threshold, Assumption 1",
    4: "Prop 4 Retention against exit",
    5: "Prop 5 Path independence of yield",
    6: "Prop 6 Regulator bounds; earlier form of Sec 4.3",
    7: "Prop 7 Bounded impulse absorption",
    8: "Prop 8 Velocity incentive; Prop 9 Revenue adequacy",
    9: "Sec 8.2 sign and bound of the KL term",
    10: "Prop 11 Bounded excess risk",
    11: "Prop 10 Convergence of decentralized descent",
}


def check(name, ok, detail=""):
    results.append(bool(ok))
    m = re.match(r"C(\d+)", name)
    ref = PAPER_REF.get(int(m.group(1)), "") if m else ""
    label = name if not ref else name.split(" ", 1)[0] + " [" + ref + "] " + name.split(" ", 1)[1]
    print(("PASS" if ok else "FAIL") + " | " + label + (" | " + detail if detail else ""))


# ---------------------------------------------------------------------------
# C1. Abstract decay formula: C0*exp(-alpha(t)*t) versus exp of minus the integral
# ---------------------------------------------------------------------------
alpha = lambda s: 0.5 + 0.4 * np.sin(s)
T = 5.0
integral_alpha = 0.5 * T + 0.4 * (1 - np.cos(T))          # closed form of the integral
orig = math.exp(-alpha(T) * T)
corr = math.exp(-integral_alpha)
check("C1a original abstract form differs from the integral form",
      abs(orig - corr) > 1e-3, f"original={orig:.5f} corrected={corr:.5f}")
h = 1e-6
f_orig = lambda s: math.exp(-alpha(s) * s)
f_corr = lambda s: math.exp(-(0.5 * s + 0.4 * (1 - np.cos(s))))
d_orig = (f_orig(T + h) - f_orig(T - h)) / (2 * h)
d_corr = (f_corr(T + h) - f_corr(T - h)) / (2 * h)
check("C1b corrected form satisfies dC/dt = -alpha*C", abs(d_corr + alpha(T) * f_corr(T)) < 1e-6,
      f"residual={abs(d_corr + alpha(T) * f_corr(T)):.2e}")
check("C1c original form does NOT satisfy dC/dt = -alpha*C", abs(d_orig + alpha(T) * f_orig(T)) > 1e-3,
      f"residual={abs(d_orig + alpha(T) * f_orig(T)):.4f}")

# ---------------------------------------------------------------------------
# C2. Axiom I limits: friction integral vanishes as velocity grows; Shannon baseline stays
# ---------------------------------------------------------------------------
p = np.array([0.5, 0.2, 0.2, 0.1])
H_A = -(p * np.log(p)).sum()
f_sum, tau0, horizon = 0.3, 1.0, 10.0
vals = []
for v in [1, 10, 100, 1e6]:
    fric = f_sum / (tau0 * v) * horizon
    vals.append(fric)
check("C2a friction term tends to 0 as v grows", vals[-1] < 1e-4 and vals == sorted(vals, reverse=True),
      "friction term for v=1,10,100,1e6: " + ", ".join(f"{x:.2e}" for x in vals))
check("C2b total S_E tends to the Shannon baseline, not to 0", abs((H_A + vals[-1]) - H_A) < 1e-4 and H_A > 0.5,
      f"baseline H_A={H_A:.4f}")

# ---------------------------------------------------------------------------
# C3. Retention proposition: monotone net rate and a unique threshold
# ---------------------------------------------------------------------------
b1, b2, b3, a0, gam = 0.02, 0.03, 0.05, 0.04, 0.10
E0, Eref, v0, dv, f0, y0 = 1.0, 1.0, 0.1, 0.6, 1.5, 0.5


def Delta(R):
    E = E0 * (1 + R)
    v = v0 + dv * (1 - np.exp(-R))
    fs = f0 * np.exp(-R)
    y = y0 + (1 - y0) * (1 - np.exp(-R))
    a = R / (1 + R)
    return b1 * np.log(E / Eref) + b2 * v - b3 * fs - a0 * (1 - y) - gam * (1 - a)


grid = np.linspace(0, 200, 20001)
D = Delta(grid)
check("C3a Delta(R) is strictly increasing on the grid", np.all(np.diff(D) > 0))
check("C3b stagnant node has Delta(0) < 0", Delta(0.0) < 0, f"Delta(0)={Delta(0.0):.4f}")
check("C3c active node has Delta(200) > 0", Delta(200.0) > 0, f"Delta(200)={Delta(200.0):.4f}")
Rstar = optimize.brentq(Delta, 0, 200)
check("C3d unique threshold R* exists", abs(Delta(Rstar)) < 1e-9, f"R*={Rstar:.4f}")
rng = np.random.default_rng(0)
ok = True
for _ in range(200):
    pb = rng.uniform(0.001, 0.2, 5)
    pe = rng.uniform(0.2, 2.0, 3)
    pa = rng.uniform(0.1, 1.0)

    def D_(R):
        E = pe[0] * (1 + R)
        v = pe[1] + pe[2] * (1 - np.exp(-R))
        fs = pa * np.exp(-R)
        y = 0.4 + 0.6 * (1 - np.exp(-R))
        a = R / (1 + R)
        return pb[0] * np.log(E) + pb[1] * v - pb[2] * fs - pb[3] * (1 - y) - pb[4] * (1 - a)

    ok &= bool(np.all(np.diff(D_(np.linspace(0, 100, 2001))) > 0))
check("C3e monotonicity holds for 200 random parameter sets", ok)

# ---------------------------------------------------------------------------
# C4. Exit versus stay over horizon T
# ---------------------------------------------------------------------------
d_bar, r_ext, F_ext = 0.04, 0.06, 0.5
Tstar = F_ext / (r_ext - d_bar)
rows = []
agree = True
for Th in [1, 5, 10, 20, 24, 26, 30, 100]:        # 25 is the exact tie, tested separately below
    stay = d_bar * Th
    leave = -F_ext + r_ext * Th
    rule = d_bar > r_ext - F_ext / Th
    agree &= (stay > leave) == rule
    rows.append(f"T={Th}:{'stay' if stay > leave else 'leave'}")
check("C4a stay/leave rule matches direct comparison", agree, " ".join(rows))
check("C4b crossover horizon T* = F_ext/(r_ext - d_bar), and both options tie there",
      abs(Tstar - 25) < 1e-9 and abs(d_bar * Tstar - (-F_ext + r_ext * Tstar)) < 1e-9, f"T*={Tstar:.6f}")

# ---------------------------------------------------------------------------
# C5. Path independence of the yield line integral
# ---------------------------------------------------------------------------
def V(q):
    C, fc, ft, fi = q
    return 2 * math.sqrt(1 + C) / (1 + fc + ft + fi)


def grad(q, h=1e-6):
    g = np.zeros(4)
    for i in range(4):
        qp, qm = np.array(q, float), np.array(q, float)
        qp[i] += h
        qm[i] -= h
        g[i] = (V(qp) - V(qm)) / (2 * h)
    return g


q0 = np.array([0.0, 1.0, 1.0, 1.0])
q1 = np.array([10.0, 0.2, 0.1, 0.3])


def path_straight(s):
    return q0 + s * (q1 - q0), (q1 - q0)


def path_curved(s):
    pos = q0 + s * (q1 - q0) + np.array([0, 0.3 * math.sin(math.pi * s), -0.2 * math.sin(2 * math.pi * s), 0.1 * s * (1 - s)])
    dpos = (q1 - q0) + np.array([0, 0.3 * math.pi * math.cos(math.pi * s), -0.4 * math.pi * math.cos(2 * math.pi * s), 0.1 * (1 - 2 * s)])
    return pos, dpos


def line_int(path):
    f = lambda s: float(np.dot(grad(path(s)[0]), path(s)[1]))
    return integrate.quad(f, 0, 1, limit=200)[0]


I1, I2, dV = line_int(path_straight), line_int(path_curved), V(q1) - V(q0)
check("C5 line integral equals V(end) - V(start) on two different paths",
      abs(I1 - dV) < 1e-5 and abs(I2 - dV) < 1e-5, f"straight={I1:.6f} curved={I2:.6f} delta V={dV:.6f}")

# ---------------------------------------------------------------------------
# C6. Throughput regulator: original versus corrected
# ---------------------------------------------------------------------------
Q0, lam = 1.0, 0.5
Qorig = lambda L, Vc: Q0 * math.tanh(1 - L) * math.exp(lam * Vc)       # L is L_core/L_max
Qcorr = lambda L, v, eta=3.0: Q0 * math.tanh(max(0.0, 1 - L)) * min(math.exp(lam * v), eta)
check("C6a original goes negative above saturation", Qorig(1.5, 1.0) < 0, f"Q(1.5,1)={Qorig(1.5, 1.0):.4f}")
check("C6b original grows without bound with velocity", Qorig(0.0, 50.0) > 1e9, f"Q(0,50)={Qorig(0.0, 50.0):.3e}")
vals = [Qcorr(L, v) for L in np.linspace(0, 3, 31) for v in np.linspace(0, 100, 51)]
check("C6c corrected form stays within [0, Q0*tanh(1)*eta_max]", min(vals) >= 0 and max(vals) <= math.tanh(1) * 3.0 + 1e-12,
      f"min={min(vals):.4f} max={max(vals):.4f} cap={math.tanh(1) * 3.0:.4f}")

# ---------------------------------------------------------------------------
# C7. Impulse energy: unit-area pulse of width w
# ---------------------------------------------------------------------------
J0, xi, E_idle = 1.0, 1.0, 100.0
rows, ok = [], True
for w in [1, 0.1, 0.01, 0.001]:
    num = integrate.quad(lambda t: (J0 / w) ** 2, 0, w)[0]
    ok &= abs(num - J0 ** 2 / w) < 1e-6 * J0 ** 2 / w
    rows.append(f"w={w}: {num:.1f}")
check("C7a pulse energy equals J0^2/w and diverges as w goes to 0", ok, "; ".join(rows))
wmin = xi * J0 ** 2 / E_idle
check("C7b minimum absorbable width w_min = xi*J0^2/E_idle", abs(wmin - 0.01) < 1e-12, f"w_min={wmin}")

# ---------------------------------------------------------------------------
# C8. Fee schedule and revenue arithmetic
# ---------------------------------------------------------------------------
G0, mu, vmax, bmax = 5e-4, 2.0, 1.0, 1.0
fee = lambda v, b: G0 * ((1 - v / vmax) + mu * b)
check("C8a fee is zero at v=vmax, b=0", fee(1.0, 0.0) == 0.0)
check("C8b fee at v=0, b=bmax equals G0*(1+mu*bmax), not G0+mu*b",
      abs(fee(0.0, bmax) - G0 * (1 + mu * bmax)) < 1e-15, f"fee={fee(0.0, bmax):.6f}")
check("C8c fee is strictly decreasing in velocity (rate rises when velocity falls)",
      fee(0.2, 0.3) > fee(0.8, 0.3), f"fee(0.2)={fee(0.2, 0.3):.6f} fee(0.8)={fee(0.8, 0.3):.6f}")
need = 0.20 / 5e-4
check("C8d taxed turnover needed for 20 percent of GDP at 0.05 percent is 400x GDP", abs(need - 400) < 1e-9, f"need={need}")

# ---------------------------------------------------------------------------
# C9. KL against the uniform distribution: bound and direction of the regulariser
# ---------------------------------------------------------------------------
n = 8
rng = np.random.default_rng(1)
kl_u = lambda P: float(np.sum(P * np.log(np.clip(P, 1e-300, None) * n)))
samples = [rng.dirichlet(np.full(n, a)) for a in [0.05, 0.2, 1.0, 5.0] for _ in range(2500)]
kls = [kl_u(P) for P in samples]
check("C9a KL(P||uniform) never exceeds ln(n)", max(kls) <= math.log(n) + 1e-9, f"max={max(kls):.4f} ln(n)={math.log(n):.4f}")
check("C9b +KL is minimised by the uniform (chaos) distribution", min(kls) >= 0 and kl_u(np.full(n, 1 / n)) < 1e-12,
      f"min sampled KL={min(kls):.5f}")
softmax = lambda z: np.exp(z - z.max()) / np.exp(z - z.max()).sum()
ent = lambda P: float(-(P * np.log(np.clip(P, 1e-300, None))).sum())
r_plus = optimize.minimize(lambda z: kl_u(softmax(z)), rng.normal(size=n), method="BFGS")
r_minus = optimize.minimize(lambda z: -kl_u(softmax(z)), rng.normal(size=n), method="BFGS")
check("C9c minimising +KL drives entropy up to ln(n) (original sign pulls toward chaos)",
      abs(ent(softmax(r_plus.x)) - math.log(n)) < 1e-3, f"entropy={ent(softmax(r_plus.x)):.4f}")
check("C9d minimising -KL drives entropy down (corrected sign pushes away from chaos)",
      ent(softmax(r_minus.x)) < 0.05, f"entropy={ent(softmax(r_minus.x)):.4f}")

# ---------------------------------------------------------------------------
# C10. Contamination bound: excess clean risk <= 8*eps*B^2
# ---------------------------------------------------------------------------
B, mu_clean = 1.0, 0.2
ok, worst = True, 0.0
for eps in np.linspace(0.001, 0.5, 200):
    c_eps = (1 - eps) * mu_clean + eps * B               # minimiser of contaminated risk (constant predictor)
    excess = (c_eps - mu_clean) ** 2                      # excess clean risk of that predictor
    worst = max(worst, excess / (8 * eps * B ** 2))
    ok &= excess <= 8 * eps * B ** 2 + 1e-12
check("C10 excess clean risk stays below 8*eps*B^2 (constant predictor, worst case corruption)", ok,
      f"largest ratio excess/bound={worst:.4f}")

# ---------------------------------------------------------------------------
# C11. Gradient descent bound for a convex quadratic
# ---------------------------------------------------------------------------
rng = np.random.default_rng(2)
M_ = rng.normal(size=(6, 6))
A = M_ @ M_.T + 0.1 * np.eye(6)
Lc = np.linalg.eigvalsh(A).max()
eta = 1 / Lc
u = rng.normal(size=6)
u0 = u.copy()
Jf = lambda x: 0.5 * x @ A @ x
ok = True
for m in range(1, 201):
    u = u - eta * (A @ u)
    ok &= Jf(u) <= (u0 @ u0) / (2 * eta * m) + 1e-12
check("C11 J(u_m) - J* <= ||u0 - u*||^2 / (2 eta m) for 200 steps", ok, f"L={Lc:.3f}")

print()
print(f"{sum(results)} of {len(results)} checks passed")
