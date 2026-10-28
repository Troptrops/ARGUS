# ARGUS Surface Support 0.4.1 — Independently Verified Held-Out Audit

**Date:** 22 October 2026, America/Toronto (capture on 23 October 2026 UTC)  
**Scroll:** PHerc. 211 (`PHerc0211`); masked native CT dataset and m7 surface-prediction label volume  
**Status:** `COMPLETE_RAW_BYTE_VERIFIED; STORAGE_SUPPORT_ONLY; REGISTRATION_NOT_INDEPENDENTLY_TESTED`  
**Study:** prespecified, deterministic local R04-region held-out selection; **not** a scroll-wide random sample.

## Headline finding

The 24-cell frozen survey captured 13 stored prediction chunks and 11 absent (`404`) prediction chunks. Independently decoding the **13 original Blosc chunks** yielded **19,932,389 nonzero prediction voxels**. Of these, **8,519,612 (42.742553%)** occupy nominal coordinates for which no masked native-CT Zarr chunk object was stored; **11,412,777 (57.257447%)** occupy stored CT-chunk regions. No CT or prediction outcomes were unknown.

This is a **ratio of positive prediction voxels within the prespecified captured sample**, not the fraction of the PHerc. 211 scroll, its surfaces, or physical material that lacks valid CT. It is neither an unbiased whole-scroll prevalence estimate nor an error rate for an ink detector.

## Reproducibility / integrity

- Frozen canonical selection SHA-256: `a8bcb68978589f8314952f64e8243d556628bcf76a038bf371f077aa20964d97`.
- Sampling frame: 423 eligible prediction-grid cells intersecting the historic R04 halo, **after excluding all 18 previously inspected survey keys**.
- Hash-ranked selection: eight chunk-grid cells in each of three predetermined Z strata (24 total), using a fixed seed and without querying their prediction values or CT storage first.
- Capture: `ARGUS_04_HELDOUT_CAPTURE.zip` with **212 uncached HTTP request receipts** (26 GETs including two metadata files; 186 HEAD checks of distinct CT chunks). 13 compressed chunk byte streams retained, 11 prediction `404`s retained.
- Stored native masked-CT chunk inventory: **75 present**, **111 absent**, across 186 distinct CT keys. This chunk-inventory ratio is NOT itself a voxel-support ratio.
- Metadata SHA-256 hashes are fixed; decoded arrays have declared `192 × 192 × 192` `uint8` prediction chunks; CT has `128 × 128 × 128` chunks and Zarr-v2 `fill_value: 0`.
- Two verification implementations agreed exactly: the original ARGUS row-wise-count verifier plus an independent vectorized, eight-block-per-chunk slicing implementation. Both checked the stored HTTP receipts, original byte SHA-256 hashes, and completeness of each per-chunk CT partition.
- All 24 planned keys were accounted for. No failed responses were silently discarded or replaced.

## Cell-level results

| Outcome | Count / measurement |
|---|---:|
| Prespecified sample | 24 prediction grid cells |
| Prediction chunk stored | 13 |
| Prediction chunk absent | 11 |
| Stored prediction chunks with some positive voxels in absent CT-chunk regions | 5 of 13 |
| Stored prediction chunks with **all** positive voxels in absent CT-chunk regions | 2 of 13 |
| Positive prediction voxels in absent CT-storage regions | 8,519,612 |
| Positive prediction voxels in stored CT-storage regions | 11,412,777 |
| Total nonzero prediction voxels | 19,932,389 |
| Positive-voxel-weighted storage-gap share within the sampled chunks | **42.742553%** |

The five cells with nonzero predictions in CT-storage gaps were `H06`, `H07`, `H10`, `H11`, and `H13`. `H06` and `H13` had all of their positives in absent CT-chunk storage; the remaining three were mixed. Of the 11 absent prediction chunks, eight were in the highest predefined Z stratum.

### Z-stratum transparency

