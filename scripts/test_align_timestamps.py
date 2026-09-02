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
