# Sovereign Negentropy

A foundation paper for a parallel economic system: a settlement and incentive layer that runs alongside legacy financial and administrative systems, is joined voluntarily, and is tested through a gated pilot.

Author: Kevin Ansong, independent researcher. Edition: October 2026.

## Status

* This is a working paper. It has not yet been independently reviewed.
* It proposes a framework and states testable hypotheses. It reports no empirical results.
* The mathematics has been checked for internal consistency (see verification below). That is a check on the algebra and logic, not on whether the economics works.

## What is in this repository

* paper/sovereign_negentropy.pdf and paper/sovereign_negentropy.tex: the paper (LaTeX source and compiled PDF).
* verification/verify_checks.py: 28 numerical checks of the paper's mathematical statements.
* verification/verify_symbolic.py: 19 exact algebra checks using SymPy.
* verification/outputs/: saved output of one run of each program, with date, software versions and script hash.
* verification/VERIFICATION.md: a map from every check to the statement in the paper it supports, including what no check covers and a record of the failures found along the way.
* verification/requirements.txt: Python packages needed to rerun the checks.

The paper itself contains no code. The code is separate so it can be reviewed, run and extended independently.

## How the paper is organised

* Chapters 2 to 5 are the economic core: a friction entropy index, a demurrage currency with a utility offset, a path independent yield, and a velocity fee. Their propositions use no result from Chapters 6 to 9.
* Chapter 10 is the parallel entry strategy: voluntary participation, interoperation with legacy rails, regulators inside from day one, three gated phases and stop conditions.
* Chapters 4 and 6 to 9 describe supporting infrastructure and sector applications. Their engineering claims are design targets to be benchmarked, not results.
* Appendix A is the notation table with units. Appendix B records every change from the earlier draft, with the reason. Appendix C lists each hypothesis with the test that would confirm or refute it.

## Verification in brief

To rerun: install Python, run pip install numpy scipy sympy, then run python3 verify_checks.py and python3 verify_symbolic.py from the verification folder. A PASS shows that a statement is consistent on the numbers or symbols tested. It is not a proof. Read verification/VERIFICATION.md before relying on these checks.

## Questions for reviewers

1. Is the network utility premium U_n a defensible model of what a participant earns, and is the retention condition (net rate above the external rate, with exit friction buying only a finite horizon) the right way to frame demurrage?
2. Can the friction indices f_c, f_t, f_i and the allocation distribution p_i be measured in a real corridor, and is the entropy index S_E useful as an index or only as a metaphor?
3. The velocity fee rises when local velocity falls. Is it acceptable as an incentive instrument, given that it is not by itself a stabilizer?
4. Is the revenue adequacy result (a 0.05 percent fee funds 20 percent of GDP only at taxed turnover of 400 times GDP) stated correctly, and what turnover ratios do real payment systems show?
5. The paper models one jurisdiction. Cross border settlement, exchange rates, and interaction with central bank policy are not modelled. What is the minimum needed to support a global claim?
6. Does the paper position itself correctly against prior work on demurrage currencies, velocity of money, and transaction cost economics? A literature review is not yet included.

## License
This work is licensed under the Creative Commons Attribution 4.0 International (CC BY 4.0) License. To view a copy of this license, visit https://creativecommons.org/licenses/by/4.0/
