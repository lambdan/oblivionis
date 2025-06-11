import datetime
import logging

logger = logging.getLogger("utils")

def now() -> datetime.datetime:
    return datetime.datetime.now(datetime.UTC)

def datetimeFromISO8601(s: str) -> datetime.datetime | None:
    try:
        s = s.upper().strip()
        return datetime.datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception as e:
        return None

def secsToHHMMSS(secs: int) -> str | None:
    try:
        if secs < 0:
            return "00:00:00"
        hours = secs // 3600
        minutes = (secs % 3600) // 60
        seconds = secs % 60
        return f"{hours:02}:{minutes:02}:{seconds:02}"
    except Exception as e:
        logger.error("Error converting seconds to HH:MM:SS format: %s", e)
        return None

def secsFromString(s: str) -> int:
    """
    Returns -1 on error
    """
    # is it a number? then its seconds
    if s.isdigit():
        return int(s)

    # is it HH:MM:SS?
    if ":" in s:
        parts = s.split(":")
        for p in parts:
            if not p.isdigit():
                return -1
        try:
            hrs = int(parts[0])
            if hrs < 0:
                return -1
            mins = int(parts[1])
            if mins < 0 or mins > 59:
                return -1
            secs = int(parts[2])
            if secs < 0 or secs > 59:
                return -1
            return (hrs * 3600) + (mins * 60) + secs
        except: 
            return -1

    # is it in the format "XhYmZs"?
    s = s.strip().lower().replace(" ", "")
    parts = s.split("h")
    if len(parts) == 2:
        hours = int(parts[0])
        parts = parts[1].split("m")
        minutes = int(parts[0])
        seconds = int(parts[1].replace("s", ""))
    else:
        hours = 0
        parts = s.split("m")
        minutes = int(parts[0])
        seconds = int(parts[1].replace("s", ""))
    return hours * 3600 + minutes * 60 + seconds