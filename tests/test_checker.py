import zipfile
from pathlib import Path

from extension_truth.checker import detect_kind, inspect_path


def test_png_with_wrong_extension_is_reported(tmp_path: Path) -> None:
    source = tmp_path / "cover.txt"
    source.write_bytes(b"\x89PNG\r\n\x1a\n" + b"data")
    finding = inspect_path(source)[0]
    assert finding.status == "mismatch"
    assert finding.proposed_name == "cover.png"


def test_matching_jpeg_alias_passes(tmp_path: Path) -> None:
    source = tmp_path / "photo.jpeg"
    source.write_bytes(b"\xff\xd8\xff" + b"data")
    assert inspect_path(source)[0].status == "match"


def test_docx_is_distinguished_from_zip(tmp_path: Path) -> None:
    source = tmp_path / "draft.zip"
    with zipfile.ZipFile(source, "w") as archive:
        archive.writestr("word/document.xml", "<document/>")
    kind = detect_kind(source)
    assert kind is not None
    assert kind.canonical_extension == ".docx"


def test_epub_is_distinguished_from_zip(tmp_path: Path) -> None:
    source = tmp_path / "book.bin"
    with zipfile.ZipFile(source, "w") as archive:
        archive.writestr("mimetype", "application/epub+zip")
    assert inspect_path(source)[0].proposed_name == "book.epub"


def test_proposed_name_collision_is_flagged(tmp_path: Path) -> None:
    source = tmp_path / "cover.txt"
    source.write_bytes(b"\x89PNG\r\n\x1a\n" + b"data")
    (tmp_path / "cover.png").write_bytes(b"existing")
    assert inspect_path(source)[0].collision


def test_unknown_signature_is_not_guessed(tmp_path: Path) -> None:
    source = tmp_path / "notes.txt"
    source.write_text("ordinary text", encoding="utf-8")
    finding = inspect_path(source)[0]
    assert finding.status == "unknown"
    assert finding.proposed_name is None
