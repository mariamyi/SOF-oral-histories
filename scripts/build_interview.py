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
import csv
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
    """Convert a .docx file to plain text using macOS's `textutil`.

    docx_path: path to the source .docx transcript.

    Returns: the converted plain text.

    Raises: RuntimeError if textutil fails, or if it exits 0 but produces
    no output (its actual failure mode for a missing/unreadable file:
    textutil exits 0 and writes an error message to stderr instead of
    raising, so a bare `check=True` subprocess call would silently treat
    that as success).
    """
    result = subprocess.run(
        ["textutil", "-convert", "txt", docx_path, "-stdout"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"textutil failed to convert {docx_path!r} "
            f"(exit code {result.returncode}): {result.stderr.strip()}"
        )
    if not result.stdout.strip():
        raise RuntimeError(
            f"textutil produced no text for {docx_path!r}; the docx path is "
            f"likely wrong or unreadable. textutil stderr: {result.stderr.strip()!r}"
        )
    return result.stdout


def get_whisper_words(audio_path, cache_path, model_size="small"):
    """Get word-level Whisper timestamps for audio_path, using a cache if possible.

    audio_path: path to the source audio file.
    cache_path: optional path to a JSON cache file. The cache stores the
        source audio file's size and mtime alongside the words so that a
        cache file accidentally reused across two different audio files is
        detected and ignored (re-transcribed and overwritten) rather than
        silently trusted.
    model_size: Whisper model size to use if transcription is needed.

    Returns: list of {"word": str, "start": float, "end": float}.
    """
    audio_stat = os.stat(audio_path)
    if cache_path and os.path.exists(cache_path):
        with open(cache_path, encoding="utf-8") as f:
            cached = json.load(f)
        if (
            cached.get("audio_size") == audio_stat.st_size
            and cached.get("audio_mtime") == audio_stat.st_mtime
        ):
            return cached["words"]
        print(
            f"Cache at {cache_path!r} does not match {audio_path!r} "
            "(size/mtime mismatch) - re-transcribing.",
            file=sys.stderr,
        )
    words = transcribe_word_timestamps(audio_path, model_size=model_size)
    if cache_path:
        cache_dir = os.path.dirname(cache_path)
        if cache_dir:
            os.makedirs(cache_dir, exist_ok=True)
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "audio_size": audio_stat.st_size,
                    "audio_mtime": audio_stat.st_mtime,
                    "words": words,
                },
                f,
            )
    return words


def _out_has_existing_tags(out_path):
    """Return True if out_path is an existing CSV with any non-empty tags value."""
    if not os.path.exists(out_path):
        return False
    with open(out_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None or "tags" not in reader.fieldnames:
            return False
        return any(row.get("tags", "").strip() for row in reader)


def main():
    """Run the full transcript alignment pipeline end to end.

    Parses CLI args, converts the docx to text, parses speaker turns,
    aligns them to Whisper word timestamps for the audio, and writes the
    result to a CB-OH transcript CSV. Refuses to overwrite an existing
    --out file that already has hand-added tags unless --force is passed.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--docx", required=True)
    parser.add_argument("--audio", required=True)
    parser.add_argument("--aliases", required=True, help="JSON dict of label -> canonical speaker name")
    parser.add_argument("--out", required=True, help="Output CSV path")
    parser.add_argument("--cache", default=None, help="Path to cache raw Whisper word timestamps as JSON")
    parser.add_argument("--model-size", default="small")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite --out even if it already has hand-added tags",
    )
    args = parser.parse_args()

    if not os.path.exists(args.docx):
        print(f"--docx path does not exist: {args.docx}", file=sys.stderr)
        sys.exit(1)
    if not os.path.exists(args.audio):
        print(f"--audio path does not exist: {args.audio}", file=sys.stderr)
        sys.exit(1)

    try:
        aliases = json.loads(args.aliases)
    except json.JSONDecodeError as e:
        print(f"--aliases is not valid JSON: {e}", file=sys.stderr)
        sys.exit(1)

    if _out_has_existing_tags(args.out):
        if not args.force:
            print(
                f"{args.out} already has hand-added tags; refusing to overwrite "
                "without --force.",
                file=sys.stderr,
            )
            sys.exit(1)
        print(
            f"{args.out} already has hand-added tags; overwriting because --force "
            "was passed.",
            file=sys.stderr,
        )

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

    out_dir = os.path.dirname(args.out)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    write_transcript_csv(turns, args.out)
    print(f"Wrote {len(turns)} turns to {args.out}")


if __name__ == "__main__":
    main()
