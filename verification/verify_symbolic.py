"""Symbolic (exact algebra) checks for the Sovereign Negentropy paper.

Unlike verify_checks.py, which tests statements on numbers, this script uses the
SymPy computer algebra system to confirm algebraic identities exactly, for all
values of the symbols. A PASS means SymPy reduced the difference of the two sides
to zero (or evaluated the stated quantity exactly).

Each check names the statement in the paper it supports (paper edition October 2026).
Run with:  python3 verify_symbolic.py      Requires: sympy
No network access and no AI are used.
"""
import sympy as sp

results = []


def check(name, ok, detail=""):
    results.append(bool(ok))
    print(("PASS" if ok else "FAIL") + " | " + name + (" | " + detail if detail else ""))


t, s = sp.symbols("t s", positive=True)
alpha = sp.Function("alpha")

# ---------------------------------------------------------------------------
# S1  Abstract and Section 3.1: C_t = C0 exp(-integral of alpha) solves dC/dt = -alpha C;
#     the earlier form C0 exp(-alpha(t) t) does not.
# ---------------------------------------------------------------------------
C0 = sp.symbols("C0", positive=True)
C_good = C0 * sp.exp(-sp.Integral(alpha(s), (s, 0, t)))
res_good = sp.simplify(sp.diff(C_good, t) + alpha(t) * C_good)
check("S1a [Abstract; Sec 3.1] corrected decay solves dC/dt = -alpha*C for every alpha(t)", res_good == 0,
      f"residual={res_good}")
C_old = C0 * sp.exp(-alpha(t) * t)
res_old = sp.simplify(sp.diff(C_old, t) + alpha(t) * C_old)
expected = -t * sp.Derivative(alpha(t), t) * C_old
check("S1b [Abstract] earlier decay form leaves residual -t*alpha'(t)*C, zero only if alpha is constant",
      sp.simplify(res_old - expected) == 0, f"residual={res_old}")

# ---------------------------------------------------------------------------
# S2  Proposition 8 (velocity incentive) and Section 5.2 fee schedule
# ---------------------------------------------------------------------------
v, vmax, G0, mu, b = sp.symbols("v v_max Gamma_0 mu b", positive=True)
fee = G0 * ((vmax - v) / vmax + mu * b)
check("S2a [Prop 8 (i)] d(fee)/dv = -Gamma0/vmax", sp.simplify(sp.diff(fee, v) + G0 / vmax) == 0)
check("S2b [Prop 8 (ii)] fee is zero at v = vmax, b = 0", sp.simplify(fee.subs({v: vmax, b: 0})) == 0)
check("S2c [Prop 8 (iii)] fee at v = 0 is Gamma0*(1 + mu*b), not Gamma0 + mu*b",
      sp.simplify(fee.subs(v, 0) - G0 * (1 + mu * b)) == 0)

# ---------------------------------------------------------------------------
# S3  Proposition 7 (bounded impulse absorption)
# ---------------------------------------------------------------------------
J0, w, xi, Eidle = sp.symbols("J0 w xi E_idle", positive=True)
energy = sp.integrate(xi * (J0 / w) ** 2, (t, 0, w))
check("S3a [Prop 7] pulse energy equals xi*J0^2/w", sp.simplify(energy - xi * J0**2 / w) == 0, f"energy={energy}")
wmin = sp.solve(sp.Eq(xi * J0**2 / w, Eidle), w)
check("S3b [Prop 7] minimum absorbable width is xi*J0^2/E_idle", wmin == [xi * J0**2 / Eidle], f"solution={wmin}")
check("S3c [Prop 7] required energy diverges as the pulse width goes to 0", sp.limit(xi * J0**2 / w, w, 0, "+") == sp.oo)

# ---------------------------------------------------------------------------
# S4  Section 8.2: KL divergence to the uniform distribution equals ln n minus entropy
# ---------------------------------------------------------------------------
p1, p2, p3 = sp.symbols("p1 p2 p3", positive=True)
p4 = 1 - p1 - p2 - p3                      # probabilities must sum to 1; without this the identity is false
p = [p1, p2, p3, p4]
n = 4
KL = sum(pi * sp.log(pi * n) for pi in p)
Hent = -sum(pi * sp.log(pi) for pi in p)
check("S4 [Sec 8.2] D_KL(P || uniform) = ln n - H(P) for n = 4, with the probabilities summing to 1",
      sp.simplify(sp.expand_log(KL - (sp.log(n) - Hent), force=True)) == 0)

# ---------------------------------------------------------------------------
# S5  Definition of yield and Proposition 5: chain rule along a trajectory
# ---------------------------------------------------------------------------
C = sp.symbols("C", positive=True)
a_, c1, c2, c3, d1, d2, d3 = sp.symbols("a c1 c2 c3 d1 d2 d3", positive=True)
fc, ft, fi = (c1 * sp.exp(-d1 * C), c2 * sp.exp(-d2 * C), c3 * sp.exp(-d3 * C))
x0, x1, x2, x3 = sp.symbols("x0 x1 x2 x3", positive=True)
Vq = a_ * sp.sqrt(1 + x0) / (1 + x1 + x2 + x3)
along = Vq.subs({x0: C, x1: fc, x2: ft, x3: fi})
total = sp.diff(along, C)
grad_form = (sp.diff(Vq, x0) + sp.diff(Vq, x1) * sp.diff(fc, C) + sp.diff(Vq, x2) * sp.diff(ft, C)
             + sp.diff(Vq, x3) * sp.diff(fi, C)).subs({x0: C, x1: fc, x2: ft, x3: fi})
