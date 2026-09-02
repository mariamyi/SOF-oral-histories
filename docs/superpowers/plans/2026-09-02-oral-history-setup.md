# Souls on Fire Oral History Setup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Get two real oral history interviews (Patricia Poole; Randy & Natasha Grubb) fully working in the CollectionBuilder-OH site at `/Users/mariamyi/Downloads/SOF-oral-histories`, with accurate timestamps (via forced alignment) and theme tags, rendering the color-coded thematic bar synced to audio playback.

**Architecture:** A small Python pipeline (in `scripts/`) parses each Word-doc transcript into speaker turns, runs Whisper on the corresponding mp3 to get word-level timestamps, aligns the two via sequence matching to attach accurate timing to the human-edited transcript text, and writes the result into CollectionBuilder-OH's required CSV format. Theme tags are added as a manual/editorial pass. The pipeline logic (parsing, alignment, CSV writing) is unit-tested; the Whisper wrapper gets an integration test using a synthesized macOS `say` audio fixture so the test suite doesn't depend on the real (large, slow) interview recordings.

**Tech Stack:** Python 3.9 (venv), `openai-whisper`, `pytest`, Ruby/Jekyll (site build, already present via system Ruby + Bundler), macOS `textutil` (docx→text), macOS `say`/`afconvert` (test audio fixture).

---

## Reference data (established during design)

**Source files** (already staged, outside git):
- `/Users/mariamyi/Downloads/SOF-oral-histories-source/transcripts/Patricia Poole Transcipt .docx`
- `/Users/mariamyi/Downloads/SOF-oral-histories-source/transcripts/Randy & Natasha Grubb Transcript.docx`
- `/Users/mariamyi/Downloads/SOF-oral-histories-source/audio/Patricia Poole Interview.mp3` (23:52, ~33MB)
- `/Users/mariamyi/Downloads/SOF-oral-histories-source/audio/Randy & Natasha Grubb Interview.mp3` (19:30, ~27MB)

**Speaker alias maps** (confirmed by scanning every label variant in each doc):
- Patricia Poole interview: `{"C": "Clay Adkins", "P": "Patricia Poole"}`
- Grubb interview: `{"C": "Clay Adkins", "Clay Adkins": "Clay Adkins", "R": "Randy Grubb", "Randy": "Randy Grubb", "N": "Natasha Grubb"}`

**objectids:** `patricia-poole`, `randy-natasha-grubb`

**Theme taxonomy** (confirmed with user): Stories of Joy, Stories of Faith, Stories of Struggle, Community & Family, Education & Integration, Gospel Music, Activism & Change.

**Open item — flag to user, do not fabricate:** the main metadata CSV has `rights` / `rightsstatement` columns. Leave these blank in this plan; the Calfee Center's actual release-form language needs to go there before any public deployment. This is called out again in Task 15.

---

### Task 1: Python environment setup

**Files:**
- Create: `scripts/requirements.txt`
- Modify: `.gitignore`

- [ ] **Step 1: Check for ffmpeg (required by Whisper to decode audio) and install if missing**

Run: `which ffmpeg || brew install ffmpeg`
Expected: prints a path to the ffmpeg binary (either it was already there, or brew installs it).

- [ ] **Step 2: Create the requirements file**

```
openai-whisper
pytest
```

Save as `scripts/requirements.txt`.

- [ ] **Step 3: Create a virtual environment and install dependencies**

Run:
```bash
cd "/Users/mariamyi/Downloads/SOF-oral-histories"
python3 -m venv scripts/.venv
scripts/.venv/bin/pip install --upgrade pip
scripts/.venv/bin/pip install -r scripts/requirements.txt
```
Expected: completes without error (this downloads PyTorch as a dependency of `openai-whisper`, so it can take a few minutes).

- [ ] **Step 4: Verify the install**

Run: `scripts/.venv/bin/python -c "import whisper, pytest; print('ok')"`
Expected: `ok`

- [ ] **Step 5: Ignore the venv and future cache/output dirs in git**

Add to `.gitignore`:
```

# Python pipeline scripts (data prep, not part of the built site)
scripts/.venv/
scripts/__pycache__/
scripts/whisper_cache/
```

