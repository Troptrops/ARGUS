# ARGUS 0.4 Frozen Held-out Sampling Protocol

## Scientific question

Within a small historical R04-parent native CT region, and independently of the six already examined cases, what proportion of **nonzero native-grid prediction voxels** falls in nominally matching coordinates where the **masked CT Zarr has no stored chunk object**? Which sampled cells lack a prediction chunk altogether? Is the function of ARGUS reproducible with raw compressed bytes and source HTTP receipts?

## Prespecified sampling frame

- Arrays: PHerc0211 native masked CT and m7 prediction, both nominal shape `[19416,7948,7948]`; prediction chunks `192³`, CT chunks `128³`, ZYX axis convention assumed.
- Historical R04 halo half-open bounds: Z `[17770,19282)`, Y `[5136,6256)`, X `[4368,5488)`. Boundaries derive from earlier R04 extraction, not new surface discovery.
- Candidate prediction-chunk grid: indices Z 92…100, Y 26…32, X 22…28 (441 cells).
- Exclusions: **18 unique prediction chunk keys** sampled at 18 historical survey positions. The list and raw archived survey JSON are locked in `HELDOUT_PLAN.json` / `HISTORICAL_POINTS_EXCLUSION_SOURCE.json`.
- Eligible: 423 cells. Sort each cell within Z strata (92–94, 95–97, 98–100) by SHA256 of `ARGUS-2026-10-22-HELDOUT-24-PREDECLARED-V1|<chunk-key>`; select first 8 in each stratum. Freeze 24 selected keys, without querying those cells' prediction values or CT status.
- Plan canonical hash: stored in `HELDOUT_PLAN.sha256`; verify `python tools/heldout_capture.py --dry-run` before online retrieval.

## Fixed measurement and inference rules

1. Query the **entire** selection, even when prediction chunk is absent, all-zero or inaccessible. Never substitute another location for it.
2. Fetch exact remote `.zarray` metadata and require source hashes/shape/chunks/dtype/fill to match previously captured metadata; fail closed if changed.
3. For each selected prediction key, HTTP GET raw Blosc chunk. `200` stores bytes; `404` records absent chunk (zero-fill); other code/error remains unknown.
4. For **every sampled cell**, HEAD all geometrically overlapping CT storage chunks, deduplicated. HTTP `200` means stored CT chunk; `404` means absent object; transient/network errors stay `UNKNOWN`. No inferred CT voxel intensities.
5. Independent offline decoder counts nonzero prediction bytes within exact intersection boxes; verify global counts using `.count(0)` and optionally NumPy slicing.
6. Report all sampled locations, source SHA256 and receipts, missingness, storage-conditioned positive counts, and incomplete classifications. Never silently drop failed cells.
7. A single exploratory pooled fraction may be reported **only if all 24 sampled predictions have resolved status and all overlapping CT storage states are known**. Otherwise report incomplete-data bounds or explicit null and unknown counts. Do not calculate scroll-wide prevalence, significance tests or naive confidence intervals from spatially dependent adjacent cells.

## What this protocol cannot establish

- Physical identity of a papyrus winding, phantom geometry, ink, writing, or surface-registration accuracy.
- Absence of CT content from the **unmasked** scan; masked Zarr 404 simply indicates missing storage under declared fill convention.
- Population-wide calibration beyond this conditional local R04 frame, which was itself chosen through prior work.
- New method novelty over Schurkai's cross-scroll chunk audit, voxel-level verification and cleanup. A concrete independent workflow advantage must be demonstrated separately.

**Selection / outcome firewall:** Plan keyed cells are frozen with local hash, but not third-party timestamped. Six earlier handpicked cases remain reported separately; never pool them with this audit for a random sample estimate.
