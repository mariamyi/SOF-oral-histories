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
