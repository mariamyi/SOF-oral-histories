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
