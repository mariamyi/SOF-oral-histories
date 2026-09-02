def format_timestamp(seconds):
    """Format a number of seconds as CB-OH's expected h:mm:ss timestamp string."""
    total = int(round(seconds))
    h = total // 3600
    m = (total % 3600) // 60
    s = total % 60
    return f"{h}:{m:02d}:{s:02d}"
