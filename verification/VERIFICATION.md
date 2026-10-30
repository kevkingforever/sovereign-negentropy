# Verification map

This folder holds two short Python programs that test the mathematical statements in the paper "Sovereign Negentropy" (edition October 2026), the saved output of one run of each, and this map.

## What these programs are, and are not

* They are tests of the paper's mathematics, written by an AI assistant (Claude) during the preparation of the paper and run in a cloud workspace on 29 October 2026. They were not part of the author's original draft.
* They do not read the paper. The formulas are typed into the programs by hand. This file lists, for every check, which statement in the paper it supports, so a reader can compare the two.
* They use no internet and no AI when they run.
* A PASS shows that a statement is consistent on the numbers or symbols tested. It is not a proof, and it says nothing about whether the economics works in a real economy.

## How to rerun

1. Install Python 3.
2. Run: pip install numpy scipy sympy
3. Run: python3 verify_checks.py
4. Run: python3 verify_symbolic.py

Both also run in Google Colab. Each prints PASS or FAIL per check, with the numbers behind it, and a final count.

## Where the evidence is

* outputs/verify_checks_output.txt: the saved run of the numerical program. It records the date, the Python and package versions, and a SHA256 hash of the script that produced it. Result: 28 of 28 checks passed.
* outputs/verify_symbolic_output.txt: the same for the symbolic program. Result: 19 of 19 checks passed.

You can confirm the saved output is genuine in two ways: rerun the programs and compare the PASS lines, and compute the hash of your copy of each script (sha256sum verify_checks.py) and compare it with the hash printed at the top of the saved output.

## Map: numerical checks (verify_checks.py)

Proposition numbers are those printed in the paper.

* C1a, C1b, C1c. Abstract and Section 3.1. The decay C0 exp(minus the integral of alpha) satisfies dC/dt = minus alpha C; the earlier form C0 exp(minus alpha(t) t) does not.
* C2a, C2b. Proposition 1 (Velocity Friction Core). The friction integral tends to zero as velocity grows, and the Shannon allocation term remains.
* C3a to C3e. Proposition 3 (Retention threshold) with Assumption 1. The net rate Delta rises with routing capacity, is negative at zero capacity, positive at large capacity, and has a unique threshold; tested on a worked example and 200 random parameter sets. The functional forms used (for example E equal to E0 times 1 plus R) are illustrative choices that satisfy Assumption 1; they are not claimed to be the true economy.
* C4a, C4b. Proposition 4 (Retention against exit). The stay or leave rule matches a direct comparison, and the two options tie exactly at the crossover horizon T star.
* C5. Proposition 5 (Path independence). The yield line integral gives the same value on two different paths and equals the change in V_c.
* C6a, C6b, C6c. Proposition 6 (Regulator bounds) and the earlier form in Section 4.3. The original throughput formula goes negative above saturation and grows without bound; the corrected form stays within its bounds.
* C7a, C7b. Proposition 7 (Bounded impulse absorption). A pulse of width w needs energy xi J0 squared over w, and the minimum absorbable width follows.
* C8a to C8d. Proposition 8 (Velocity incentive) and Proposition 9 (Revenue adequacy). The fee is zero at maximum velocity, equals Gamma0 times 1 plus mu b at zero velocity, falls as velocity rises, and a 0.05 percent fee needs taxed turnover of 400 times GDP to raise 20 percent of GDP.
* C9a to C9d. Section 8.2. KL divergence to a uniform distribution never exceeds ln n, and the sign of the regularizer decides whether training pulls the model toward chaos (plus sign) or away from it (minus sign, as in the corrected paper).
* C10. Proposition 11 (Bounded excess risk). Excess clean risk stays below 8 epsilon B squared in a worst case corruption setting.
* C11. Proposition 10 (Convergence of decentralized descent), convex case. The gradient descent bound holds for 200 steps on a convex quadratic.

## Map: symbolic checks (verify_symbolic.py)

These use the SymPy computer algebra system and hold for all values of the symbols.

* S1a, S1b. Abstract and Section 3.1. The corrected decay solves dC/dt = minus alpha C for any alpha(t); the earlier form leaves a residual of minus t alpha prime C.
* S2a to S2c. Proposition 8. The derivative of the fee with respect to velocity is minus Gamma0 over vmax; the fee is zero at (vmax, 0); the fee at zero velocity is Gamma0 times 1 plus mu b.
* S3a to S3c. Proposition 7. The pulse energy integral, the minimum width, and divergence as the width goes to zero.
* S4. Section 8.2. KL divergence to the uniform distribution equals ln n minus entropy when the probabilities sum to 1.
* S5. Definition of yield and Proposition 5. The chain rule identity along a trajectory.
* S6a, S6b. Proposition 4. The stay or leave inequality and the crossover horizon.
* S7. Proof of Proposition 3. The derivative printed in the paper equals the derivative of the net rate Delta.
* S8a to S8c. Proof of Proposition 11. The contamination identities and the corner bound of 4 epsilon B squared.
* S9. Proposition 9. The 400 times arithmetic, exact.
* S10a, S10b. Proposition 6. The hyperbolic tangent factor is increasing, zero at zero, and below 1.

## What no check covers

* The strongly convex rate and the nonconvex gradient bound in Proposition 10.
* Proposition 2, the unit and dimension consistency of the definitions, and the parts of Propositions 1 and 3 that are plain inequalities.
* Every engineering claim in Chapters 4, 6, 7, 8 and 9, and every hypothesis in Appendix C. Those are design targets or empirical claims and need benchmarks or a pilot.

## Honest record of failures during preparation

* One numerical check (C4a) first failed because it tested the exact tie point T equal to 25, where both options are equal and floating point arithmetic decides the comparison. The test was changed to check values on either side of the tie, and the tie itself with a tolerance (C4b). The paper's statement was correct.
* One symbolic check (S4) first failed because it did not impose that the probabilities sum to 1. Without that condition the identity is false. The check was corrected; the paper already states that P is a probability distribution.
* An earlier version of the paper's change log (Appendix B) printed five proposition numbers that were off by one. Fixed; the log now uses automatic references.

## External source cited in the paper

Appendix C.2 cites a documentation page on zero knowledge proofs for Aptos Keyless, hosted at alinush.github.io/keyless-zkp, for the order of magnitude of proof verification time (about 1.1 to 1.3 milliseconds). That measurement was made by others, on a different circuit. It was not run or reproduced by the author or by these programs.
