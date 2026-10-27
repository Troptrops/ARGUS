# ARGUS 0.4 changes

- Deterministic 24-cell, three-Z-stratum held-out sample from historical R04 halo; 18 earlier observed prediction keys excluded; canonical SHA locked.
- Stdlib-only Windows script `RUN_HELDOUT_24.cmd`; GET 24 frozen prediction chunk paths and all intersecting native CT HEADs, recording negative (404) and unknown cases without replacement.
- Independent raw Blosc+numpy/row-byte verifier with exact boundary-correct CT-overlap partition, full totals and source receipts.
- Network/metadata failure-safe evidence ZIP, no cache, bounded GET, retry rules, hashes and provenance.
- Nine new tests: sample lock, exclusion, tamper, source metadata, full capture+redecode, unknown handling, per-box counting, failure artifact.
- Frozen 0.3.3 selected-case evidence kept separate and original 0.3 source/tests preserved in full bundle.
- Public-release candidate excludes legacy scripts without clarified licensing and private raw captures.
- Still not executed against the 24 real held-out chunk locations; not published or submitted.
