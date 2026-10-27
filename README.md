**ARGUS Surface Support — Reproducible CT-storage auditing for PHerc. 211**

I am submitting ARGUS Surface Support v0.4.2, an independent, open-source quality-assurance workflow developed using public Vesuvius Challenge data from PHerc. 211.

**The problem:** Surface-prediction models can produce positive labels at nominal coordinates where the corresponding masked-CT dataset has no stored chunk. Researchers need transparent ways to inspect these conditions before interpreting reconstructed surfaces or using them in downstream analysis.

**The contribution:** ARGUS provides a compact, reproducible workflow that captures original prediction bytes, hashes, HTTP request receipts, CT-storage states, and per-chunk positive-voxel counts. It includes a prespecified sampling protocol and independent verification methods, without requiring a full-scroll download or GPU.

**Evidence:** In a frozen, local 24-cell sample, 13 prediction chunks were stored and 11 absent. Independent decoding identified 19,932,389 positive prediction voxels, of which 8,519,612 (42.74%) mapped to absent masked-CT storage regions under nominal index alignment. Two independent verification implementations agreed. A detailed H11 case study and earlier six-case comparison are included, together with figures, source provenance, test code, and a seven-page research dossier.

**Scientific limitations:** These findings concern masked-CT storage availability, not confirmed absence of papyrus, validated physical geometry, or ink. Independent prediction-to-CT registration remains outstanding. The results are local and cannot be generalized to the entire scroll. Earlier work, including Schurkai's phantom audit, already addresses related problems; ARGUS does not claim to have originated voxel-level auditing or demonstrated superiority.

**Future development:** My November–December critical-path proposal prioritizes benchmarking against existing tools, registration validation, independent transfer testing, practical integration, and upstream collaboration.

My objective is to contribute a useful, reproducible research tool and develop it in cooperation with the Vesuvius community. I welcome technical criticism, independent verification, and opportunities to contribute beyond the October prize decision.
