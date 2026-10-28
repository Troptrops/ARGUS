# ARGUS Surface Support | November-December 2026 Critical-Path Proposal

**A reproducible surface-support quality-assurance workflow for the Vesuvius research ecosystem**  
**Status:** Forward-looking technical proposal accompanying the October 2026 Progress Prize submission draft; **not** work already completed.  
**Contributor:** [Contributor name / GitHub handle]  
**Version:** Proposal 1.0, October 22, 2026

## Executive intent

ARGUS is being developed as a small, inspectable quality-assurance layer between surface prediction and subsequent unwrapping or ink analysis. Its purpose is to tell researchers *where a predicted surface label does and does not have corresponding stored masked-CT evidence*, while preserving enough source provenance to reproduce that judgment. It is not a papyrus or ink classifier. The near-term ambition is not to duplicate the existing phantom-audit ecosystem but to identify a concrete missing function, implement it well, and contribute it wherever maintainers think it belongs.

The October evidence provides a specific foundation. In a **prespecified, locally stratified 24-cell study** on PHerc. 211, 13 cells had stored prediction chunks and 11 did not. Independent decoding recovered **19,932,389 positive prediction voxels** across the 13 stored chunks; **8,519,612 (42.742553%)** fell at indices whose corresponding *masked CT Zarr chunk objects* were absent. All 24 locations and 186 distinct CT chunk-object statuses were accounted for. Two separate counting implementations agreed. Earlier six-case data are reported separately because those examples were selected based on prior observations.

The conclusion is deliberately narrow: these are verified *storage-state/label overlap* measurements on the nominal grid, **not** a scroll-wide prevalence estimate, a finding of physical papyrus absence, or evidence of ink. Prediction-to-native-CT physical registration remains unverified. Existing work, especially Schurkai's `vesuvius-phantom-audit`, already studies phantom predictions, performs voxel-level checks and provides cleanup. ARGUS must prove complementary utility rather than claim priority over that work.

## The critical path

**Path to a useful contribution:** October evidence + publicly runnable release → equivalent-baseline benchmark → independent registration audit → demonstrable researcher action / integration → external reproduction → stable, maintainable release.

**Rule:** a failed or unresolved gate does not get converted into a positive scientific claim. We may still publish the data-quality tool with an explicit *storage-support only* label.

| Stage / target window | Dependency and work | Required deliverable / exit gate | Owner / fallback |
|---|---|---|---|
| **G0 · Oct 23-31** | Public release readiness, licensing and data-rights check, clear reproducibility from source. Complete a fair benchmark plan without changing held-out outcomes. | Public URL and immutable commit or tag; Windows Python 3.13 and Linux smoke tests; all results reproducible from documented inputs, with any untested platform labeled. **October submission only asserts verified outcomes.** | ARGUS contributor. If license or reproducibility fails, disclose the blocker and postpone claims of a release. |
| **G1 · Nov 2-6** | Compare like-for-like against published `vesuvius-phantom-audit` and, where relevant, existing data tools. Re-run on identical sample, grid, threshold and fill semantics. | Table of agreement, differences, runtime, memory, network bytes, failure behavior, and provenance artifacts. One actual unmet user need identified, or a decision to upstream rather than duplicate. | ARGUS contributor; invite audit maintainer feedback, not approval as a dependency. |
| **G2 · Nov 9-13** | Independently examine shared-grid provenance: volume ID, axes, origin, transforms, mask semantics, resampling/crops, known CT/prediction landmarks, and edge cases. | Registration test report with uncertainty and failure cases; explicit `REGISTERED`, `NOT_REGISTERED`, or `UNRESOLVED` gate. **Only pass `REGISTERED` with independent coordinate evidence.** | ARGUS contributor; request a geometry specialist's review. If unresolved, restrict outputs to storage-state language. |
| **G3 · Nov 16-20** | Turn the verified audit into one actionable workflow: flag a selected risk region, export traceable mask/CSV/JSON, and hand it to a reconstruction workflow or upstream maintainer. | Reproducible before/after or triage example showing what decision a user can make. Confirm standard Zarr input and consistent outputs; optional tifxyz/VC3D integration only after a documented contract. | ARGUS contributor; upstream PR if maintainers welcome it. If no integration access, ship a standalone example and small API. |
| **G4 · Nov 23-30** | Freeze a second independent region or scroll *before* reading results, and repeat the same audit. Preserve negative/absent/failed observations. | External-region validation report, denominator and selection method, error budget, raw-hash manifest, and honest comparison to PHerc. 211. No claim of generalization unless data support it. | ARGUS contributor. If access fails, publish the prespecified plan and a failure report; do not substitute favorable cases. |
| **G5 · Dec 1-11** | Stabilize and seek reproducibility: clean Windows/Linux install, CI fixture, versioned schema, optional no-GPU demo, memory/network-budget test, docs. Invite one independent user to reproduce a fixed case. | Versioned v0.5 candidate, installation video or walkthrough, reproducibility checklist, resolved/triaged issues. Outside reproduction is a target, not a guaranteed outcome. | ARGUS contributor; volunteers only if interested. Without reviewers, release a self-contained replay fixture and document lack of external validation. |
| **G6 · Dec 14-18** | Release a technical note and maintenance plan, with reviewer feedback, unresolved concerns, upstream issue/PR status and 2027 priorities. | Stable release candidate, changelog, open limitations, dataset citations, measurable benchmark, and a clear accept/iterate/deprecate decision. | ARGUS contributor. If benchmark shows no unique value, recommend upstream merger or retirement of duplicate functionality. |
| **Dec 21-31 · Buffer** | Holiday/maintainer availability, follow-up reviews, documentation, issue triage. | End-of-year status note; no dependency on receiving a prize, job offer or team invitation. | ARGUS contributor. |

