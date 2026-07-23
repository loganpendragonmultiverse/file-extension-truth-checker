# File Extension Truth Checker

File Extension Truth Checker compares a filename's extension with recognizable bytes inside the file. It reports matches, mismatches, unknown signatures, safe proposed names, and destination collisions without renaming or uploading anything.

## Recognized families

- PNG, JPEG, GIF, WebP, and AVIF images
- PDF documents
- ZIP, 7-Zip, RAR, Gzip, Bzip2, and XZ archives
- DOCX, XLSX, PPTX, EPUB, and image-only CBZ containers
- SQLite databases
- Windows PE and ELF executables
- ISO base media containers such as MP4, MOV, HEIC, and HEIF, reported conservatively as one family

## Install

Python 3.10 or newer is required.

```bash
python -m venv .venv
python -m pip install -e .
```

## Three-minute use

```bash
extension-truth suspicious-download.bin
extension-truth "C:\Downloads" --recursive
extension-truth collection --format csv --output extension-review.csv --fail-on-mismatch
```

The command is read-only. Exit code 1 is available for automation when a recognized mismatch exists; unknown signatures are reported without guesses.

## Privacy and limitations

- Files stay local. Only a short header and, for ZIP-family containers, the internal directory and identifying entries are read.
- A matching extension does not prove that a file is safe, complete, authentic, or free of malicious content.
- Shared container signatures can be ambiguous. The tool uses conservative families and accepted extension aliases.
- Proposed names are review suggestions. This project deliberately performs no renames; pair reviewed results with a safe rename tool if needed.

## Development

```bash
python -m pip install -e . pytest build
python -m pytest
python -m build
```

## Project status

**Feature complete for v1.0.** New signatures should be narrow, documented, and backed by realistic fixtures.

Released under the [MIT License](LICENSE). Contributions follow the [organization guidelines](https://github.com/loganpendragonmultiverse/.github/blob/main/CONTRIBUTING.md).

## More open-source projects

This project is part of the [Logan Pendragon Forge open-source collection](https://www.loganpendragonforge.com/open-source/). Browse the catalog for other released tools, source repositories, live demos, and downloads.
