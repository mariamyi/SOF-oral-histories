from format_timestamp import format_timestamp

def test_zero_seconds():
    assert format_timestamp(0) == "0:00:00"

def test_seconds_and_minutes():
    assert format_timestamp(75) == "0:01:15"

def test_rounds_to_nearest_second():
    assert format_timestamp(75.6) == "0:01:16"

def test_over_an_hour():
    assert format_timestamp(3661) == "1:01:01"
