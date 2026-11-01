# Pre registration

This folder holds the pre registration of the first empirical tests of the friction entropy index.

## Files

* PREREGISTRATION_v1_1.md and PREREGISTRATION_v1_1.pdf: the current version. It supersedes version 1.0.
* archive/PREREGISTRATION_v1_0.md: version 1.0, kept unchanged as a record. It was committed on 31 October 2026 and amended before any data access.
* DEVIATIONS.md: the log of any departure from the registered plan. No deviations are recorded yet.
* REGISTRATION_RECORD.md: created after registration. It holds the OSF registration link, the Zenodo DOI and the file hashes.

## Registering version 1.1

A git commit alone is not a trustworthy timestamp, because history can be rewritten and commit dates are set by the committer. Use an external registry.

1. Complete the two bracketed items in PREREGISTRATION_v1_1.md (the data access statement and the independent reviewer) and commit the result. Do this before registering and never afterwards.
2. Compute and record the hashes: `sha256sum PREREGISTRATION_v1_1.md PREREGISTRATION_v1_1.pdf`.
3. Create a registration on OSF Registries (osf.io/registries). Upload the PDF. Enter the hashes in the description.
4. Ask the independent reviewer to record the hash of the PDF before any dataset is loaded.
5. Tag the commit `preregistration_v1_1` and publish a release. With the Zenodo GitHub integration enabled for this repository, the release is archived and receives a DOI.
6. Write REGISTRATION_RECORD.md with the OSF link, the DOI, the tag, and the hashes. Commit it. Do not edit the registered files.

## Data freeze amendment

Before any validation or test data are loaded, a dated amendment records exact file versions, row counts, SHA256 checksums, download dates, the chosen window length and bin edges (from the training period only), and the chain data source. It is committed and registered before the validation and test periods are opened. See Section 5 of the registration.

## Reporting

The results of every registered test are published in this repository within 30 days of completing the analysis, whatever the outcome.
