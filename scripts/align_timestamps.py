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
