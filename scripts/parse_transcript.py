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
