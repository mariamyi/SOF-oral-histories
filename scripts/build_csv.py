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
