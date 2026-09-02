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
