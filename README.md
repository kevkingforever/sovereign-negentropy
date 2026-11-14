# Sovereign Negentropy

A foundation paper for a parallel economic system: a settlement and incentive layer that runs alongside legacy financial and administrative systems, is joined voluntarily, and is tested through a gated pilot.

Author: Kevin Ansong, independent researcher. Edition: October 2026.

## Status

* This is a working paper. It has not yet been independently reviewed.
* It proposes a framework and states testable hypotheses. It reports no empirical results.
* The mathematics has been checked for internal consistency (see verification below). That is a check on the algebra and logic, not on whether the economics works.
* The first empirical tests are pre registered (see the preregistration folder), with two dated amendments (A1 and A1.1) registered on 12 November 2026 and a data freeze amendment (A2) registered on 14 November 2026. No test has been run and no result is reported.

## What is in this repository

* paper/sovereign_negentropy.pdf and paper/sovereign_negentropy.tex: the paper (LaTeX source and compiled PDF).
* verification/verify_checks.py: 28 numerical checks of the paper's mathematical statements.
* verification/verify_symbolic.py: 19 exact algebra checks using SymPy.
* verification/outputs/: saved output of one run of each program, with date, software versions and script hash.
* verification/VERIFICATION.md: a map from every check to the statement in the paper it supports, including what no check covers and a record of the failures found along the way.
* verification/requirements.txt: Python packages needed to rerun the checks.
* preregistration/: the pre registration of the first empirical tests (version 1.1), Amendments A1 and A1.1, the archived version 1.0, a deviations log, REGISTRY.md (every document with its fingerprint and DOI) and registration instructions.
* s1/: the code for registered test S1 and its 13 tests. A draft until the code freeze tag exists.
* CONTRIBUTING.md and REVIEWERS.md: how to take part in review, and who has reviewed.
* LICENSE: the MIT licence for the code. The paper has its own licence (see the end of this file).

The paper itself contains no code. The code is separate so it can be reviewed, run and extended independently.

## How the paper is organised

* Chapters 2 to 5 are the economic core: a friction entropy index, a demurrage currency with a utility offset, a path independent yield, and a velocity fee. Their propositions use no result from Chapters 6 to 9.
* Chapter 10 is the parallel entry strategy: voluntary participation, interoperation with legacy rails, regulators inside from day one, three gated phases and stop conditions.
* Chapters 4 and 6 to 9 describe supporting infrastructure and sector applications. Their engineering claims are design targets to be benchmarked, not results.
* Appendix A is the notation table with units. Appendix B records every change from the earlier draft, with the reason. Appendix C lists each hypothesis with the test that would confirm or refute it. Appendix D gives the entropy index a measurement rule and summarises the registered tests.

## Verification in brief

To rerun: install Python, run pip install numpy scipy sympy, then run python3 verify_checks.py and python3 verify_symbolic.py from the verification folder. A PASS shows that a statement is consistent on the numbers or symbols tested. It is not a proof. Read verification/VERIFICATION.md before relying on these checks.

## Questions for reviewers

1. Is the network utility premium U_n a defensible model of what a participant earns, and is the retention condition (net rate above the external rate, with exit friction buying only a finite horizon) the right way to frame demurrage?
2. Can the friction indices f_c, f_t, f_i and the allocation distribution p_i be measured in a real corridor, and is the entropy index S_E useful as an index or only as a metaphor?
3. The velocity fee rises when local velocity falls. Is it acceptable as an incentive instrument, given that it is not by itself a stabilizer?
4. Is the revenue adequacy result (a 0.05 percent fee funds 20 percent of GDP only at taxed turnover of 400 times GDP) stated correctly, and what turnover ratios do real payment systems show?
5. The paper models one jurisdiction. Cross border settlement, exchange rates, and interaction with central bank policy are not modelled. What is the minimum needed to support a global claim?
6. Does the paper position itself correctly against prior work on demurrage currencies, velocity of money, and transaction cost economics? A literature review is not yet included.
7. Appendix D defines the entropy from the latency distribution of completed transactions. Is that a sensible operational definition, and can the registered test S1 fail?

## Licences

The paper is licensed under the Creative Commons Attribution 4.0 International (CC BY 4.0) License. To view a copy of this license, visit https://creativecommons.org/licenses/by/4.0/

The code, including the programs in the verification folder, is licensed under the MIT licence. See the LICENSE file.


## Repository layout

* paper/: the working paper, source and PDF, including Appendix D.
* preregistration/: the registered tests (version 1.1), Amendments A1 and A1.1, the registry of fingerprints and DOIs, the deviations log and the archived version 1.0.
* s1/: the S1 analysis code, its tests and a power study on synthetic data.
* docs/: the Technical Annex describing the Phase 1 pilot.
* telemetry/: the Phase 1 reference pipeline, its 22 self checks, the lock benchmark and the saved results, including a second run on Google Colab.
* verification/: the 47 offline checks of the paper's mathematics.

## Tools and assistance

This work was developed by Kevin Ansong with AI assistance (Claude, by Anthropic) for drafting, code and test construction. Kevin Ansong directs the project and is responsible for every claim. All code, tests and results are open and can be rerun by anyone.

## Registration

The pre registration (version 1.1) was registered publicly on OSF Registries on 1 November 2026.

* Registration: https://osf.io/w6uan/
* DOI: https://doi.org/10.17605/OSF.IO/W6UAN
* Archive: https://doi.org/10.5281/zenodo.23869943

Amendments to the registration, both registered on 12 November 2026 before any data were loaded:

* A1: design decisions for S1. GitHub release `preregistration_a1`, Zenodo DOI https://doi.org/10.5281/zenodo.24167638, PDF SHA256 ceac2e992772b3b18611d6ceab9004db886fcb7d13f50d3dd816a1112a1752b2.
* A1.1: two clarifications after reviewer comments. GitHub release `preregistration_a1_1`, Zenodo DOI https://doi.org/10.5281/zenodo.24170447, PDF SHA256 120aa87963569650ce79551abb1afc1a4cd550b36c67e6d6da88f1c1b05c4a42.
* OSF registration of both: https://osf.io/ezpxf (project https://osf.io/wc4e8).

Data freeze, registered on 14 November 2026:

* A2: the 28 Ethereum files (16 October to 12 November 2026) with checksums, and the status of D1. GitHub release `preregistration_a2`, Zenodo DOI https://doi.org/10.5281/zenodo.24213041, PDF SHA256 605009011f49cabdb85a4c07c954377c6c8a2aef412d194b5f88476248e40380. OSF registration https://osf.io/pt43h. The manifests are in preregistration/manifests/.

The next record is Amendment A3: the window length, the bin edges and the unresolved share report, from the training period only. The full list is in preregistration/REGISTRY.md.
