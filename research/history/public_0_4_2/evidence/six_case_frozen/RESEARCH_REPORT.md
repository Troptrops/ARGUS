# ARGUS 0.3.3 — Six-case CT-storage comparison

**Status:** Independent raw-byte and receipt audit completed, using the two uploaded capture archives. This packet records **stored-object coverage** on the datasets' nominal shared ZYX grid, not confirmed physical or anatomical support.

## Core result

| Case | Selection | Positive prediction voxels | In absent masked-CT chunks | In stored masked-CT chunks |
|---|---|---:|---:|---:|
| R04_08 | Initially flagged | 1,120,896 | 1,120,896 | 0 |
| R04_11 | Initially flagged | 4,102,836 | 4,102,836 | 0 |
| R04_00 | Prespecified comparator | 2,025,451 | 0 | 2,025,451 |
| R04_06 | Prespecified comparator | 1,539,949 | 0 | 1,539,949 |
| R04_07 | Prespecified comparator | 893,670 | 0 | 893,670 |
| R04_09 | Prespecified comparator | 2,061,194 | 0 | 2,061,194 |
| **All six** | **Nonrandom cohort** | **11,743,996** | **5,223,732** | **6,520,264** |

**Two flagged cases:** 100% of their 5,223,732 positive voxels are in missing masked-CT storage chunks. **Four comparator cases:** 0% of their 6,520,264 positive voxels are in missing storage chunks. The comparisons are a useful **functionality / contrast demonstration**, **not** evidence of classification accuracy, statistical significance, or novelty beyond prior audits.

## Verification evidence

- Two raw Blosc captures included: `ARGUS_031_RAW_CAPTURE.zip` and `ARGUS_032_COMPARATOR_CAPTURE.zip`.
- Independently decoded all six 192 × 192 × 192 prediction blocks (7,077,888 voxels per block).
- Checked the source ZIP file checksums against capture-manifest hashes.
- Recomputed per-CT-chunk positive counts by NumPy block slicing; independently reconciled global totals with Python `bytes.count(0)`.
- Verified the four comparator prediction sample values equal 255 as frozen in the plan; all four prediction blocks had eight CT intersections marked `PRESENT`.
- Capture manifests collectively record 54 HTTP receipt entries (10 GET-200 and 44 HEAD requests). Comparators: 28 unique CT chunks were checked, all `PRESENT`. Flagged cases: 16 unique CT chunks, 6 present and 10 absent.
- The `predeclared_plan_sha256` in the comparator manifest matches **canonical JSON** (`json.dumps(plan, sort_keys=True).encode()`) as written by the capture code; it is not the raw file hash of the pretty-printed `plan.json` file. This difference was verified and is not evidence of altered selection.
- The frozen survey origin hash recorded in the plan also matches the original archived 18-point survey document.
- Five local unit tests passed, including exact-cover checks across CT chunk boundaries.

## Selection bias and limitations

1. **Nonrandom sample.** The original 18-point survey supplied six prediction-positive sample locations. The two flagged cases were chosen because their *sample CT chunks* were absent; the four comparator cases were the remaining prediction-positive *sample CT-nonzero* locations. The separation between groups was therefore partially built into the selection. Do **not** report a generalizable classifier accuracy, specificity, sensitivity, or p-value from these six cases.
2. **Only masked-CT storage.** Zarr v2 metadata defines zero fill for unstored chunks. An unstored object does not mean that the unmasked scan contains no physical sheet, or even that the representation is wrong.
3. **Unverified registration.** The reported alignment uses matching array shape and index coordinates. The physical origin, resampling, transformations and surface-registration equivalence have not been independently checked.
4. **No artifact identity conclusion.** Prediction-positive voxels do not identify papyrus, ink or false sheet geometry without additional spatial and physical validation.
5. **Provenance scope.** The captured HTTP timestamps and ETags are recorded by the Windows run; SHA256 validates the uploaded file bytes and internal consistency, not third-party attestation of the remote server.

## Defensible submission wording

> ARGUS performs voxel-resolved inspection of predicted surface labels against the storage footprint of a masked CT Zarr volume. In a six-chunk, deliberately selected PHerc.211 demonstration, independently decoded source data contain 11,743,996 nonzero surface-prediction voxels: 5,223,732 located within absent masked-CT chunk objects across two flagged cases, and 6,520,264 located within stored CT chunk objects across four prespecified comparators. These counts verify storage-audit behavior under an assumed common voxel grid; they are not evidence that any reconstructed physical surface is invalid, nor an unbiased estimate across the scroll.

## Next scientific decision

**Priority 1:** Freeze a new **held-out cohort** using deterministic coordinates or random selection independent of both prediction intensity and CT storage state; evaluate **all** sampled cells, including negative-prediction chunks, and report prevalence and error bars with spatial block dependence.

**Priority 2:** Audit voxel-index registration and compare flagged regions against original unmasked CT and/or validated surface geometry before using the word "phantom".

**Priority 3:** Benchmark coverage and usability against upstream `vesuvius-phantom-audit` and document a genuine, practical improvement (voxel-level fractions and reproducible provenance alone may or may not satisfy reviewers). Publicly release with tests and sample data, and ask for independent reproduction.

**R12 status:** remains `UNRESOLVED_PHYSICAL_ANOMALY`; Gate 7F `BLOCKED`. This six-case analysis is separate from R12 ink investigation.

## Reproduce locally

```bash
python -m pip install numpy blosc2
python verify_six_cases.py ARGUS_031_RAW_CAPTURE.zip ARGUS_032_COMPARATOR_CAPTURE.zip ./reproduced
python -m unittest discover -p 'test_*.py' -v
```

This package intentionally includes both raw ZIP inputs and the Python verifier, along with machine-readable audit results, per-chunk CSV, and the source-derived figure.
