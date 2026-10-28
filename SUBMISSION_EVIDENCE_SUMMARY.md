# ARGUS Surface Support | October 2026 research evidence

## The problem

Predicted surface labels can occupy nominal index positions where **masked-CT Zarr chunks are not stored**. A rendering alone does not explain the storage provenance of those predictions. Prior published work has reported this general issue; ARGUS studies whether a compact, source-byte-auditable workflow can help investigators inspect it.

## The completed local PHerc.211 study

A frozen 24-cell *local* sample was drawn from 423 eligible prediction-grid cells in a previously selected R04-region sampling frame, excluding the 18 previously queried prediction keys. The sampling plan and hash are stored in `protocol/`.

- **24 selected cells:** 13 stored prediction chunks and 11 absent prediction chunks.
- **19,932,389** positive prediction voxels across the 13 stored chunks, independently re-decoded.
- **8,519,612** positive voxels (**42.742553%**) nominally map to absent *masked CT chunk objects*; **11,412,777** map to stored chunks.
- **5 of 13** stored prediction chunks include positives in CT-storage gaps; **2** were entirely in such areas.
- **186 unique CT chunk statuses** checked, with **212 recorded uncached HTTP requests** overall.
- The counts were reproduced by **two independent counting implementations** and reconciled with byte hashes and recorded network receipts.

The **24-cell plan regenerates exactly; independent external preregistration chronology is not attested**, but the larger R04 area had been chosen previously: these are not independent whole-scroll random observations. All positive-voxel counts use full prediction chunks, not only the portion intersecting the local R04 halo. The 42.74% is not a physical false-surface rate or whole-scroll rate.

## H11 original-data example

One 192³ prediction chunk has **279,426** positive labels. **196,608** form an exact rectangular **64 × 16 × 192** slab at local Z=128…191, Y=176…191, X=0…191, nominally in absent masked-CT storage. Another **82,818** positives map to stored CT-chunk regions. The slab was present in the original prediction array, prior to 3D visualization. Its cause has not been established.

## Six earlier selected comparison cases

Two historically flagged cases comprised **5,223,732** positives mapped to absent CT storage; four selected contrast cases comprised **6,520,264** positives mapped to stored CT objects. The examples were chosen after preliminary status screens and are strictly descriptive.

## What this does not prove

No independent geometric registration; no proof of a false papyrus reconstruction, physical papyrus absence, ink, writing or a novel model defect. Missing masked-CT storage and original source CT availability are not identical. Prior voxel-level auditing exists. An independent head-to-head practical benchmark is a **planned November task**, not a completed October result.

## Reproduction and review

- Fixed selection: `protocol/HELDOUT_PLAN.json` and `.sha256`.
- Code: `tools/heldout_capture.py`, `tools/heldout_verify.py` and `tools/verify_heldout_vectorized.py`.
- Case-level derived outputs: `evidence/` and `figures/`.
- The already-public capture is retained unchanged under `ARGUS_04_HELDOUT_CAPTURE.zip`; use the README offline replay commands. No new raw data is added, and prediction-asset redistribution terms remain unresolved.
- Annotated limitations: `evidence/HELDOUT_24_RESEARCH_REPORT.md` and `docs/DATA_RIGHTS_AND_PRIOR_ART.md`.
