from datetime import datetime, timedelta, tzinfo
import time

ZERO = timedelta(0)


class Utc(tzinfo):
    """UTC
    """
    __slots__ = ()

    def utcoffset(self, dt):
        return ZERO

    def tzname(self, dt):
        return "UTC"

    def dst(self, dt):
        return ZERO

UTC = Utc()


#del Utc


def datetime_now():
    return datetime.now(UTC)


def datetime_the_future(offset = 0):
    """ Returns a datetime instance <offset> seconds in the future.
        @note: if no offset is provided or offset == 0, this is equivalent to datetime_now
        @param offset: seconds from now
        @return: datetime in <offset> seconds
    """
    f = time.time() + offset
    return datetime.fromtimestamp(f, UTC)

