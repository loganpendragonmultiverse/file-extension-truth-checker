import io
import wave
from pathlib import Path

import pytest

from extension_truth.checker import detect_kind, inspect_path


def flac():
    info = (44100 << 44) | (1 << 41) | (15 << 36)
    return b"fLaC\x80\x00\x00\x22" + b"\x10\x00\x10\x00" + bytes(6) + info.to_bytes(8, "big") + bytes(16)


def wav():
    stream = io.BytesIO()
    with wave.open(stream, "wb") as audio:
        audio.setparams((1, 2, 8000, 0, "NONE", "not compressed"))
        audio.writeframes(b"\x00\x00" * 16)
    return stream.getvalue()


def ogg():
    # A complete first-page framing with a codec identification packet; no codec inference.
    payload = b"OpusHead" + bytes(12)
    return b"OggS\x00\x02" + bytes(20) + b"\x01" + bytes([len(payload)]) + payload


@pytest.mark.parametrize("payload,extension,label", [
    (flac(), ".flac", "FLAC audio"), (wav(), ".wav", "RIFF/WAVE audio"),
    (wav(), ".wave", "RIFF/WAVE audio"),
    *[(ogg(), ext, "Ogg container (codec unknown)") for ext in (".ogg", ".oga", ".ogv", ".ogx", ".opus", ".spx")],
])
def test_audio_aliases_are_read_only(tmp_path, payload, extension, label):
    source = tmp_path / ("audio" + extension.upper())
    source.write_bytes(payload)
    finding = inspect_path(source)[0]
    assert finding.status == "match" and finding.detected_type == label
    assert source.read_bytes() == payload


@pytest.mark.parametrize("payload", [flac(), wav(), ogg()])
def test_audio_truncations_and_collisions(tmp_path: Path, payload):
    source = tmp_path / "audio.bin"
    for cut in range(min(42, len(payload))):
        source.write_bytes(payload[:cut])
        assert detect_kind(source) is None
    source.write_bytes(payload)
    proposed = inspect_path(source)[0].proposed_name
    (tmp_path / proposed).write_bytes(b"keep")
    finding = inspect_path(source)[0]
    assert finding.status == "mismatch" and finding.collision
    assert source.read_bytes() == payload
    assert (tmp_path / proposed).read_bytes() == b"keep"


@pytest.mark.parametrize("payload", [
    b"fLaC" + bytes(38), flac()[:4] + b"\x81" + flac()[5:],
    ogg()[:4] + b"\x01" + ogg()[5:], ogg()[:5] + b"\x80" + ogg()[6:],
    ogg()[:27] + b"\xff" + ogg()[28:],
    b"RIFF\x04\x00\x00\x00WAVE", wav()[:4] + b"\xff" * 4 + wav()[8:],
    wav()[:16] + b"\xff" * 4 + wav()[20:],
    wav()[:20] + bytes(16) + wav()[36:],
    b"RIFF" + bytes(4) + b"AVI ",
])
def test_contradictory_headers_stay_unknown(tmp_path, payload):
    path = tmp_path / "audio.ogg"
    path.write_bytes(payload)
    assert inspect_path(path)[0].status == "unknown"
