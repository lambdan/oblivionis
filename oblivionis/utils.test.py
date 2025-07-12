import datetime
import string
import sys
import oblivionis.utils as utils

# TODO: Proper python test framework?

def fail():
    sys.exit(1)

def stringEq(s1: str, s2: str, msg: str):
    print(f"{msg}", end="... ")
    if s1 != s2:
        print(f"❌ Expected '{s2}', got '{s1}'")
        fail()
    else:
        print("✅")

def dtEqual(dt1: datetime.datetime | None, dt2: datetime.datetime | None, msg: str):
    print(f"{msg}", end="... ")
    if dt1 is None:
        print("❌ dt1 is None")
        fail()
        return
    if dt2 is None:
        print("❌ dt2 is None")
        fail()
        return
    delta = abs((dt1 - dt2).total_seconds())
    if delta > 0.1:
        print(f"❌ Delta too large: {delta} seconds")
        fail()
        return
    print("✅")

############
# datetimes
############

print("utils.now()")


dtEqual(utils.now(), datetime.datetime.now(datetime.UTC), "utils.now() is now")

print("utils.datetimeParse")

dtEqual(utils.datetimeParse("2023-10-01T12:00:00Z"), datetime.datetime(2023, 10, 1, 12, 0, tzinfo=datetime.UTC), "absolute js format")
dtEqual(utils.datetimeParse("-1h30m5s"), datetime.datetime.now(datetime.UTC) - datetime.timedelta(hours=1, minutes=30, seconds=5), "hours, minutes, seconds")
dtEqual(utils.datetimeParse("-666s"), datetime.datetime.now(datetime.UTC) - datetime.timedelta(seconds=666), "just seconds")
dtEqual(utils.datetimeParse("-666h"), datetime.datetime.now(datetime.UTC) - datetime.timedelta(hours=666), "just hours")
dtEqual(utils.datetimeParse("-666m"), datetime.datetime.now(datetime.UTC) - datetime.timedelta(minutes=666), "just mins")
dtEqual(utils.datetimeParse("-666m666s"), datetime.datetime.now(datetime.UTC) - datetime.timedelta(minutes=666,seconds=666), "just mins and seconds")
dtEqual(utils.datetimeParse("-666h666s"), datetime.datetime.now(datetime.UTC) - datetime.timedelta(hours=666,seconds=666), "just hours and seconds")
dtEqual(utils.datetimeParse("-666h666m"), datetime.datetime.now(datetime.UTC) - datetime.timedelta(hours=666,minutes=666), "just hours and minutes")

# hh:mm:ss format

dtEqual(utils.datetimeParse("-00:01:01"), datetime.datetime.now(datetime.UTC) - datetime.timedelta(minutes=1, seconds=1), "-00:00:01")

dtEqual(utils.datetimeParse("-01:01:01"), datetime.datetime.now(datetime.UTC) - datetime.timedelta(hours=1, minutes=1, seconds=1), "-00:00:01")

dtEqual(utils.datetimeParse("-00:00:01"), datetime.datetime.now(datetime.UTC) - datetime.timedelta(seconds=1), "-00:00:01")



###########
# secs to hh:mm:ss
###########

print("secsToHHMMSS")

stringEq(utils.secsToHHMMSS(0), "00:00:00", "(0)")
stringEq(utils.secsToHHMMSS(1), "00:00:01", "(1)")
stringEq(utils.secsToHHMMSS(60), "00:01:00", "(60)")
stringEq(utils.secsToHHMMSS(3600), "01:00:00", "(3600)")
stringEq(utils.secsToHHMMSS(3661), "01:01:01", "(3661)")
stringEq(utils.secsToHHMMSS(86400), "24:00:00", "(86400)")
stringEq(utils.secsToHHMMSS(-1), "00:00:00", "(-1)")
stringEq(utils.secsToHHMMSS(-3600), "00:00:00", "(-3600)")

###############
# secsFromString
###############

print ("secsFromString")

def secsFromStringTest(input_str: str, expected: int | None):
    print(f"{input_str}", end="... ")
    result = utils.secsFromString(input_str)
    if result != expected:
        print(f"❌ Expected {expected}, got {result}")
        fail()
    else:
        print("✅")

secsFromStringTest("01:30:45", 5445)
secsFromStringTest("00:00:00", 0)
secsFromStringTest("01:00:00", 3600)
secsFromStringTest("00:01:00", 60)
secsFromStringTest("00:00:01", 1)
secsFromStringTest("1h30m45s", 5445)
secsFromStringTest("1h30m", 5400)
secsFromStringTest("1h", 3600)
secsFromStringTest("30m", 1800)
secsFromStringTest("45s", 45)
secsFromStringTest("1h30m45s", 5445)

##################
# parseRange
##################

print ("parseRange")

def parseRangeTest(input_str: str, expected: tuple|None):
    print(f"{input_str}", end="... ")
    try:
        result = utils.parseRange(input_str)
        if result != expected:
            print(f"❌ Expected {expected}, got {result}")
            fail()
        else:
            print("✅")
    except Exception as e:
        print(f"❌ Exception: {e}")
        fail()

parseRangeTest("1-10", (1, 10))
parseRangeTest("5-15", (5, 15))
parseRangeTest("100-200", (100, 200))
parseRangeTest("0-0", (0, 0))
parseRangeTest("1-1", (1, 1))
parseRangeTest("1-10-20", None)
parseRangeTest("10", None)
parseRangeTest("1-", None)
parseRangeTest("-1-", None)
parseRangeTest("-1", None)

#######################
# normalizeQuotes
#######################

print("normalizeQuotes")

stringEq(utils.normalizeQuotes('Hello "World"'), 'Hello "World"', "good quotes")
stringEq(utils.normalizeQuotes('Hello “World”'), 'Hello "World"', "fancy quotes")
stringEq(utils.normalizeQuotes("It's a test"), "It's a test", "apostrophe")
stringEq(utils.normalizeQuotes("‘Hello’"), "'Hello'", "fancy apostrophe")
stringEq(utils.normalizeQuotes("`Hello`"), "'Hello'", "backticks")
stringEq(utils.normalizeQuotes("´Hello´"), "'Hello'", "accented quotes")

########################
# validate date
########################

print("validateDate")

def validateDateTest(input_date: datetime.datetime, ok: bool):
    print(f"{input_date.isoformat()}", end="... ")
    try:
        result = utils.validateDate(input_date)
        if result == "OK" and not ok:
            print(f"❌ Expected error, but got OK")
            fail()
        else:
            print("✅")
    except Exception as e:
        print(f"❌ Exception: {e}")
        fail()

validateDateTest(datetime.datetime(2025, 1, 20, tzinfo=datetime.UTC), True)
validateDateTest(datetime.datetime(2025, 1, 19, tzinfo=datetime.UTC), False)
validateDateTest(utils.now(), True)
validateDateTest(datetime.datetime(1969, 1, 19, tzinfo=datetime.UTC), False)

#############################

print("All tests passed!")
sys.exit(0)