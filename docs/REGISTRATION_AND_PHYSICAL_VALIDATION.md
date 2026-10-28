# Physical registration remains unverified

Matching `shape=[19416,7948,7948]`, ZYX order and native indices is **necessary but insufficient** to prove physical index alignment. This tool intentionally makes no claim that positive predictions in absent *masked* CT Zarr storage are physically false surfaces.

Before a stronger claim:
1. Inspect both source representations' original producers, index origin, transformations, resampling, crop offsets, version, and scan reference ID. Where these are not documented, label alignment unverified.
2. Cross-check 3D landmarks or known boundaries between native unmasked CT, masked CT and prediction volume using original voxel values, not merely file existence. Work with authorized public data.
3. Examine predicted voxels near the mask boundary at several depths and compare to unmasked native CT, including spatially adjacent stored chunks and known-zero fill.
4. Test controls with independently validated papyrus surfaces and report any shifts/registrations required.
5. Do not conflate chunk-key absence, masked zero intensity, no physical material, and false papyrus; these are distinct endpoints.
6. Keep R12's 55-slice research quarantined from the storage-audit submission and preserve Gate 7F `BLOCKED`.
