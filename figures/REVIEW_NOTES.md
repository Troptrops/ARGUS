# Figure review notes

These eight figures are source-derived measurements or explicitly labeled schematics, regenerated in the October 23 local review. They supersede the supplied Figure 06 that incorrectly called Y=176 a CT storage boundary. The revision distinguishes prediction-label slab edge Y=176 from CT-object transition Z=128. These are not original CT images, and a label locator is not a validated papyrus mesh.

The received release ZIP is preserved outside the repository in the user's private audit backup; its figure hashes are recorded in docs/FILE_AUDIT.csv. The existing source ZIP remains at its original root path, ARGUS_GITHUB_READY_0_4_2.zip. No absent historical appendix is claimed to be present here.

Source: Vesuvius Challenge PHerc0211 m7 prediction bytes and archived masked-CT HEAD receipts. Axis units are voxel indices or label counts. Data-derived imagery is excluded from the software MIT grant.

To rebuild, install numpy, blosc2 and matplotlib, then run `python tools/build_research_figures.py` from the repository root. It reads the retained historical capture; do not redistribute raw inputs without checking rights. Rebuilding intentionally overwrites figures; regenerate FILE_SHA256.txt afterward. For PDFs, additionally install reportlab, pillow and pypdf and run `python tools/build_research_pdfs.py`.