- [ ] **Step 6: Commit**

```bash
git add scripts/requirements.txt .gitignore
git commit -m "Set up Python environment for transcript alignment pipeline"
```

---

### Task 2: Transcript turn parser

**Files:**
- Create: `scripts/parse_transcript.py`
- Test: `scripts/test_parse_transcript.py`

- [ ] **Step 1: Write the failing tests**

```python
# scripts/test_parse_transcript.py
from parse_transcript import parse_speaker_turns

ALIASES = {"C": "Clay Adkins", "P": "Patricia Poole"}

def test_parses_simple_alternating_turns():
    text = "C: Hello there\nP: Hi Clay\n"
    turns = parse_speaker_turns(text, ALIASES)
    assert turns == [
        {"speaker": "Clay Adkins", "words": "Hello there"},
        {"speaker": "Patricia Poole", "words": "Hi Clay"},
    ]

def test_skips_header_lines_before_first_known_speaker():
    text = (
        "Narrator: Patricia Poole\n"
        "Interviewer: Clay Adkins\n"
        "Legend: C = Clay Adkins, P = Patricia Poole\n"
        "C: Alright my name is Clay\n"
    )
    turns = parse_speaker_turns(text, ALIASES)
    assert turns == [{"speaker": "Clay Adkins", "words": "Alright my name is Clay"}]

def test_continuation_lines_merge_into_previous_turn():
    text = (
        "C: First part of a long question\n"
        "still part of the same question because no label starts this line\n"
        "P: A short answer\n"
    )
    turns = parse_speaker_turns(text, ALIASES)
    assert turns == [
        {
            "speaker": "Clay Adkins",
            "words": "First part of a long question still part of the same question because no label starts this line",
        },
        {"speaker": "Patricia Poole", "words": "A short answer"},
    ]

def test_multiple_alias_variants_map_to_same_canonical_speaker():
    aliases = {"C": "Clay Adkins", "Clay Adkins": "Clay Adkins", "R": "Randy Grubb", "Randy": "Randy Grubb", "N": "Natasha Grubb"}
    text = "Clay Adkins: Question one\nR: Answer one\nRandy: More from Randy\nN: Natasha jumps in\n"
    turns = parse_speaker_turns(text, aliases)
    assert turns == [
        {"speaker": "Clay Adkins", "words": "Question one"},
        {"speaker": "Randy Grubb", "words": "Answer one"},
        {"speaker": "Randy Grubb", "words": "More from Randy"},
        {"speaker": "Natasha Grubb", "words": "Natasha jumps in"},
    ]

def test_blank_lines_are_ignored():
    text = "C: Hello\n\n\nP: Hi\n"
    turns = parse_speaker_turns(text, ALIASES)
    assert turns == [
        {"speaker": "Clay Adkins", "words": "Hello"},
        {"speaker": "Patricia Poole", "words": "Hi"},
    ]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd scripts && ../scripts/.venv/bin/python -m pytest test_parse_transcript.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'parse_transcript'`

- [ ] **Step 3: Write the implementation**

```python
# scripts/parse_transcript.py
import re

LABEL_PATTERN = re.compile(r'^([A-Za-z][A-Za-z .]{0,30}):\s*(.*)$')


def parse_speaker_turns(text, speaker_aliases):
    """Parse a textutil-converted oral history transcript into speaker turns.

    text: full transcript text, one paragraph per line (as produced by
        `textutil -convert txt` from the source .docx).
    speaker_aliases: dict mapping every label variant that appears in the
        document (e.g. "C", "Clay Adkins") to a single canonical display
        name (e.g. "Clay Adkins"). Header lines (Narrator:, Interviewer:,
        Legend:, etc.) are skipped because their labels won't be in this
        dict.

    Returns: list of {"speaker": str, "words": str}, one entry per turn.
    Lines that don't start with a recognized speaker label are treated as
    a continuation of the previous turn's paragraph (mid-sentence line
    wraps) and are appended to it.
    """
    turns = []
    started = False
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        match = LABEL_PATTERN.match(line)
        if match and match.group(1) in speaker_aliases:
            started = True
            speaker = speaker_aliases[match.group(1)]
            words = match.group(2).strip()
            turns.append({"speaker": speaker, "words": words})
        elif started:
            turns[-1]["words"] = (turns[-1]["words"] + " " + line).strip()
    return turns
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd scripts && ../scripts/.venv/bin/python -m pytest test_parse_transcript.py -v`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add scripts/parse_transcript.py scripts/test_parse_transcript.py
git commit -m "Add transcript turn parser with tests"
```

---

### Task 3: Timestamp formatter

**Files:**
- Create: `scripts/format_timestamp.py`
- Test: `scripts/test_format_timestamp.py`

- [ ] **Step 1: Write the failing tests**

```python
# scripts/test_format_timestamp.py
from format_timestamp import format_timestamp

