# Executed release validation

Local platform: Windows, Python 3.12.14, isolated virtual environment. Installed wheel: argus-surface-support 0.4.3; NumPy 2.5.4, Blosc2 4.14.1. No global packages were changed. Commands below actually executed successfully on 28 October 2026 unless marked separately.

| Command | Actual local result |
|---|---|
| `python -m pip install ".[verification]"` | Built and installed wheel plus declared verification dependencies |
| `python -m unittest discover -s tests -v` | 16 tests passed, zero failures/errors |
| `python tools/heldout_capture.py --dry-run` | Exit 0; all 24 frozen selections verified; no HTTP |
| `python -m argus_support --help` | Exit 0 |
| `argus-surface-support --help` | Installed console entry point checked from outside checkout |
| `python tools/heldout_verify.py CAPTURE --out OUTPUT` | Exit 0, COMPLETE, exact central counts |
| `python tools/verify_heldout_vectorized.py CAPTURE --out OUTPUT` | Exit 0, independently agrees |
| `python -O tools/review_release.py CAPTURE --out OUTPUT` | Exit 0, explicit checks remain enabled; exact counts and H11 block equality |
| `python tools/check_release.py` | Manifest/version/root and docs relative links checked before publication |

CAPTURE means ARGUS_04_HELDOUT_CAPTURE.zip; OUTPUT is a new local output directory. The actual three replay results agree on 13 stored / 11 absent predictions, 19,932,389 positives, 8,519,612 nominally in absent CT storage, 11,412,777 in stored regions. H11 has 279,426 positives; its absent-storage mask exactly equals the 196,608-voxel block, while the entire positive mask does not.

CI is configured for ubuntu-latest/windows-latest and Python 3.11/3.13. Configuration is not proof of a successful run: see the exact commit's GitHub Actions checks and the final publication report for executed remote results. Python 3.10 is declared but not independently platform-tested here. No live large-data capture, full-library/tifxyz certification, physical registration or external researcher replication was performed. Synthetic offline tests are distinct from source-byte replays and live network capture.

The PDF was rendered and visually reviewed; ordinary relative links and source images are checked separately. Historical original documentation may contain obsolete paths; its archival status is explicit.

Windows launchers were executed with ARGUS_PYTHON set to the isolated interpreter and ARGUS_NO_PAUSE=1 and ARGUS_CAPTURE pointing to the existing historical ZIP: RUN_HELDOUT_24.cmd returned 1 when a capture already existed and preserved its SHA256; RUN_VERIFY_CAPTURE.cmd returned 0 and reproduced the archived totals. Only newly generated diagnostics were removed after checking; the original root capture is unchanged. No live capture was triggered.
