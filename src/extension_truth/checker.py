from __future__ import annotations

import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class Kind:
    name: str
    canonical_extension: str
    accepted_extensions: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class Finding:
    path: str
    status: str
    detected_type: str | None
    current_extension: str
    expected_extensions: tuple[str, ...]
    proposed_name: str | None
    collision: bool

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


MAGIC: tuple[tuple[bytes, Kind], ...] = (
    (b"\x89PNG\r\n\x1a\n", Kind("PNG image", ".png", (".png",))),
    (b"\xff\xd8\xff", Kind("JPEG image", ".jpg", (".jpg", ".jpeg", ".jpe"))),
    (b"GIF87a", Kind("GIF image", ".gif", (".gif",))),
    (b"GIF89a", Kind("GIF image", ".gif", (".gif",))),
    (b"%PDF-", Kind("PDF document", ".pdf", (".pdf",))),
    (b"7z\xbc\xaf'\x1c", Kind("7-Zip archive", ".7z", (".7z", ".cb7"))),
    (b"Rar!\x1a\x07", Kind("RAR archive", ".rar", (".rar", ".cbr"))),
    (b"\x1f\x8b\x08", Kind("Gzip archive", ".gz", (".gz", ".gzip"))),
    (b"BZh", Kind("Bzip2 archive", ".bz2", (".bz2",))),
    (b"\xfd7zXZ\x00", Kind("XZ archive", ".xz", (".xz",))),
    (b"SQLite format 3\x00", Kind("SQLite database", ".sqlite", (".sqlite", ".sqlite3", ".db"))),
    (b"\x7fELF", Kind("ELF executable", "", ("",))),
    (b"MZ", Kind("Windows executable", ".exe", (".exe", ".dll", ".sys"))),
)


def inspect_path(target: Path, recursive: bool = False) -> tuple[Finding, ...]:
    source = target.expanduser().resolve()
    if source.is_file():
        files = [source]
        root = source.parent
    elif source.is_dir():
        candidates = source.rglob("*") if recursive else source.iterdir()
        files = sorted((path for path in candidates if path.is_file() and not path.is_symlink()), key=lambda path: str(path.relative_to(source)).casefold())
        root = source
    else:
        raise ValueError(f"Not a file or directory: {source}")
    return tuple(_inspect(file, root) for file in files)


def detect_kind(path: Path) -> Kind | None:
    with path.open("rb") as handle:
        header = handle.read(64)
    if header.startswith((b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08")):
        return _detect_zip(path)
    if header.startswith(b"RIFF") and header[8:12] == b"WEBP":
        return Kind("WebP image", ".webp", (".webp",))
    if len(header) >= 12 and header[4:8] == b"ftyp":
        brand = header[8:12]
        if brand in {b"avif", b"avis"}:
            return Kind("AVIF image", ".avif", (".avif",))
        return Kind("ISO base media", ".mp4", (".mp4", ".m4v", ".mov", ".heic", ".heif"))
    for signature, kind in MAGIC:
        if header.startswith(signature):
            return kind
    return None


def _detect_zip(path: Path) -> Kind:
    try:
        with zipfile.ZipFile(path) as archive:
            names = {name.casefold() for name in archive.namelist()}
            if "word/document.xml" in names:
                return Kind("Microsoft Word document", ".docx", (".docx",))
            if "xl/workbook.xml" in names:
                return Kind("Microsoft Excel workbook", ".xlsx", (".xlsx",))
            if "ppt/presentation.xml" in names:
                return Kind("Microsoft PowerPoint presentation", ".pptx", (".pptx",))
            try:
                if archive.read("mimetype").strip() == b"application/epub+zip":
                    return Kind("EPUB ebook", ".epub", (".epub",))
            except KeyError:
                pass
            image_extensions = {".avif", ".bmp", ".gif", ".jpeg", ".jpg", ".png", ".tif", ".tiff", ".webp"}
            file_names = [name for name in names if not name.endswith("/")]
            if file_names and any(Path(name).suffix in image_extensions for name in file_names):
                allowed = image_extensions | {".xml"}
                if all(Path(name).suffix in allowed or Path(name).name in {".ds_store"} for name in file_names):
                    return Kind("CBZ comic archive", ".cbz", (".cbz", ".zip"))
    except zipfile.BadZipFile:
        return Kind("ZIP-like data with a damaged directory", ".zip", (".zip",))
    return Kind("ZIP archive", ".zip", (".zip",))


def _inspect(path: Path, root: Path) -> Finding:
    kind = detect_kind(path)
    current = path.suffix.casefold()
    relative = path.relative_to(root).as_posix()
    if kind is None:
        return Finding(relative, "unknown", None, current, (), None, False)
    if current in kind.accepted_extensions:
        return Finding(relative, "match", kind.name, current, kind.accepted_extensions, None, False)
    proposed = path.with_suffix(kind.canonical_extension).name if kind.canonical_extension else None
    collision = bool(proposed and path.with_name(proposed).exists())
    return Finding(relative, "mismatch", kind.name, current, kind.accepted_extensions, proposed, collision)