def test_zero_seconds():
    assert format_timestamp(0) == "0:00:00"

def test_seconds_and_minutes():
    assert format_timestamp(75) == "0:01:15"

def test_rounds_to_nearest_second():
    assert format_timestamp(75.6) == "0:01:16"

def test_over_an_hour():
    assert format_timestamp(3661) == "1:01:01"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd scripts && ../scripts/.venv/bin/python -m pytest test_format_timestamp.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'format_timestamp'`

- [ ] **Step 3: Write the implementation**

```python
# scripts/format_timestamp.py

def format_timestamp(seconds):
    """Format a number of seconds as CB-OH's expected h:mm:ss timestamp string."""
    total = int(round(seconds))
    h = total // 3600
    m = (total % 3600) // 60
    s = total % 60
    return f"{h}:{m:02d}:{s:02d}"
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd scripts && ../scripts/.venv/bin/python -m pytest test_format_timestamp.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add scripts/format_timestamp.py scripts/test_format_timestamp.py
git commit -m "Add timestamp formatter with tests"
```

---

### Task 4: Word-alignment logic

**Files:**
- Create: `scripts/align_timestamps.py`
- Test: `scripts/test_align_timestamps.py`

- [ ] **Step 1: Write the failing tests**

```python
# scripts/test_align_timestamps.py
from align_timestamps import align_turns_to_words, normalize_word

def test_normalize_word_strips_punctuation_and_case():
    assert normalize_word("Hello,") == "hello"
    assert normalize_word("DON'T") == "don't"
    assert normalize_word("--word--") == "word"

def test_aligns_exact_match_words():
    turns = [
        {"speaker": "A", "words": "hello world"},
        {"speaker": "B", "words": "nice to meet you"},
    ]
    whisper_words = [
        {"word": "hello", "start": 0.0, "end": 0.4},
        {"word": "world", "start": 0.4, "end": 0.9},
        {"word": "nice", "start": 1.2, "end": 1.5},
        {"word": "to", "start": 1.5, "end": 1.6},
        {"word": "meet", "start": 1.6, "end": 1.9},
        {"word": "you", "start": 1.9, "end": 2.1},
    ]
    result = align_turns_to_words(turns, whisper_words)
    assert result[0]["timestamp"] == 0.0
    assert result[1]["timestamp"] == 1.2

def test_falls_back_to_next_matched_word_when_first_word_unmatched():
    # Whisper mis-hears "Hmmm" as an interjection with no equivalent token,
    # so the turn's first normalized word ("hmmm") never appears in whisper_words.
    turns = [
        {"speaker": "A", "words": "hmmm well the answer is yes"},
    ]
    whisper_words = [
        {"word": "well", "start": 5.0, "end": 5.3},
        {"word": "the", "start": 5.3, "end": 5.4},
        {"word": "answer", "start": 5.4, "end": 5.8},
        {"word": "is", "start": 5.8, "end": 5.9},
        {"word": "yes", "start": 5.9, "end": 6.2},
    ]
    result = align_turns_to_words(turns, whisper_words)
    assert result[0]["timestamp"] == 5.0