check("S5 [Def of yield; Prop 5] dV_c/dC along the path equals dV/dC + sum_k (dV/df_k)(df_k/dC)",
      sp.simplify(total - grad_form) == 0)

# ---------------------------------------------------------------------------
# S6  Proposition 4: stay or leave rule and crossover horizon
# ---------------------------------------------------------------------------
Db, T, F, r = sp.symbols("Dbar T F_ext r_ext", positive=True)
stay_minus_leave = Db * T - (-F + r * T)
rule_form = T * (Db - (r - F / T))
check("S6a [Prop 4] staying beats leaving iff Dbar > r_ext - F_ext/T (algebraic identity)",
      sp.simplify(stay_minus_leave - rule_form) == 0)
Tstar = sp.solve(sp.Eq(Db * T, -F + r * T), T)
check("S6b [Prop 4] crossover horizon T* = F_ext/(r_ext - Dbar)", [sp.simplify(x - F / (r - Db)) for x in Tstar] == [0],
      f"solution={Tstar}")

# ---------------------------------------------------------------------------
# S7  Proposition 3: the derivative printed in the proof equals the derivative of Delta(R_a)
# ---------------------------------------------------------------------------
R = sp.symbols("R", positive=True)
b1, b2, b3, a0, gam, Eref, Ystar = sp.symbols("beta1 beta2 beta3 alpha0 gamma E_ref Ystar", positive=True)
E, vv, Y, aa, g1, g2, g3 = [sp.Function(nm)(R) for nm in ["E", "v", "Y", "a", "f1", "f2", "f3"]]
Delta = (b1 * sp.log(E / Eref) + b2 * vv - b3 * (g1 + g2 + g3) - a0 * (1 - Y / Ystar) - gam * (1 - aa))
paper = (b1 * sp.diff(E, R) / E + b2 * sp.diff(vv, R) - b3 * (sp.diff(g1, R) + sp.diff(g2, R) + sp.diff(g3, R))
         + a0 * sp.diff(Y, R) / Ystar + gam * sp.diff(aa, R))
check("S7 [Prop 3 proof] d(Delta)/dR_a equals the expression printed in the paper (branch Y < Y*)",
      sp.simplify(sp.diff(Delta, R) - paper) == 0)

# ---------------------------------------------------------------------------
# S8  Proposition 11: contamination identities and corner bound
# ---------------------------------------------------------------------------
eps, R0, Rc, Bm = sp.symbols("epsilon R0 R_c B", positive=True)
Reps = (1 - eps) * R0 + eps * Rc
check("S8a [Prop 11 proof] R_eps - R_0 = eps*(R_c - R_0)", sp.simplify(Reps - R0 - eps * (Rc - R0)) == 0)
A1, A2, A3, A4 = sp.symbols("A1:5")
check("S8b [Prop 11 proof] the three bracketed terms telescope to R0(Phi_eps) - R0(Phi_0)",
      sp.simplify((A1 - A2) + (A2 - A3) + (A3 - A4) - (A1 - A4)) == 0)
corners = [eps * (rc - r0) for r0 in (0, 4 * Bm**2) for rc in (0, 4 * Bm**2)]
check("S8c [Prop 11 proof] on [0, 4B^2]^2 the largest |eps*(R_c - R_0)| is 4*eps*B^2 (linear map, extremes at corners)",
      sp.simplify(sp.Max(*[sp.Abs(c) for c in corners]) - 4 * eps * Bm**2) == 0)

# ---------------------------------------------------------------------------
# S9  Proposition 9: revenue adequacy arithmetic
# ---------------------------------------------------------------------------
need = sp.Rational(20, 100) / sp.Rational(5, 10000)
check("S9 [Prop 9] 20 percent of GDP at a 0.05 percent fee needs taxed turnover of 400 times GDP", need == 400,
      f"nu_required={need}")

# ---------------------------------------------------------------------------
# S10 Proposition 6: the tanh factor is increasing and bounded by tanh(1) on [0, 1]
# ---------------------------------------------------------------------------
x = sp.symbols("x", real=True)
check("S10a [Prop 6] d/dx tanh(x) = 1 - tanh(x)^2 = 1/cosh(x)^2 > 0",
      sp.simplify(sp.diff(sp.tanh(x), x) - 1 / sp.cosh(x) ** 2) == 0)
check("S10b [Prop 6] tanh(0) = 0 so Q = 0 at saturation, and tanh(1) < 1 bounds the factor", sp.tanh(0) == 0 and sp.N(sp.tanh(1)) < 1,
      f"tanh(1)={sp.N(sp.tanh(1), 6)}")

print()
print(f"{sum(results)} of {len(results)} symbolic checks passed")
