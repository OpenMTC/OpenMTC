from openmtc.exc import OpenMTCError


class ConfigurationError(OpenMTCError):
    pass


class NetworkManagerException(OpenMTCError):
    """Generic Network Manager exception"""
    pass


class InterfaceNotFoundException(NetworkManagerException):
    """Exception raised if no interface was found matching request"""
    pass