def test_falls_back_to_last_known_time_when_turn_has_no_matches_at_all():
    turns = [
        {"speaker": "A", "words": "hello world"},
        {"speaker": "B", "words": "completely unmatched gibberish"},
    ]
    whisper_words = [
        {"word": "hello", "start": 10.0, "end": 10.4},
        {"word": "world", "start": 10.4, "end": 10.9},
    ]
    result = align_turns_to_words(turns, whisper_words)
    assert result[0]["timestamp"] == 10.0
    assert result[1]["timestamp"] == 10.0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd scripts && ../scripts/.venv/bin/python -m pytest test_align_timestamps.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'align_timestamps'`

- [ ] **Step 3: Write the implementation**

```python
# scripts/align_timestamps.py
import difflib
import re

_PUNCT = re.compile(r"[^a-z0-9']")


def normalize_word(word):
    return _PUNCT.sub("", word.lower())


def align_turns_to_words(turns, whisper_words):
    """Attach a 'timestamp' (float seconds) to each turn by aligning the
    turn's own words against Whisper's word-level ASR timestamps.

    turns: list of {"speaker": str, "words": str}, in transcript order.
        Mutated in place (a "timestamp" key is added to each dict) and
        also returned for convenience.
    whisper_words: list of {"word": str, "start": float, "end": float},
        in audio order, as produced by transcribe.transcribe_word_timestamps.

    For each turn, the timestamp is the start time of its first token that
    has a matching Whisper word (found via difflib sequence alignment on
    normalized tokens). If a turn has no matching word at all (e.g. very
    short interjections the ASR mis-heard), it inherits the timestamp of
    the previous turn.
    """
    our_tokens = []
    turn_start_index = []
    for turn in turns:
        turn_start_index.append(len(our_tokens))
        for w in turn["words"].split():
            nw = normalize_word(w)
            if nw:
                our_tokens.append(nw)

    whisper_tokens = [normalize_word(w["word"]) for w in whisper_words]

    matcher = difflib.SequenceMatcher(None, our_tokens, whisper_tokens, autojunk=False)
    our_to_time = {}
    for block in matcher.get_matching_blocks():
        for offset in range(block.size):
            our_idx = block.a + offset
            whisper_idx = block.b + offset
            our_to_time[our_idx] = whisper_words[whisper_idx]["start"]

    last_time = 0.0
    for i, turn in enumerate(turns):
        start_idx = turn_start_index[i]
        end_idx = turn_start_index[i + 1] if i + 1 < len(turns) else len(our_tokens)
        found = None
        for idx in range(start_idx, end_idx):
            if idx in our_to_time:
                found = our_to_time[idx]
                break
        if found is None:
            found = last_time
        turn["timestamp"] = found
        last_time = found
    return turns
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd scripts && ../scripts/.venv/bin/python -m pytest test_align_timestamps.py -v`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add scripts/align_timestamps.py scripts/test_align_timestamps.py
git commit -m "Add Whisper-to-transcript word alignment logic with tests"
```

---

### Task 5: CSV writer

**Files:**
- Create: `scripts/build_csv.py`
- Test: `scripts/test_build_csv.py`

- [ ] **Step 1: Write the failing test**

```python
# scripts/test_build_csv.py
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd scripts && ../scripts/.venv/bin/python -m pytest test_build_csv.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'build_csv'`

- [ ] **Step 3: Write the implementation**

```python
# scripts/build_csv.py
import csv


def write_transcript_csv(turns, output_path):
    """Write turns to a CB-OH-format transcript CSV: speaker,words,tags,timestamp.

    turns: list of {"speaker": str, "words": str, "timestamp": str, "tags": str (optional)}
    """
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["speaker", "words", "tags", "timestamp"])
        for turn in turns:
            writer.writerow([
                f"{turn['speaker']}:",
                turn["words"],
                turn.get("tags", ""),
                turn["timestamp"],
            ])
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd scripts && ../scripts/.venv/bin/python -m pytest test_build_csv.py -v`
Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add scripts/build_csv.py scripts/test_build_csv.py
git commit -m "Add CB-OH transcript CSV writer with tests"
```

---

### Task 6: Whisper transcription wrapper

**Files:**
- Create: `scripts/transcribe.py`
- Test: `scripts/test_transcribe.py`

- [ ] **Step 1: Write the failing integration test**

This test synthesizes a short speech clip with macOS's built-in `say`, converts it to a wav Whisper can read, and checks that the wrapper returns word-level timestamps covering roughly the right words in increasing time order. Using a synthesized fixture keeps the test fast and independent of the real (large) interview recordings.

```python
# scripts/test_transcribe.py
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd scripts && ../scripts/.venv/bin/python -m pytest test_transcribe.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'transcribe'`

- [ ] **Step 3: Write the implementation**

```python
# scripts/transcribe.py
import whisper


