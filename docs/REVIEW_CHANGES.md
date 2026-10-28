# Review changes - 0.4.3



| ID / severity | Problem and implication | Resolution |
|---|---|---|
| C1 Critical | Capture Fetch catches size/budget exceptions but can return stale HTTP 200 and a failed body as success | Fixed in reviewed 0.4.3; oversize/budget tests return unknown and no payload |
| C2 Critical | Capture and error handler can overwrite an existing evidence ZIP | Exclusive creation; errors get a separate timestamped ZIP; preservation regression passes |
| M1 Major | Figure 06 calls Y=176 a storage boundary | Corrected figure distinguishes label-slab edge Y=176 from stored/absent CT transition Z=128 |
| M2 Major | Reproduction commands name absent verify_independent.py / verify_six_cases.py and outdated archive paths | One maintained standalone review command plus Windows launcher; executed locally |
| M3 Major | 0.4.2 folder / 0.4.1 README / 0.4.0 packaging / 0.2.0 runtime disagree | Reviewed source consistently identified as 0.4.3; originals retained |
| M4 Major | Plan hash described as proof of outcome-blind preregistration | Selection regenerates, but hash and local dates do not independently attest chronology; wording qualified |
| M5 Major | Unfamiliar UNKNOWN state can yield false resolved-overlap classification | Normalize all non-200/404-equivalent states to unknown |
| M6 Major | Positive-partition code accepts equal-volume duplicate/overlapping boxes | Pairwise disjointness check; regression rejects overlap |
| M7 Major | Unknown storage with zero positives can be called a complete partition | Completeness now depends on storage states, not just unknown-positive count |
| M8 Major | Existing library CLI has only nine held-out tests in the source candidate; historical 82-test claim cannot certify this release | Report nine received tests and 16 reviewed tests accurately; broader platform/API validation remains open |
| M9 Major | Physical registration, native unmasked support and sheet identity remain untested | Keep STORAGE_SUPPORT_ONLY; not a blocker to that narrow claim, but blocks physical/phantom/ink conclusions |
| M10 Major | Novelty and practical downstream benefit not demonstrated | Matched upstream overlap-function comparison agrees 24/24; full end-to-end benchmark and user intervention remain proposed |
| N1 Minor | Original H11 verifier relies on assert and prints an ambiguous whole-block statement | Maintained review verifier uses explicit exceptions and precise slab-mask equality; original preserved as reference |
| N2 Minor | Coarse GLB has max-pool edge expansion and no embedded scientific provenance | Sidecar records limits; regenerated source-label figure is preferred; models remain locators only |
| N3 Minor | Source LICENSE points to absent licensing documentation; optional decoder dependencies unclear | Added licensing guide and verification extra; keep data terms separate from software MIT |
| E1 Editorial | Placeholder author/URLs, duplicate continuation headings and inconsistent source paths | Author identified as supplied; unpublished URLs stated plainly; current local paths documented |
| E2 Editorial | Personal context absent; schematics use 'verified join' despite unverified registration | Added bounded personal introduction and explicit evidence-level diagram |

