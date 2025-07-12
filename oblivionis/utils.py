import datetime
import logging

logger = logging.getLogger("utils")

def now() -> datetime.datetime:
    """
    Shortcut for current time in UTC
    """
    return datetime.datetime.now(datetime.UTC)

def datetimeParse(s: str) -> datetime.datetime | None:
    """
    Parses an datetime from a JS-like ISO8601 string (`YYYY-MM-DDTHH:MM:SSZ`) 
    or 
    relative time (-1h30m5s)
    """
    if s.startswith("-"):
        s = s.lower().strip()
        s = s[1:]  # Remove the leading '-' for easier parsing
        if ":" in s:
            parts = s.split(":")
            if len(parts) != 3:
                return None
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds = int(parts[2])
            return now() - datetime.timedelta(hours=hours, minutes=minutes, seconds=seconds)
        hours = 0
        mins = 0
        secs = 0
        if "h" in s:
            hours = s.split("h")[0]
            s = s.replace(hours + "h", "")
            hours = int(hours)
        if "m" in s:
            mins = s.split("m")[0]
            s = s.replace(mins + "m", "")
            mins = int(mins)
        if "s" in s:
            secs = s.split("s")[0]
            s = s.replace(secs + "s", "")
            secs = int(secs)
        return now() - datetime.timedelta(hours=hours, minutes=mins, seconds=secs)

    try:
        s = s.upper().strip()
        return datetime.datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception as e:
        return None

def secsToHHMMSS(secs: int) -> str:
    """
    Returns a string in HH:MM:SS format
    """
    if secs < 0:
        return "00:00:00"
    try:
        hours = secs // 3600
        minutes = (secs % 3600) // 60
        seconds = secs % 60
        return f"{hours:02}:{minutes:02}:{seconds:02}"
    except Exception as e:
        logger.error("Error converting seconds to HH:MM:SS format: %s", e)
        return "00:00:00"

def secsFromString(s: str) -> int | None:
    """
    Turns a duration string into seconds.
    Supported formats:
    - HH:MM:SS (e.g., 01:30:45)
    - HhMmSs (e.g., 1h30m45s)
    - Just a number (e.g., 3600 = 1 hour)
    Returns None on error
    """
    try:
        s = s.strip().lower().replace(" ", "")
        if ":" in s:
            parts = s.split(":")
            if len(parts) != 3:
                return None
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds = int(parts[2])
            return hours * 3600 + minutes * 60 + seconds
        elif "h" in s or "m" in s or "s" in s:
            hours = minutes = seconds = 0
            if "h" in s:
                hours = int(s.split("h")[0])
            if "m" in s:
                minutes = int(s.split("m")[0].split("h")[-1])
            if "s" in s:
                seconds = int(s.split("s")[0].split("m")[-1])
            return hours * 3600 + minutes * 60 + seconds
        else:
            return int(s)
    except Exception as e:
        logger.error("Error parsing duration string '%s': %s", s, e)
        return None

def parseRange(s: str) -> tuple[int, int] | None:
    """ 
    Attempts to parse a range in the format a-b
    """
    try:
        parts = s.split("-")
        if len(parts) != 2:
            return None
        start = int(parts[0])
        end = int(parts[1])
        return (start, end)
    except Exception as e:
        return None

def normalizeQuotes(s: str) -> str:
    """
    Remove dumb Apple quotes and replaces them with standard quotes
    """
    return s.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'").replace("’", "'").replace("`", "'").replace("´", "'")

def validateDate(date: datetime.datetime) -> str:
    """
    Returns OK if valid
    """
    now = datetime.datetime.now(datetime.UTC)
    if date > now:
        return "Date cannot be in the future"
    
    if date < datetime.datetime(2025, 1, 20, tzinfo=datetime.UTC):
        return "Date cannot be before 2025-01-20 (timeplayed started then!)"
    
    return "OK"