def transcribe_word_timestamps(audio_path, model_size="small"):
    """Run Whisper on audio_path and return word-level timestamps.

    Returns: list of {"word": str, "start": float, "end": float}, in
    audio order. Uses "small" by default as a speed/accuracy tradeoff for
    ~20 minute interview recordings on CPU; tests pass model_size="tiny"
    for speed.
    """
    model = whisper.load_model(model_size)
    result = model.transcribe(audio_path, word_timestamps=True)
    words = []
    for segment in result["segments"]:
        for w in segment.get("words", []):
            words.append({"word": w["word"], "start": w["start"], "end": w["end"]})
    return words
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd scripts && ../scripts/.venv/bin/python -m pytest test_transcribe.py -v`
Expected: 1 passed (downloads the "tiny" Whisper model on first run, ~75MB)

- [ ] **Step 5: Run the full test suite together**

Run: `cd scripts && ../scripts/.venv/bin/python -m pytest -v`
Expected: 17 passed

- [ ] **Step 6: Commit**

```bash
git add scripts/transcribe.py scripts/test_transcribe.py
git commit -m "Add Whisper word-timestamp wrapper with synthesized-audio integration test"
```

---

### Task 7: Driver script tying the pipeline together

**Files:**
- Create: `scripts/build_interview.py`

- [ ] **Step 1: Write the driver script**

This is orchestration glue (no new logic to unit test — it composes the already-tested pieces from Tasks 2-6). It caches Whisper's raw output to JSON so re-runs (e.g. after fixing a typo in the docx) don't require re-transcribing.

```python
# scripts/build_interview.py
"""
Usage:
    .venv/bin/python build_interview.py \
        --docx "/path/to/transcript.docx" \
        --audio "/path/to/interview.mp3" \
        --aliases '{"C": "Clay Adkins", "P": "Patricia Poole"}' \
        --out "_data/transcripts/patricia-poole.csv" \
        --cache "scripts/whisper_cache/patricia-poole.json"

Produces a CB-OH transcript CSV with an aligned "timestamp" per turn and an
empty "tags" column, ready for the manual theme-tagging pass (Task 9).
"""
import argparse
import json
import os
import subprocess
import sys

from parse_transcript import parse_speaker_turns
from transcribe import transcribe_word_timestamps
from align_timestamps import align_turns_to_words
from format_timestamp import format_timestamp
from build_csv import write_transcript_csv


