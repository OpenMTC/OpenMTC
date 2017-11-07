from futile.net.exc import NetworkError


class OpenMTCError(Exception):
    pass


class OpenMTCNetworkError(OpenMTCError, NetworkError):
    pass


class ConnectionFailed(OpenMTCNetworkError):
    pass
