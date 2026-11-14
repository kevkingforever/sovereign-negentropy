---
title: "Amendment A2 to the Pre Registration of Empirical Tests, Version 1.1"
subtitle: "Data freeze: the files used for S1, with checksums"
author: "Kevin Ansong. Status: to be registered"
date: "14 November 2026"
---

# 1. Status and purpose

A2 records the exact data files for S1 before any value in them is read. It changes no rule, threshold, model or outcome. It follows Amendment A1 (SHA256 ceac2e992772b3b18611d6ceab9004db886fcb7d13f50d3dd816a1112a1752b2) and Amendment A1.1 (SHA256 120aa87963569650ce79551abb1afc1a4cd550b36c67e6d6da88f1c1b05c4a42), both registered on 12 November 2026. The registration is PREREGISTRATION_v1_1, SHA256 8a065dee4f3b365f0d592336074a9203e1bafab9f1dddcac1d3a25f0278fa1e0.

# 2. One change of order

A1 says A2 records the files, the window length and the bin edges. The window length and the bin edges are computed from the training period of the data. To lock the files first, they are split out. A2 (this document) records the files. A3 records the window length, the bin edges and the unresolved share report required by A1.1. A3 is made before the validation and test periods are opened, and uses the training period only. The registration section 5 requirement is unchanged: the window and bins are fixed before the validation and test periods are opened. This is recorded in DEVIATIONS.md as made before data access.

# 3. Data exposure up to this amendment

The fingerprint tool counted rows and computed SHA256 for each file. It printed and stored no value from any file. The only content read is the first line of column names of each Ethereum file, which was identical in all 28 files and in the file checked on 12 November 2026. No statistic has been computed from any value.

# 4. D2: Ethereum, Flashbots Mempool Dumpster (CC0)

* Source: https://mempool-dumpster.flashbots.net/ethereum/mainnet/YYYY-MM/YYYY-MM-DD.csv.zip
* Days: 28 contiguous UTC days, 16 October 2026 to 12 November 2026 inclusive. This is the 28 days ending 3 days before the freeze date of 15 November 2026 (A1 section 3.2). The freeze date is the day this amendment is registered. If it is registered on another day, these exact days still apply.
* Downloaded on 14 November 2026 in Google Colab. All 28 downloads returned HTTP 200.
* Files: 28. Total rows: 25,155,158. Total size: 2,379,966,683 bytes. Rows per day range from 716,050 to 1,046,382. All 28 SHA256 values differ.
* Columns (all files identical): timestamp_ms, hash, chain_id, from, to, value, nonce, gas, gas_price, gas_tip_cap, gas_fee_cap, data_size, data_4bytes, sources, included_at_block_height, included_block_timestamp_ms, inclusion_delay_ms, tx_type.
* Arrival is timestamp_ms. Completion is included_block_timestamp_ms (A1 section 3.4).
* Fingerprint tool: fingerprint_files.py version 1.0, SHA256 2297aba8c33ae081751dd369af42369b26449d0ed9bea7d14ed581ed572139aa. Its own 12 checks passed.
* Manifest files: manifest_d2.json, SHA256 12ca0cb8ee24cdd164a05bc247048682a8467151a36d9b889c42b22cdbf01148. manifest_d2.csv, SHA256 3f7a80db6166349392c3db46a609da87ca70c59459ef615bddd3fc0e0e3d9d88. Both are in the repository at preregistration/manifests/.
* Any later download must reproduce these SHA256 values. A file that does not match is not used.

# 5. D1: Bitcoin, DataForge lifecycle sample

D1 was not retrieved. On 14 November 2026 the download in Google Colab returned "401, repository not found" for dataforge-labs/bitcoin-mempool-lifecycle on Hugging Face, and the dataset page returned 404 to a logged out visitor. It is not known whether the dataset was removed or made private. No D1 file exists in the author's hands and no D1 value has been seen.

Effect under A1 section 3.1: D1 was expected to be ineligible because its 7 day sample leaves fewer than 3 bootstrap blocks. It is treated as ineligible. It is left out of the Holm correction and of the outcome. The S1 outcome is decided on D2 alone. If D1 becomes available later, it is not added to S1.

# 6. What is still to come

1. A3: window length, bin edges and the unresolved share report by day and by hour of day (A1.1), from the training period of D2 only, before the validation and test periods are opened.
2. The code freeze tag for the S1 code.
3. One run of S1 on D2, reproduction by a reviewer, and publication of the result within 30 days.