def docx_to_text(docx_path):
    result = subprocess.run(
        ["textutil", "-convert", "txt", docx_path, "-stdout"],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def get_whisper_words(audio_path, cache_path, model_size="small"):
    if cache_path and os.path.exists(cache_path):
        with open(cache_path, encoding="utf-8") as f:
            return json.load(f)
    words = transcribe_word_timestamps(audio_path, model_size=model_size)
    if cache_path:
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(words, f)
    return words


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--docx", required=True)
    parser.add_argument("--audio", required=True)
    parser.add_argument("--aliases", required=True, help="JSON dict of label -> canonical speaker name")
    parser.add_argument("--out", required=True, help="Output CSV path")
    parser.add_argument("--cache", default=None, help="Path to cache raw Whisper word timestamps as JSON")
    parser.add_argument("--model-size", default="small")
    args = parser.parse_args()

    aliases = json.loads(args.aliases)
    text = docx_to_text(args.docx)
    turns = parse_speaker_turns(text, aliases)
    if not turns:
        print("No turns parsed - check the alias map against the transcript's labels.", file=sys.stderr)
        sys.exit(1)

    whisper_words = get_whisper_words(args.audio, args.cache, model_size=args.model_size)
    turns = align_turns_to_words(turns, whisper_words)
    for turn in turns:
        turn["timestamp"] = format_timestamp(turn["timestamp"])
        turn["tags"] = ""

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    write_transcript_csv(turns, args.out)
    print(f"Wrote {len(turns)} turns to {args.out}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Commit**

```bash
git add scripts/build_interview.py
git commit -m "Add driver script to run the transcript alignment pipeline end to end"
```

---

### Task 8: Generate the aligned CSV for the Patricia Poole interview

**Files:**
- Create: `_data/transcripts/patricia-poole.csv` (generated, not hand-written)
- Create: `scripts/whisper_cache/patricia-poole.json` (generated cache, gitignored)

- [ ] **Step 1: Run the driver script**

```bash
cd "/Users/mariamyi/Downloads/SOF-oral-histories"
scripts/.venv/bin/python scripts/build_interview.py \
  --docx "/Users/mariamyi/Downloads/SOF-oral-histories-source/transcripts/Patricia Poole Transcipt .docx" \
  --audio "/Users/mariamyi/Downloads/SOF-oral-histories-source/audio/Patricia Poole Interview.mp3" \
  --aliases '{"C": "Clay Adkins", "P": "Patricia Poole"}' \
  --out "_data/transcripts/patricia-poole.csv" \
  --cache "scripts/whisper_cache/patricia-poole.json"
```
Expected: `Wrote N turns to _data/transcripts/patricia-poole.csv` (N should be roughly the number of C:/P: lines in the source doc). This step transcribes ~24 minutes of audio with the "small" Whisper model, which can take several minutes on CPU.

- [ ] **Step 2: Spot-check alignment quality**

Open `_data/transcripts/patricia-poole.csv` and pick 3 timestamps from different points in the interview (start, middle, end). For each, play the audio at that offset and confirm the transcript text at that row is actually being spoken around that time:

```bash
afplay "/Users/mariamyi/Downloads/SOF-oral-histories-source/audio/Patricia Poole Interview.mp3" -t 5 -T <timestamp-in-seconds>
```
Expected: the words spoken in that 5-second clip roughly match the row's `words` column. A few seconds of drift is fine; if a timestamp is wildly wrong (e.g. off by minutes), note it — it likely means that turn had very few words that Whisper could match (short turns like "OK" or "Yeah" are the most error-prone) and may need a manual timestamp correction later.

- [ ] **Step 3: Commit**

```bash
git add _data/transcripts/patricia-poole.csv
git commit -m "Generate aligned transcript CSV for Patricia Poole interview"
```

---

### Task 9: Generate the aligned CSV for the Grubb interview

**Files:**
- Create: `_data/transcripts/randy-natasha-grubb.csv` (generated)
- Create: `scripts/whisper_cache/randy-natasha-grubb.json` (generated cache, gitignored)

- [ ] **Step 1: Run the driver script**

```bash
cd "/Users/mariamyi/Downloads/SOF-oral-histories"
scripts/.venv/bin/python scripts/build_interview.py \
  --docx "/Users/mariamyi/Downloads/SOF-oral-histories-source/transcripts/Randy & Natasha Grubb Transcript.docx" \
  --audio "/Users/mariamyi/Downloads/SOF-oral-histories-source/audio/Randy & Natasha Grubb Interview.mp3" \
  --aliases '{"C": "Clay Adkins", "Clay Adkins": "Clay Adkins", "R": "Randy Grubb", "Randy": "Randy Grubb", "N": "Natasha Grubb"}' \
  --out "_data/transcripts/randy-natasha-grubb.csv" \
  --cache "scripts/whisper_cache/randy-natasha-grubb.json"
```
Expected: `Wrote N turns to _data/transcripts/randy-natasha-grubb.csv`

- [ ] **Step 2: Spot-check alignment quality**

Same approach as Task 8, Step 2, against `/Users/mariamyi/Downloads/SOF-oral-histories-source/audio/Randy & Natasha Grubb Interview.mp3`.

- [ ] **Step 3: Commit**

```bash
git add _data/transcripts/randy-natasha-grubb.csv
git commit -m "Generate aligned transcript CSV for Randy & Natasha Grubb interview"
```

---

### Task 10: Define the theme taxonomy (`filters.csv`)

**Files:**
- Modify: `_data/filters.csv`

- [ ] **Step 1: Replace the demo taxonomy with the Souls on Fire taxonomy**

Replace the contents of `_data/filters.csv` with:

```csv
tag,description
joy,Stories of Joy
faith,Stories of Faith
struggle,Stories of Struggle
community-family,Community & Family
education-integration,Education & Integration
gospel-music,Gospel Music
activism-change,Activism & Change
```

(Slugged `tag` values are used as CSS classes by the template, so they must be single tokens; `description` is the human-readable label shown in the UI.)

- [ ] **Step 2: Commit**

```bash
git add _data/filters.csv
git commit -m "Define Souls on Fire theme taxonomy for thematic transcript visualization"
```

---

### Task 11: Theme-tag the Patricia Poole transcript (editorial pass)

**Files:**
- Modify: `_data/transcripts/patricia-poole.csv`

- [ ] **Step 1: Read through the generated CSV alongside the taxonomy and assign tags**

For each row, decide which of `joy`, `faith`, `struggle`, `community-family`, `education-integration`, `gospel-music`, `activism-change` apply (a row can have zero, one, or several — semicolon-separated, e.g. `faith;gospel-music`). Base this on the actual content of the row's `words` column (e.g. talk of Richard Smallwood/choir favorites → `gospel-music`; the NAACP/school integration passages → `education-integration` and possibly `activism-change`; discussion of the shrinking, aging congregation → `struggle`; memories of Mayday Queen, cornbread, Girl Scouts → `joy`).

Flag any row where the theme is genuinely ambiguous (could reasonably go two different ways, or doesn't fit the taxonomy at all) to the user before finalizing, rather than guessing silently.

- [ ] **Step 2: Save the updated CSV and spot-check a few rows render sensibly**

(Full rendering verification happens in Task 14, once the site is wired up — this step is just re-reading the saved CSV to confirm the edits saved correctly and no rows were accidentally dropped or reordered.)

- [ ] **Step 3: Commit**

```bash
git add _data/transcripts/patricia-poole.csv
git commit -m "Add theme tags to Patricia Poole transcript"
```

---

### Task 12: Theme-tag the Grubb transcript (editorial pass)

**Files:**
- Modify: `_data/transcripts/randy-natasha-grubb.csv`

- [ ] **Step 1: Read through the generated CSV alongside the taxonomy and assign tags**

Same approach as Task 11. E.g.: the Kirk Franklin "Smile" passage → `gospel-music` and likely `joy`; the discussion of scarce Black teachers → `education-integration` and `struggle`; "Church is cool... it's like a family" → `faith` and `community-family`; talk of Pulaski's decline and outgrowing it → `struggle`; the closing reflection on what would help youth → `activism-change`.

Flag ambiguous rows to the user rather than guessing.

- [ ] **Step 2: Save and spot-check**

- [ ] **Step 3: Commit**

```bash
git add _data/transcripts/randy-natasha-grubb.csv
git commit -m "Add theme tags to Randy & Natasha Grubb transcript"
```

---

### Task 13: Add audio files and main metadata

**Files:**
- Create: `objects/patricia-poole.mp3`
- Create: `objects/randy-natasha-grubb.mp3`
- Create: `_data/sof-metadata.csv`
- Modify: `_config.yml`

- [ ] **Step 1: Copy the mp3s into the site's objects directory**

```bash
cd "/Users/mariamyi/Downloads/SOF-oral-histories"
cp "/Users/mariamyi/Downloads/SOF-oral-histories-source/audio/Patricia Poole Interview.mp3" objects/patricia-poole.mp3
cp "/Users/mariamyi/Downloads/SOF-oral-histories-source/audio/Randy & Natasha Grubb Interview.mp3" objects/randy-natasha-grubb.mp3
```

- [ ] **Step 2: Create the main metadata CSV**

Save as `_data/sof-metadata.csv`:

```csv
objectid,parentid,title,interviewee,interviewer,date,description,subject,location,latitude,longitude,rights,rightsstatement,display_template,object_location,type,format
patricia-poole,,Interview with Patricia Poole,Patricia Poole,Clay Adkins,2026-07-19,"Oral history interview with Patricia Poole, covering NAACP-era school integration at Pulaski High School, memories of Calfee School, Clark's Chapel United Methodist Church, and favorite gospel music.","NAACP;integrated schools;youth church participation;Pulaski High School;early integration;gospel music",Pulaski VA,37.0587,-80.7734,,,transcript,/objects/patricia-poole.mp3,sound,audio/mpeg
randy-natasha-grubb,,Interview with Randy & Natasha Grubb,Randy Grubb; Natasha Grubb,Clay Adkins,2026-06-14,"Oral history interview with Randy and Natasha Grubb at First Baptist Church, covering Pulaski County Public Schools, revitalization of Pulaski, and support within the church.","Pulaski County Public Schools;revitalization of Pulaski;support within the church",Pulaski VA,37.0587,-80.7734,,,transcript,/objects/randy-natasha-grubb.mp3,sound,audio/mpeg
```

**Note:** `rights` and `rightsstatement` are intentionally blank — this needs the Calfee Center's actual release-form/rights language before the site goes public. Flag this to the user; do not fill in placeholder legal text.

- [ ] **Step 3: Point the site config at the new metadata file**

In `_config.yml`, change:
```yaml
metadata: demo-ohd-metadata
```
to:
```yaml
metadata: sof-metadata
```

- [ ] **Step 4: Commit**

```bash
git add objects/patricia-poole.mp3 objects/randy-natasha-grubb.mp3 _data/sof-metadata.csv _config.yml
git commit -m "Add interview audio, metadata, and point site config at Souls on Fire collection"
```

---

### Task 14: Install Jekyll dependencies and build the site locally

**Files:** none (environment setup + verification only)

- [ ] **Step 1: Install gems into a project-local path**

System Ruby (2.6.10) can hit permission errors writing to system gem directories, so install into a project-local `vendor/bundle` instead:

```bash
cd "/Users/mariamyi/Downloads/SOF-oral-histories"
bundle config set --local path 'vendor/bundle'
bundle install
```
Expected: completes without error. If it fails with a permissions or Ruby-version error, report the exact error before working around it — don't retry blindly.

- [ ] **Step 2: Start the local Jekyll server**

Run: `bundle exec jekyll serve` (run in the background/a separate terminal since it stays running)
Expected: output ending in `Server address: http://127.0.0.1:4000` with no build errors.

- [ ] **Step 3: Verify both interview pages build and render correctly**

With the server running, check both:
- `http://127.0.0.1:4000/items/patricia-poole.html`
- `http://127.0.0.1:4000/items/randy-natasha-grubb.html`

On each page, confirm:
1. An audio player is present and the mp3 plays.
2. The transcript text appears, broken into speaker turns.
3. The color-coded thematic bar/visualization is visible (this only renders when `_data/filters.csv` is populated and at least one transcript row has a tag — confirmed in Tasks 10-12).
4. Clicking a point on the bar jumps the audio to roughly that point in the interview.

If the colored bar doesn't appear, check the browser console for Jekyll/Liquid errors first, then re-check that `_data/filters.csv` tag values (Task 10) exactly match the tag values used in the transcript CSVs (Tasks 11-12) — they must match exactly (including slug format) for the color mapping to apply.

- [ ] **Step 4: Stop the server**

Ctrl+C in the terminal running `jekyll serve` (or stop the background process).

---

### Task 15: Final review and push

**Files:** none

- [ ] **Step 1: Review the full diff**

```bash
cd "/Users/mariamyi/Downloads/SOF-oral-histories"
git log --oneline main..HEAD 2>/dev/null || git log --oneline
git status
```
Expected: all pipeline scripts, generated CSVs, audio, and config changes are committed; nothing unexpected is left uncommitted.

- [ ] **Step 2: Confirm with the user before pushing**

This pushes real, named individuals' oral history content to a public GitHub repo — confirm the user is ready for that (in particular, that the still-blank `rights`/`rightsstatement` fields from Task 13 are acceptable to leave blank for now, or should be filled in first) before running `git push`.

- [ ] **Step 3: Push (once confirmed)**

```bash
git push -u origin main
```
