# Baseline and contribution scope

Related [vesuvius-phantom-audit](https://github.com/Schurkai/vesuvius-phantom-audit) already performs chunk-level auditing, voxel-level checks and cleanup. ARGUS does not claim to have invented this field, established false papyrus surfaces, solved registration or outperformed prior tools.

The October contribution is a compact local source-byte-auditable workflow: a frozen 24-cell plan, historical-key exclusions, metadata fingerprints, request receipts, hashes, exact storage partitions and independent counting implementations. The study concerns an already selected R04 area and whole prediction chunks; it is not a random whole-scroll study.

The October 23 comparison isolated the upstream overlapping_vol_chunks function at commit ab9ace908a1644c32ce0206e3eecfefba2c4bc81. CT overlap-key sets matched for all 24 cells. This is only a geometry-function comparison, not a pipeline benchmark or evidence of a performance advantage. The pinned source hashes and reproduction command are supplied in UPSTREAM_SOURCE_RECORD.json and tools/compare_upstream_overlap.py; that tool requires the separate private evidence tree and a separately obtained pinned upstream source file.

Registration checks, matched full-pipeline benchmarks and useful integration are future work. Equivalent prior functionality should lead to an upstream contribution, a documented niche, or retirement of redundant code.
