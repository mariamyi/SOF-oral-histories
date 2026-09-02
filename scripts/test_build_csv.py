import csv
import tempfile
import os
from build_csv import write_transcript_csv

def test_writes_expected_header_and_rows():
    turns = [
        {"speaker": "Clay Adkins", "words": "Hello there", "tags": "", "timestamp": "0:00:00"},
        {"speaker": "Patricia Poole", "words": "Hi Clay", "tags": "Stories of Joy", "timestamp": "0:00:03"},
    ]
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "out.csv")
        write_transcript_csv(turns, path)
        with open(path, newline="", encoding="utf-8") as f:
            rows = list(csv.reader(f))
    assert rows[0] == ["speaker", "words", "tags", "timestamp"]
    assert rows[1] == ["Clay Adkins:", "Hello there", "", "0:00:00"]
    assert rows[2] == ["Patricia Poole:", "Hi Clay", "Stories of Joy", "0:00:03"]

def test_missing_tags_key_defaults_to_empty_string():
    turns = [{"speaker": "Clay Adkins", "words": "Hello", "timestamp": "0:00:00"}]
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "out.csv")
        write_transcript_csv(turns, path)
        with open(path, newline="", encoding="utf-8") as f:
            rows = list(csv.reader(f))
    assert rows[1] == ["Clay Adkins:", "Hello", "", "0:00:00"]
