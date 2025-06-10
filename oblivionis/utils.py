import datetime

def now() -> datetime.datetime:
    return datetime.datetime.now(datetime.UTC)

def datetimeFromISO8601(s: str) -> datetime.datetime:
    s = s.upper().strip()
    return datetime.datetime.fromisoformat(s.replace("Z", "+00:00"))

def secsToHHMMSS(secs: int) -> str:
    if secs < 0:
        return "00:00:00"
    hours = secs // 3600
    minutes = (secs % 3600) // 60
    seconds = secs % 60
    return f"{hours:02}h{minutes:02}m{seconds:02}s"