### Critical dependencies and go/no-go gates

- **G0 before outreach:** anyone reviewing ARGUS should be able to access the code and reproduce at least a fixed result; a ZIP on a private computer is not a public release.
- **G1 before a novelty claim:** if an upstream tool already produces the same output with comparable reproducibility, prioritize a small compatible improvement or pull request over a competing product.
- **G2 before geometry or phantom claims:** identical array shape and a masked-CT 404 do not establish physical alignment or missing papyrus. If registration cannot be verified, every export must label the result `STORAGE_SUPPORT_ONLY`.
- **G3 before declaring impact:** show a changed researcher decision (for example, triaging a mask boundary before sheet tracing), not merely a large count or attractive visualization.
- **G4 before transfer/generalization:** independent prespecified sampling, documented exclusions and denominator, and a clear report of empty/unavailable data.
- **G5 before calling it community-validated:** independent reproduction is *requested*, never reported as successful until somebody actually does it.

### Quantifiable acceptance targets (proposed, not achieved)

| Dimension | Planned measure | Minimum interpretation |
|---|---|---|
| Numerical correctness | Exact agreement with a reference or separately implemented decoder on fixed raw chunks; hash-verified inputs | Required for any published quantitative case |
| Sampling discipline | Frozen sample manifest, immutable fingerprint, no dropping empty results | Required for independent-region studies |
| Practicality | Report wall time, peak memory, bytes downloaded, and error recovery on commodity Windows and Linux | Figures reported, with no unsupported speedup claim |
| Integration | Machine-readable risk summary and coordinates, standard Zarr input, stable schema and documented example | One independently repeatable downstream decision |
| Scientific boundary | Explicit source grid, mask semantics, fill value and registration state in every report | Unknown values remain unknown |
| Community | Public issue tracker and reproducible question for maintainers; record feedback or lack thereof | Participation is measured by artifacts, not implied acceptance |

## Work packages beyond the critical path

**WP-A — Storage-support instrumentation (primary, Nov-Dec).** Strengthen Zarr V2 handling, metadata checks, exact voxel/chunk intersections, source evidence, robust failure states, and outputs that reconstructors can consume. This remains the contribution most directly supported by October data.

**WP-B — Geometric validity (conditional, Nov).** Compare candidate surfaces with native unmasked CT where publicly authorized, establish coordinate transforms and mask-edge cross-sections, and test independently known geometry. Any failure prevents assertions about physical papyrus support and creates a targeted bug report instead.

