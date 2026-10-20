# File Extension Truth Checker

File Extension Truth Checker compares a filename's extension with recognizable bytes inside the file. It reports matches, mismatches, unknown signatures, safe proposed names, and destination collisions without renaming or uploading anything.

## Recognized families

- PNG, JPEG, GIF, WebP, and AVIF images
- Native FLAC audio, RIFF/WAVE audio (`.wav`, `.wave`), and Ogg containers
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

**Version 1.1** adds bounded audio framing checks. New signatures should be narrow, documented, and backed by realistic fixtures.

Released under the [MIT License](LICENSE). Contributions follow the [organization guidelines](https://github.com/loganpendragonmultiverse/.github/blob/main/CONTRIBUTING.md).

## More open-source projects

This project is part of the [Logan Pendragon Forge open-source collection](https://www.loganpendragonforge.com/open-source/). Browse the catalog for other released tools, source repositories, live demos, and downloads.

## Audio identification limits

At most 4 KiB of header data is read. FLAC requires the initial 34-byte STREAMINFO block and plausible block/sample fields. WAVE requires a bounded RIFF envelope with a format chunk and data chunk header within that window; large leading metadata may remain unknown. Ogg requires version-zero page framing and a complete segment table with payload lengths fitting the file. Ogg codec identity is always unknown, including for `.opus`, `.spx`, `.oga`, `.ogv`, and `.ogx` aliases. Checksums, audio frames, subsequent pages and full-file integrity are not validated.

Framing references: [FLAC RFC 9639](https://www.rfc-editor.org/rfc/rfc9639.html), [Ogg RFC 3533](https://www.rfc-editor.org/rfc/rfc3533.html), and [Microsoft RIFF](https://learn.microsoft.com/en-us/windows/win32/xaudio2/resource-interchange-file-format--riff-).

## Report and scan safety

Report destinations must be new. Existing files, including the inspected input
itself and dangling symbolic links, are preserved with exit status 2. Recursive
scans skip descendant symlinks; unreadable directory discovery stops with status 2
rather than returning a partial success. Proposed names also flag dangling-link
collisions. ZIP identification reads at most 257 bytes from a mimetype entry and
uses the EPUB value only when its declared size is at most 256 bytes and it is
unencrypted and uses Stored or Deflate compression. Other compression methods,
invalid streams and unavailable identifying metadata retain a generic ZIP-family
label. Unreadable or unsupported identifying metadata never justifies a
more specific file-type claim. ZIP directory metadata is still parsed in memory;
this is a format hint, not hostile-archive or malware certification.

See [TESTING.md](TESTING.md) for source and installed-artifact checks.
