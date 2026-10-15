# Changelog

## 1.1.0 - 2026-10-15

- Recognize native FLAC, RIFF/WAVE and Ogg framing with bounded reads and conservative rejection of truncated headers.
- Keep Ogg codec identity unknown and retain read-only collision proposals.

## 1.0.0 - 2026-07-18

- Added read-only signature checks for common images, documents, archives, databases, executables, and media containers.
- Added ZIP-family inspection for Office Open XML, EPUB, and CBZ distinctions.
- Added collision-aware rename proposals plus text, JSON, and CSV reports.
- Added tests, packaging, and cross-platform CI.
