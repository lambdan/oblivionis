import datetime

def now() -> datetime.datetime:
    return datetime.datetime.now(datetime.UTC)

def datetimeFromISO8601(s: str) -> datetime.datetime:
    s = s.upper().strip()
    return datetime.datetime.fromisoformat(s.replace("Z", "+00:00"))