# ARGUS | Community introduction (draft for GitHub/Discord)

Hello everyone — I'm working on **ARGUS Surface Support**, a small reproducible QA workflow for checking where positive surface-prediction voxels overlap absent *masked-CT storage chunks* in the Vesuvius public datasets.

On a frozen, local 24-cell PHerc. 211 sample, we decoded 19,932,389 positive voxels across 13 stored prediction chunks; 8,519,612 of those map to absent masked-CT chunk objects under the nominal grid. The sampling plan and original source-byte evidence are documented. This is **not** an ink result, not physical papyrus absence, and not a whole-scroll estimate. Registration still needs independent validation.

I'm aware that [vesuvius-phantom-audit](https://github.com/Schurkai/vesuvius-phantom-audit) already covers phantom prediction auditing and cleanup. Rather than duplicate it, my next steps are to benchmark the tools on matched inputs, test grid registration and mask semantics, and provide a useful per-region, receipt-backed export or contribute a smaller feature upstream.

I'd appreciate pointers to authoritative CT/prediction transforms, the most helpful integration point in the existing pipeline, or anyone willing to try reproducing a small fixed case. I'll share code, a reproducible sample, limitations and failures openly. Thanks for any correction or guidance.

**Links before posting:** [PUBLIC REPOSITORY URL]; [REPRODUCIBILITY/RESULT URL]. Replace placeholders only after publication.
