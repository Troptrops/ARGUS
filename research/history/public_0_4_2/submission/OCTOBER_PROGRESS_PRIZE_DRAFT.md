# ARGUS Surface Support — October 2026 Progress Prize draft (NOT SUBMITTED)

**Proposed project:** ARGUS: reproducible positive-prediction/CT-storage support inspection with compact source-byte provenance and a prespecified local holdout.

**Repository URL:** [NOT PUBLISHED]

**Release commit/tag:** [PENDING]

**Evidence reproduction URL:** [PENDING]

## Problem / context

Some published predicted surface-label volumes include positive predictions over masked CT regions without stored chunks. Existing work from Schurkai has already documented this across scrolls and includes voxel-level checks and cleanup. ARGUS focuses on producing a compact case-level raw-evidence audit for external checking, with a frozen local sample and detailed source receipts; **not** on claiming original discovery of this artifact category.

## Verified six-case historical demonstration (biased selection)

In PHerc0211, two previously flagged prediction chunks contained 5,223,732 nonzero predicted voxels that mapped to absent native masked CT chunk objects under the nominal shared grid. Four previously identified comparator chunks contained 6,520,264 nonzero predicted voxels mapping to stored masked CT objects. Independently decoded six original Blosc blocks; all raw byte and partition counts reconciled. Selection was conditioned on prior sample storage states, so this is not a prevalence measurement.

## Prespecified held-out 24-cell experiment

The 24 prediction-grid cells were selected with no outcome-peeking from 423 eligible R04 halo cells (excluding prior 18 survey keys), with SHA256 plan recorded. The user Windows capture was completed on October 22, 2026 local time. All 24 predeclared selections and 186 unique CT chunk checks have known states. From 13 stored prediction chunks (11 others absent), 19,932,389 nonzero prediction voxels were independently decoded, of which 8,519,612 (42.742553%) occupy absent masked CT-chunk regions and 11,412,777 occupy stored CT regions. Two independent count methods reconciled. See `evidence/heldout_24/RESEARCH_REPORT.md` and the original raw capture in the separate private evidence bundle. The measured fraction is a *sampled-full-chunk positive-voxel ratio*, not an estimate of overall scroll phantom rate; the R04 frame, local spatial dependence and unvalidated registration prevent that inference.

## Innovation and usefulness — to demonstrate, not assume

Potential practical addition: a no-Colab, stdlib-only Windows capture of a fixed small sample containing source bytes and receipts, with independent, precise, per-CT-intersection positive counts. Benchmark against the already-published phantom audit and prioritize a reproducible user benefit. It may be better to contribute these features upstream if functionally overlapping.

## Limitations

- Only stored masked CT Zarr chunk status, not the unmasked original scan or verified real material.
- Physical voxel alignment and papyrus sheet identity are not independently established.
- No ink, legible letters or validated R12 discovery.
- Local held-out sample not random over entire scroll; neighboring chunk correlations and previous area selection preclude simple global inference.
- No independent third-party attestation of downloaded bytes beyond local SHA256 and recorded HTTP metadata.

## Before submission

Complete independent coordinate-registration benchmarking, clean-room Windows reproduction beyond the already completed capture, public code hosting, novelty and user-utility comparison to existing open-source work, licensing checks, and source URLs or reviewer feedback.

## November-December follow-through: critical path and community collaboration

## Continuation and collaboration (November–December 2026)

This submission is intended as the first independently reproducible increment of ARGUS, not as a one-off prize artifact. The immediate objective is to make support-state checks easy for researchers to reproduce, interpret, and act on before downstream surface tracing or ink analysis. I recognise that Schurkai's published phantom audit already provides scroll-wide chunk analysis, voxel-level checks and cleanup; any ARGUS feature must earn its place through a fair benchmark or become an upstream contribution.

**November's critical path** is: (1) publish a clean, versioned and reproducible release; (2) benchmark equivalent inputs against established approaches; (3) independently validate prediction-to-CT registration and masked-volume semantics; then (4) demonstrate a practical triage or integration example. Failure at the registration gate limits the tool to explicitly labelled storage-support findings rather than claims about physical papyrus.

**December's target** is a second predeclared validation region or scroll, stable cross-platform reproduction, an actionable machine-readable export, and a documented community review or upstream contribution where useful. I will publish negative results and unresolved issues with the same care as successful demonstrations.

I would welcome technical correction of the coordinate assumptions, suggestions for the most useful existing workflow to integrate with, and independent reproduction of one fixed case. My intention is to contribute a maintained tool or targeted improvements to existing projects beyond the October prize decision, not to seek endorsement or privileged access. The detailed gates, risks and deliverables are in `submission/NOV_DEC_2026_CRITICAL_PATH_PROPOSAL.md`.

**Full proposed roadmap:** `submission/NOV_DEC_2026_CRITICAL_PATH_PROPOSAL.md`. **Public/community note (not posted):** `submission/COMMUNITY_INTRODUCTION_DRAFT.md`. This plan is forward-looking; October’s completed evidence and the pending public-release requirements remain unchanged.
