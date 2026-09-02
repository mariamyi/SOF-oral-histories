import os
import subprocess
import tempfile
import pytest
from transcribe import transcribe_word_timestamps


@pytest.fixture
def fixture_wav():
    with tempfile.TemporaryDirectory() as d:
        aiff_path = os.path.join(d, "fixture.aiff")
        wav_path = os.path.join(d, "fixture.wav")
        subprocess.run(
            ["say", "-o", aiff_path, "This is a test of the transcription system"],
            check=True,
        )
        subprocess.run(
            ["afconvert", "-f", "WAVE", "-d", "LEI16", aiff_path, wav_path],
            check=True,
        )
        yield wav_path


def test_returns_word_level_timestamps_in_order(fixture_wav):
    words = transcribe_word_timestamps(fixture_wav, model_size="tiny")
    assert len(words) > 0
    for w in words:
        assert "word" in w and "start" in w and "end" in w
        assert w["end"] >= w["start"]
    starts = [w["start"] for w in words]
    assert starts == sorted(starts)
    joined = " ".join(w["word"].strip().lower() for w in words)
    assert "test" in joined
    assert "transcription" in joined