# Appendix: D2 file list

Day, rows, bytes and SHA256 of each downloaded file.

\begingroup\scriptsize
\begin{verbatim}
date        rows     bytes     sha256
2026-10-16   871297   83888826  cff253e183720353817a886f6c7db57b6e9fd40601cc8e4e6fd48b1b87102683
2026-10-17   788533   75385509  e9d980ec321cadb7e079d116554cfce1655837ce38a1d709c053d9e0aac2cfed
2026-10-18   784836   74480510  43315c4f8a74d4e0a53acfe90b5d3bb5a706045b24a8d9fc737049feb1bbb6e1
2026-10-19   818202   78353421  4877d61835b6484659ae2fd14a817711497f62aa63cf7b350d3f290a186d0cf2
2026-10-20   857618   81064745  4ace721de49d6cee2328b02c2e4f4f3f32382df2501bdf245e87c4d260cbdb51
2026-10-21   908505   86444441  2b9f0e028386de3d7b55cf0cd129a290c40f6aaef9698e0786a876b7d072fd08
2026-10-22   894427   85372160  d124a00fe7f1770509f7129b247d83f5a09d58caf1f568970ee24e92a15510cf
2026-10-23   966592   91427396  db485f49f520002e95a7df23bdba4b4c23d89d4805d176eed73384cf5dc8311f
2026-10-24   846304   79984900  475028a0c12d5beecb9134f7f735415e87b0f0247a5425a71dd55938f724c19f
2026-10-25   716050   68321698  873ce2b1fb00fdd63d90cb0d42e47f8b76d77c6259dec8036c1b70cd6fedb0f0
2026-10-26   865480   82492976  ce2ce715ea98bc063bc90c1d4b93e68e5db96b6157584b137bb6ad4fcc750ac0
2026-10-27   939852   88590527  82871155c92f35f9c00abe18eac489844db0796ffd27d39cfb2cebbe1f98cb78
2026-10-28  1003111   93420636  c9588963a9602eca5c83d25025d94becbeeca30829010210d72cdd66b205328b
2026-10-29   800648   77092405  1165b9c0f059f8ad8c347ced945291a9c2e0f1cf7019cb7198d35b1f5bdfa048
2026-10-30   888598   85679978  9deb2f5cbd7a9047b8e76608a5b7942e0987af2fee76d87be53b2a63a832dbbd
2026-10-31   770029   74157746  e30d798b33acd9c91a71bcbaca49809954fa01679f7852a5b570a9024726b6f1
2026-11-01   808955   76158253  c379431e435044c6ba683806a4b33e1dcaed009d1eaa7c95cf48aac5e5ec9ccf
2026-11-02   904008   85490265  8efff770cddcfb0477f08da68070af51e3e4b963b7843d676ef5eff3f74d3f9a
2026-11-03   876135   83218194  f83bcd1c592e13d554d8d598b220e27d748e0a979960fd8f8fb5cee97fde2973
2026-11-04   967704   91010907  2a59a784114b6e7e40c3705d89ba818a2bcafc77fc0be6a58037af3798354668
2026-11-05  1039172   96072093  5e23f618c54900a2bb98afda7587f619ccf44993d599a4a893287de6191fae4d
2026-11-06  1031286   96467312  a88d87fe1943c2b6dfda923791f952f4a8bf572d97871be3427b7f2d956c37ab
2026-11-07   940416   88447452  fc7478f338685c9a5883257dd1075481a50010429af332828c574cfeeb68019d
2026-11-08   913050   84872600  27f45283401139f37d2263da5916e4b8eea7c97a0aa5d49a645cc8d213f70a49
2026-11-09   974240   91834943  12539d5517b68f9f7e290d94cac82087b444ebb8c44ca9a0ba317dd8fe36852d
2026-11-10  1046382   98120412  1d852a067153fd5dc0ecc13b4efbb56ad78576d59380a938489c965cac0e145b
2026-11-11   968939   91114700  cb36f9c0db6ab02c61c72cbb5512d3c89b053a6e2039bdfcadbe11cd2d8dfc4a
2026-11-12   964789   91001678  dd382871604b00db2117da8728b6c18f972172471f909c9be5cde9ca07188e98
\end{verbatim}
\endgroup
