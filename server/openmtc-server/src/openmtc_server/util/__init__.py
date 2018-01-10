from urllib import quote
from datetime import datetime

from mimeparse import parse_mime_type

import aplus
from futile.logging import get_logger
from openmtc.exc import OpenMTCNetworkError
from openmtc_onem2m.exc import CSEError
from openmtc_onem2m.transport import OneM2MErrorResponse

logger = get_logger(__name__)


def log_error(error):
    try:
        return error.status_code == 500
    except AttributeError:
        try:
            return error.statusCode == 500
        except AttributeError:
            return not isinstance(error, (OpenMTCNetworkError, CSEError,
                                          OneM2MErrorResponse))


aplus.log_error = log_error


def uri_safe(s):
    return quote(s.replace("/", "_"), safe='~')


def is_text_content(mimetype):
    try:
        maintype, subtype, _ = parse_mime_type(mimetype)

        maintype = maintype.lower()

        if maintype == "text":
            return True

        if maintype == "application":
            return subtype.rpartition("+")[-1].lower() in ("xml", "json")
    except Exception as e:
        logger.warn("Failed to parse mimetype '%s': %s", mimetype, e)

    return False


def join_url(base, path):
    if not base.endswith("/"):
        if not path.startswith("/"):
            base += "/"
    elif path.startswith("/"):
        path = path[1:]
    return base + path


def match_now_cron(cron):
    return match_time_cron(datetime.now(), cron)


def match_time_cron(time, cron):
    cron_parts = cron.split(' ')

    if len(cron_parts) < 5:
        return False

    minute, hour, day, month, weekday = cron_parts

    to_check = {
        'minute': minute,
        'hour': hour,
        'day': day,
        'month': month,
        'weekday': weekday
    }

    ranges = {
        'minute': '0-59',
        'hour': '0-23',
        'day': '1-31',
        'month': '1-12',
        'weekday': '0-6'
    }

    for c in to_check.keys():
        val = to_check[c]
        values = []

        # For patters like 0-23/2
        if val.find('/') >= 0:
            # Get the range and step
            _range, steps = val.split('/')
            steps = int(steps)

            # Now get the start and stop
            if _range == '*':
                _range = ranges[c]

            start, stop = map(int, _range.split('-'))

            for i in range(start, stop, steps):
                values.append(i)

        # For patters like : 2 or 2,5,8 or 2-23
        else:
            k = val.split(',')

            for v in k:
                if v.find('-') >= 0:
                    start, stop = map(int, v.split('-'))

                    for i in range(start, stop):
                        values.append(i)
                elif v == '*':
                    values.append('*')
                else:
                    values.append(int(v))

        if c is 'weekday':
            if time.weekday() not in values and val != '*':
                return False
        else:
            if getattr(time, c) not in values and val != '*':
                return False

    return True
