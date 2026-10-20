import json
import os
from pathlib import Path
import zipfile

import pytest

from extension_truth.checker import detect_kind, inspect_path
from extension_truth.cli import main


def zip_mimetype(path, payload):
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as stream:
        stream.writestr("mimetype", payload)


def test_oversized_epub_metadata_is_not_decompressed(tmp_path, monkeypatch):
    path = tmp_path / "large.zip"
    zip_mimetype(path, b"application/epub+zip" + b" " * (1024 * 1024))

    def forbidden(*args, **kwargs):
        raise AssertionError("oversized metadata opened")

    monkeypatch.setattr(zipfile.ZipFile, "open", forbidden)
    assert detect_kind(path).canonical_extension == ".zip"


def test_epub_does_not_use_unbounded_zip_read(tmp_path, monkeypatch):
    path = tmp_path / "book.bin"
    zip_mimetype(path, b"application/epub+zip")

    def forbidden(*args, **kwargs):
        raise AssertionError("unbounded ZipFile.read")

    monkeypatch.setattr(zipfile.ZipFile, "read", forbidden)
    assert detect_kind(path).canonical_extension == ".epub"


@pytest.mark.parametrize("change", ["encrypted", "unsupported"])
def test_unavailable_metadata_does_not_claim_epub(tmp_path, monkeypatch, change):
    path = tmp_path / "book.zip"
    zip_mimetype(path, b"application/epub+zip")
    original = zipfile.ZipFile.getinfo

    def metadata(archive, name):
        info = original(archive, name)
        if name == "mimetype":
            if change == "encrypted":
                info.flag_bits |= 1
            else:
                info.compress_type = 99
        return info

    monkeypatch.setattr(zipfile.ZipFile, "getinfo", metadata)
    assert detect_kind(path).canonical_extension == ".zip"


def test_unreadable_discovery_fails_instead_of_partial_success(tmp_path, monkeypatch):
    (tmp_path / "sub").mkdir()
    (tmp_path / "good.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    original = os.scandir

    def denied(path):
        if Path(path) == tmp_path / "sub":
            raise PermissionError("synthetic")
        return original(path)

    monkeypatch.setattr(os, "scandir", denied)
    assert main([str(tmp_path), "--recursive"]) == 2


def test_report_cannot_replace_inspected_input_or_destination(tmp_path):
    path = tmp_path / "image.bin"
    payload = b"\x89PNG\r\n\x1a\n"
    path.write_bytes(payload)
    assert main([str(path), "--output", str(path)]) == 2
    assert path.read_bytes() == payload
    output = tmp_path / "report.json"
    assert main([str(path), "--format", "json", "--output", str(output)]) == 0
    report = output.read_bytes()
    assert json.loads(report)["files"][0]["status"] == "mismatch"
    assert main([str(path), "--output", str(output)]) == 2
    assert output.read_bytes() == report


def test_dangling_links_are_collision_and_output_boundaries(tmp_path):
    source = tmp_path / "image.bin"
    source.write_bytes(b"\x89PNG\r\n\x1a\n")
    target = tmp_path / "image.png"
    missing = tmp_path / "missing"
    try:
        target.symlink_to(missing)
    except OSError:
        pytest.skip("symlinks unavailable")
    assert inspect_path(source)[0].collision
    assert main([str(source), "--output", str(target)]) == 2
    assert target.is_symlink() and not missing.exists()


def test_report_error_and_mismatch_exit_status(tmp_path, capsys):
    source = tmp_path / "image.bin"
    source.write_bytes(b"\x89PNG\r\n\x1a\n")
    assert main([str(source), "--fail-on-mismatch", "--format", "csv"]) == 1
    assert "mismatch" in capsys.readouterr().out
    assert main([str(source), "--output", str(tmp_path / "missing" / "report")]) == 2
    assert main([str(tmp_path / "absent")]) == 2


def test_corrupt_compressed_identifying_metadata_is_controlled(tmp_path):
    path = tmp_path / "book.zip"
    zip_mimetype(path, b"application/epub+zip")
    with zipfile.ZipFile(path) as archive:
        info = archive.getinfo("mimetype")
        offset = info.header_offset + 30 + len(info.filename.encode()) + len(info.extra)
    with path.open("r+b") as stream:
        stream.seek(offset)
        stream.write(b"\xff")
    finding = inspect_path(path)[0]
    assert finding.detected_type == "ZIP-like data (identifying metadata unavailable)"
    assert finding.expected_extensions == (".zip",)
    assert main([str(path), "--format", "json"]) == 0


@pytest.mark.parametrize("payload,label", [
    (b"GIF87a", "GIF image"), (b"GIF89a", "GIF image"),
    (b"%PDF-1.7", "PDF document"), (b"7z\xbc\xaf'\x1c", "7-Zip archive"),
    (b"Rar!\x1a\x07", "RAR archive"), (b"\x1f\x8b\x08", "Gzip archive"),
    (b"BZh9", "Bzip2 archive"), (b"\xfd7zXZ\x00", "XZ archive"),
    (b"SQLite format 3\x00", "SQLite database"), (b"\x7fELF", "ELF executable"),
    (b"MZ", "Windows executable"),
    (b"RIFF" + bytes(4) + b"WEBP", "WebP image"),
    (bytes(4) + b"ftypavif", "AVIF image"),
    (bytes(4) + b"ftypisom", "ISO base media"),
])
def test_documented_signature_families(tmp_path, payload, label):
    source = tmp_path / "sample.bin"
    source.write_bytes(payload)
    assert inspect_path(source)[0].detected_type == label
    assert source.read_bytes() == payload


@pytest.mark.parametrize("member,label", [("xl/workbook.xml", "Microsoft Excel workbook"), ("ppt/presentation.xml", "Microsoft PowerPoint presentation"), ("pages/001.png", "CBZ comic archive")])
def test_other_zip_subtype_families(tmp_path, member, label):
    source = tmp_path / "sample.bin"
    with zipfile.ZipFile(source, "w") as archive:
        archive.writestr(member, b"synthetic")
    assert detect_kind(source).name == label
