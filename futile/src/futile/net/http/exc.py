'''
Created on 21.07.2011

@author: kca
'''


from futile.net.exc import NetworkError

STATUS_STRINGS = {
    100: "Continue",
    101: "Switching Protocols",
    200: "Ok",
    201: "Created",
    202: "Accepted",
    203: "Non-Authoritative Information",
    204: "No Content",
    205: "Reset Content",
    206: "Partial Content",
    300: "Multiple Choices",
    301: "Moved Permanently",
    302: "Found",
    303: "See Other",
    304: "Not Modfied",
    305: "Use Proxy",
    306: "",
    307: "Temporary Redirect",
    400: "Bad Request",
    401: "Unauthorized",
    402: "Payment Required",
    403: "Forbidden",
    404: "Not Found",
    405: "Method Not Allowed",
    406: "Not Acceptable",
    407: "Proxy Authentication Required",
    408: "Request Timeout",
    409: "Conflict",
    410: "Gone",
    411: "Length Required",
    412: "Precondition Failed",
    413: "Request Entity Too Large",
    414: "Request-URI Too Long",
    415: "Unsupported Media Type",
    416: "Requested Range Not Satisfiable",
    417: "Expectation Failed",
    500: "Internal Server Error",
    501: "Not Implemented",
    502: "Bad Gateway",
    503: "Service Unavailable",
    504: "Gateway Timeout",
}

STATUS_MIN = 100
STATUS_MAX = 504
ERROR_MIN = 400
ERROR_MAX = 504


def get_error_message(statuscode):
    try:
        return STATUS_STRINGS[statuscode]
    except KeyError:
        raise ValueError(statuscode)


class HTTPErrorType(type):
    __classes = {}

    @classmethod
    def get_error_class(cls, status):
        try:
            status = int(status)
        except (TypeError, ValueError):
            raise ValueError("Not a valid HTTP error code: '%s'" % (status, ))

        try:
            errorcls = cls.__classes[status]
        except KeyError:
            if status < STATUS_MIN or status > STATUS_MAX:
                raise ValueError("Not a valid HTTP error code: %s" % (status,))
            name = "HTTPError%s" % (status, )
            errorcls = cls(name, (HTTPError, ), {"__init__":
                                                 cls._make_init(status)})
            cls.__classes[status] = errorcls
            globals()[name] = errorcls

        return errorcls

    def __call__(self, *args, **kw):
        if self is HTTPError:
            try:
                status = kw.pop("status")
            except KeyError:
                try:
                    status = args[0]
                    args = args[1:]
                except IndexError:
                    return super(HTTPErrorType, self).__call__(*args, **kw)

            self = self.get_error_class(status)
        return super(HTTPErrorType, self).__call__(*args, **kw)

    @classmethod
    def _make_init(cls, status):
        def __init__(self, msg=None, reason=None, *args, **kw):
            super(self.__class__, self).__init__(status=status,
                               reason=reason, msg=msg, *args, **kw)
        return __init__

get_error_class = HTTPErrorType.get_error_class


class HTTPError(NetworkError):
    __metaclass__ = HTTPErrorType

    def __init__(self, status, reason=None, msg=None, *args, **kw):
        status = int(status)
        if not reason:
            reason = STATUS_STRINGS.get(status, "Unknown Error")
        if not msg:
            msg = "HTTP Error %s - %s" % (status, reason)
        super(HTTPError, self).__init__(msg, status, reason, *args, **kw)

    @property
    def message(self):
        return self.args[0]

    @property
    def status(self):
        return self.args[1]

    @property
    def reason(self):
        return self.args[2]
