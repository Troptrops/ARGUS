# ARGUS Surface Support v0.4.2 — open research source

**Public source distribution (for review; no prize decision implied).** Experimental tool for auditing **positive native-grid predicted-surface bytes** in stored vs absent *masked CT Zarr chunk* regions. Not a papyrus-identity, ink-recognition, or geometric-registration validator.

## Start

1. Extract this ZIP (do not launch within Windows compressed-folder view).
2. Double-click `RUN_HELDOUT_24.cmd` on Windows (Python 3 installed; no additional package required for capture).
3. Upload the resulting `ARGUS_04_HELDOUT_CAPTURE.zip` even if incomplete. Or perform separate verification with `RUN_VERIFY_CAPTURE.cmd` (optional `blosc2` + `numpy`).

The frozen 24-cell plan in `protocol/HELDOUT_PLAN.json` was selected independently of all newly sampled prediction values/CT-storage states from a **previously chosen R04 region**, excluding 18 earlier inspected prediction keys. It is NOT random across the full PHerc0211 scroll. See `protocol/SAMPLING_AND_LIMITATIONS.md`.

## Tests

```bash
python -m pip install blosc2 numpy  # needed for decoding tests, NOT for data capture
python -m unittest tests.test_heldout_04 -v
python tools/heldout_capture.py --dry-run
```

Nine held-out tests are packaged. The separate private research bundle (not this clean source candidate) has the 0.3 historic fixtures and 82 tests (one optional skip). The held-out capture was completed on a user Windows machine on 22 October 2026 (America/Toronto). Its archived raw bytes and receipts were independently reverified in this analysis; no new live S3 requests occurred in this workspace. See `evidence/heldout_24/RESEARCH_REPORT.md`.

## Known comparison

The six previously selected illustrative chunks had 11,743,996 independently reproduced nonzero prediction voxels: 5,223,732 within missing masked CT chunk storage in two flagged examples and 6,520,264 in stored CT storage across four comparator examples. Selection bias means these cannot be pooled to estimate scroll-wide prevalence. Raw captured blocks are not included in the public-source candidate; the derived report and summary are provided for context. Do not claim physical sheet or ink identification.

The public [`vesuvius-phantom-audit`](https://github.com/Schurkai/vesuvius-phantom-audit) already performs a broad cross-scroll storage audit with voxel-level checks and boundary cleanup. ARGUS does **not** claim priority for voxel-level auditing or established superiority. A useful complement could be the small, fixed-sample, raw-receipted external verification workflow; measure actual improvement first.

## Release / licensing

Only newly authored ARGUS modules/tools/tests are shipped under `LICENSE` (MIT). Previously supplied `legacy/` programs and user-captured raw data are excluded. Verify public source-data terms and upstream dependencies before distribution. Before competition submission complete independent geometric registration, a clear benchmark of usefulness against existing tooling, a clean Windows Python 3.13 test, public GitHub release and transparent prior-art comparison. See `docs/RELEASE_CHECKLIST.md`.

## Completed held-out audit (22 October 2026 local)

The frozen 24-cell audit accounted for all 24 selections: 13 stored prediction chunks and 11 absent. Across the 13 stored blocks, independent verification found **19,932,389 nonzero predictions**, **8,519,612 (42.742553%)** mapping to absent masked-CT chunk storage, and **11,412,777** mapping to stored CT chunks. Five of the 13 blocks had some predicted positives in storage gaps. This is neither full-scroll prevalence nor a validated phantom-surface/ink measurement. See `evidence/heldout_24/` for derived CSV, chart, protocol limitations and standalone vectorized verification source. Raw user capture is in a separate private research-evidence archive, not this public-source candidate.


### November–December research and collaboration proposal (October submission addendum)

- `submission/NOV_DEC_2026_CRITICAL_PATH_PROPOSAL.md`: detailed dependency-based execution plan, milestones, decision gates, risk register, and collaboration invitation. **Future proposed work; not completed findings.**
- `submission/SUBMISSION_CONTINUATION_PARAGRAPH.md`: concise passage for the October Progress Prize form.
- `submission/COMMUNITY_INTRODUCTION_DRAFT.md`: respectful first contact for the Vesuvius Discord/GitHub community, with unpublished-link placeholders.
- `submission/OCTOBER_PROGRESS_PRIZE_DRAFT.md`: updated to distinguish the measured October work from the proposed November–December follow-through.

Publication and competition submission are separate actions. This repository is not evidence that the prize form has been submitted.

- `submission/ARGUS_NOV_DEC_2026_PROPOSAL_BRIEF.pdf`: 3-page PDF presentation brief (forward-looking proposal).
- `submission/EXECUTIVE_BRIEF.md`: one-page editorial overview.

## Research portfolio and contact

Extended research dossier, figures, source-derived 3D visualizations, and independent capture records: [ARGUS supporting evidence on Google Drive](https://drive.google.com/drive/folders/1FDjnVvOUv58AlGtz0MuMRPQUfDbdkbZ1?usp=drive_link). **This folder’s public viewing permission must be checked separately.**

ARGUS is an independent, open research-quality-assurance contribution developed by Spencer Tropea. Technical feedback and reproducibility reports are welcome via GitHub issues. The name refers to Argus Panoptes, a many-eyed observer; the intended spirit is close examination and honest accounting of uncertainty.