| Z prediction-chunk stratum | Selected cells | Stored prediction | Absent prediction | Positive voxels | Positives in absent CT storage |
|---|---:|---:|---:|---:|---:|
| 92–94 | 8 | 7 | 1 | 9,332,548 | 2,789,605 |
| 95–97 | 8 | 6 | 2 | 10,599,841 | 5,730,007 |
| 98–100 | 8 | 0 | 8 | 0 | 0 |

**Important:** The top Z stratum having eight absent prediction chunks reflects strong geographic/scan-boundary dependence. Because this is a hash-ranked stratified selection of grid cells, not a spatially independent probability sample of scroll surfaces, naive voxel-level confidence intervals and statistical significance tests would be misleading.

## Relationship to the earlier six-case study

The earlier separately selected six chunks comprised two flagged discrepancies (5,223,732 positive predictions mapping to absent CT storage) and four intentionally contrasting comparators (6,520,264 positives mapping to stored CT storage). The six earlier cases were conditioned on initial spot-check outcomes; they remain **descriptive demonstrations** and must **not** be pooled with the new 24-cell sample to estimate rates.

Unlike the six selected cases, the 24 new locations were fixed without observing their new CT-storage states or prediction intensities. This supports a modest conclusion: the storage-gap phenomenon exists **beyond the original handpicked cases** in the prespecified local frame.

## What ARGUS does not establish

1. **Papyrus truth:** `404` in a *masked* CT Zarr indicates absent stored chunk data, not missing or phantom papyrus in the physical scroll. Zarr uses `fill_value: 0` for missing chunk objects.
2. **Physical alignment:** equal array shape and nominal ZYX indices do not independently prove that the prediction and native CT scans are correctly physically registered.
3. **Inside-the-halo localization:** cells were *selected because their prediction chunks intersect* the R04 halo; the positive counts are from their **full 192³ chunks**, including portions beyond the precise halo. This is not an R12 or arbitrary-pixel ROI analysis.
4. **Whole-scroll inference:** the R04 parent region was historically identified in earlier exploratory work, and nearby chunks are spatially correlated. No whole-scroll prevalence, statistical confidence interval, or p-value follows from these 24 samples.
5. **Method novelty:** Schurkai's public `vesuvius-phantom-audit` already identifies broad chunk- and voxel-level support defects and offers cleanup. ARGUS has not yet established superiority or a previously unknown defect category. Its candidate value is an auditable compact acquisition, preregistered local comparison, and independent reproducibility workflow.
6. **Writing/ink:** this is not evidence of legible text; R12 and Gate 7F remain unresolved/blocked.
7. **Independent server attestation:** SHA-256 verifies internal consistency of downloaded local bytes and the archived HTTP receipts. It does not establish an independently signed attestation from the storage provider.

## Recommended next actions before the October submission

1. Publish a minimally tested, MIT-licensed public source package without proprietary legacy scripts, and confirm third-party data-use terms. Make results and selection reproducible by command.
2. Demonstrate a concrete user-facing difference from existing phantom-audit tooling (e.g., compact fully receipted audit, exact per-CT-intersection provenance, and frozen sampling). If there is no meaningful gap, contribute upstream instead of overstating independent novelty.
3. Run independent geometry-registration and native CT pixel support comparisons, preferably in a second scan region, before making phantom-geometry claims.
4. Verify a clean Windows Python 3.13 run and seek technical critique. Freeze a tagged public release and submit truthful verified language through the official progress-prize entry process.

## Reproduction

The evidence ZIP bundles the original captured bytes and both verifiers. With Python, NumPy and Blosc2 available:

```bash
python verify_independent.py ARGUS_04_HELDOUT_CAPTURE.zip
```

The script writes `INDEPENDENT_AUDIT.json`, `CASE_COUNTS.csv`, and `PARTITION_COUNTS.csv`. The original ARGUS verifier is in the 0.4 project source at `tools/heldout_verify.py`.