**WP-C — Downstream intervention (conditional, Nov-Dec).** Demonstrate whether ARGUS enables safe rejection, annotation, or prioritized inspection of a risky segment and whether that intervention helps existing VC3D/villa or surface-prediction workflows. This requires a before/after demonstration with held-constant inputs, not just a screenshot.

**WP-D — R12 scientific investigation (separate exploratory track; not on October/November core critical path).** Preserve the frozen 55-plane R12 +13...+15 voxel hypothesis; recover and independently validate R12 physical coordinates; compare profiles against spatially and geometrically matched controls. No text decoding or Gate 7F progression absent physical and statistical support. Allocate effort only after G0-G2 and without taking evidence away from the public QA track.

## Risk register

| Risk | Earliest indicator | Response |
|---|---|---|
| Prior work already solves the main problem | G1 benchmark shows near-identical results and usability | Offer upstream receipts / deterministic replay as a patch; redefine project narrowly, or retire duplication |
| Prediction-to-CT registration is uncertain | Transform or landmarks cannot be independently reconciled | Keep storage-state-only output; exclude phantom/material/ink claims |
| Masked CT zeros misread as physical absence | Dataset fill value or original unmasked CT differs | Report storage object state separately from voxel intensity and material interpretation |
| Regional selection bias | Large differences between R04 strata / neighboring samples | Preserve strata, sampling manifest, all missing results; do not quote whole-scroll percentages |
| Remote data changes | Chunk hash or object status differs on replay | Record source URL, timestamp, size, SHA-256 and status; version runs rather than overwriting history |
| Limited external attention | No reviewer responds to polite requests | Continue public issue-based maintenance; don't claim endorsement or adoption |
| Sole-contributor bandwidth / credits | Integration stalls or data cost rises | Protect G0-G2; ship smaller tested increments; no dependence on Colab/Codex credits |

## A concrete invitation to the research community

> I am contributing ARGUS as a reproducible, source-auditable quality-assurance tool for surface-prediction data. The first results are intentionally modest: they identify positive prediction labels overlapping absent masked-CT storage, not verified absent papyrus or writing. I recognize and credit existing phantom-audit work. My November-December plan is to benchmark fairly, independently test registration, and either integrate one useful capability into the existing toolchain or contribute the missing functionality upstream. I would particularly welcome correction of our coordinate assumptions, suggestions for the most useful integration point, and independent attempts to reproduce a fixed case. I am happy to adapt the project to community priorities and to maintain it beyond any prize decision.

**Specific low-friction requests** (optional): (1) point me to the authoritative prediction/CT registration and masking semantics; (2) recommend a concrete existing workflow where a traceable per-voxel support report would help; (3) review one comparison case or one small proposed upstream pull request. No endorsement, role, private data or computing allocation is assumed.

## Deliverables offered by year-end

A well-scoped, versioned QA package; a reproducibility fixture and raw-byte manifest; a benchmark against the existing phantom audit; registration-status report; an independently selected second-area report or an honest access failure; a practical integration or documented upstream contribution; and an open issue/limitations log. These are **proposed deliverables**, conditional on technical feasibility and actual reviewer availability, not accomplished outcomes.

## How this should appear in the October submission

Keep the **October measurements and open-source link** as the central body of the entry. Add a **150-250 word 'Continuation & Collaboration' paragraph** pointing to this full roadmap. A detailed proposal is an appendix, not a substitute for demonstrating utility. Publicly release only what you have the rights to redistribute. Do not include private captures or unlicensed legacy files in the public GitHub repository.

### References / prior art

1. Vesuvius Challenge, [Progress Prizes and submission criteria](https://scrollprize.org/prizes), accessed 2026-10-22.
2. Vesuvius Challenge, [FAQ: community participation and publishing](https://scrollprize.org/faq), accessed 2026-10-22.
3. Schurkai, [vesuvius-phantom-audit](https://github.com/Schurkai/vesuvius-phantom-audit), existing scroll-wide chunk audit, voxel-level validation and cleanup. Attribution and feature comparison are mandatory.
4. ARGUS 0.4.1, `evidence/heldout_24/RESEARCH_REPORT.md`, `evidence/six_case_frozen/RESEARCH_REPORT.md`, and frozen `protocol/HELDOUT_PLAN.json` (source-derived measurements, not independently established physical geometry).
