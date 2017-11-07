"""
Created on 26.05.2013

@author: kca
"""
from openmtc.exc import OpenMTCError
from collections import namedtuple


STATUS = namedtuple("STATUS", "numeric_code description http_status_code")

STATUS_ACCEPTED = STATUS(
    1000, "ACCEPTED", 202)
STATUS_OK = STATUS(
    2000, "OK", 200)
STATUS_CREATED = STATUS(
    2001, "CREATED", 201)
STATUS_BAD_REQUEST = STATUS(
    4000, "BAD_REQUEST", 400)
STATUS_NOT_FOUND = STATUS(
    4004, "NOT_FOUND", 404)
STATUS_OPERATION_NOT_ALLOWED = STATUS(
    4005, "OPERATION_NOT_ALLOWED", 405)
STATUS_REQUEST_TIMEOUT = STATUS(
    4008, "REQUEST_TIMEOUT", 408)
STATUS_SUBSCRIPTION_CREATOR_HAS_NO_PRIVILEGE = STATUS(
    4101, ",_SUBSCRIPTION_CREATOR_HAS_NO_PRIVILEGE", 403)
STATUS_CONTENTS_UNACCEPTABLE = STATUS(
    4102, "CONTENTS_UNACCEPTABLE", 400)
STATUS_ORIGINATOR_HAS_NO_PRIVILEGE = STATUS(
    4103, "ORIGINATOR_HAS_NO_PRIVILEGE", 403)
STATUS_GROUP_REQUEST_IDENTIFIER_EXISTS = STATUS(
    4104, "GROUP_REQUEST_IDENTIFIER_EXISTS", 409)
STATUS_CONFLICT = STATUS(
    4105, "CONFLICT", 409)
STATUS_INTERNAL_SERVER_ERROR = STATUS(
    5000, "INTERNAL_SERVER_ERROR", 500)
STATUS_NOT_IMPLEMENTED = STATUS(
    5001, "NOT_IMPLEMENTED", 501)
STATUS_TARGET_NOT_REACHABLE = STATUS(
    5103, "TARGET_NOT_REACHABLE", 404)
STATUS_NO_PRIVILEGE = STATUS(
    5105, "NO_PRIVILEGE", 403)
STATUS_ALREADY_EXISTS = STATUS(
    5106, "ALREADY_EXISTS", 403)
STATUS_TARGET_NOT_SUBSCRIBABLE = STATUS(
    5203, "TARGET_NOT_SUBSCRIBABLE", 403)
STATUS_SUBSCRIPTION_VERIFICATION_INITIATION_FAILED = STATUS(
    5204, "SUBSCRIPTION_VERIFICATION_INITIATION_FAILED", 500)
STATUS_SUBSCRIPTION_HOST_HAS_NO_PRIVILEGE = STATUS(
    5205, "SUBSCRIPTION_HOST_HAS_NO_PRIVILEGE", 403)
STATUS_NON_BLOCKING_REQUEST_NOT_SUPPORTED = STATUS(
    5206, "NON_BLOCKING_REQUEST_NOT_SUPPORTED", 501)
STATUS_EXTERNAL_OBJECT_NOT_REACHABLE = STATUS(
    6003, "EXTERNAL_OBJECT_NOT_REACHABLE", 404)
STATUS_EXTERNAL_OBJECT_NOT_FOUND = STATUS(
    6005, "EXTERNAL_OBJECT_NOT_FOUND", 404)
STATUS_MAX_NUMBER_OF_MEMBER_EXCEEDED = STATUS(
    6010, "MAX_NUMBER_OF_MEMBER_EXCEEDED", 400)
STATUS_MEMBER_TYPE_INCONSISTENT = STATUS(
    6011, "MEMBER_TYPE_INCONSISTENT", 400)
STATUS_MANAGEMENT_SESSION_CANNOT_BE_ESTABLISHED = STATUS(
    6020, "MANAGEMENT_SESSION_CANNOT_BE_ESTABLISHED", 500)
STATUS_MANAGEMENT_SESSION_ESTABLISHMENT_TIMEOUT = STATUS(
    6021, "MANAGEMENT_SESSION_ESTABLISHMENT_TIMEOUT", 500)
STATUS_INVALID_CMDTYPE = STATUS(
    6022, "INVALID_CMDTYPE", 400)
STATUS_INVALID_ARGUMENTS = STATUS(
    6023, "INVALID_ARGUMENTS", 400)
STATUS_INSUFFICIENT_ARGUMENT = STATUS(
    6024, "INSUFFICIENT_ARGUMENT", 400)
STATUS_MGMT_CONVERSION_ERROR = STATUS(
    6025, "MGMT_CONVERSION_ERROR", 500)
STATUS_CANCELLATION_FAILED = STATUS(
    6026, "CANCELLATION_FAILED", 500)
STATUS_ALREADY_COMPLETE = STATUS(
    6028, "ALREADY_COMPLETE", 400)
STATUS_COMMAND_NOT_CANCELLABLE = STATUS(
    6029, "COMMAND_NOT_CANCELLABLE", 400)
STATUS_IMPERSONATION_ERROR = STATUS(
    6101, "IMPERSONATION_ERROR", 400)


_status_map = {v.numeric_code: v for v in globals().values()
               if isinstance(v, STATUS)}

ERROR_MIN = STATUS_BAD_REQUEST.numeric_code


class OneM2MError(OpenMTCError):
    pass


class CSEError(OneM2MError):
    response_status_code = STATUS_INTERNAL_SERVER_ERROR

    @property
    def status_code(self):
        return self.response_status_code.http_status_code

    @property
    def rsc(self):
        return self.response_status_code.numeric_code


class CSENotFound(CSEError):
    response_status_code = STATUS_NOT_FOUND


class CSEOperationNotAllowed(CSEError):
    response_status_code = STATUS_OPERATION_NOT_ALLOWED


class CSENotImplemented(CSEError):
    response_status_code = STATUS_NOT_IMPLEMENTED


class CSETargetNotReachable(CSEError):
    response_status_code = STATUS_TARGET_NOT_REACHABLE


class CSEConflict(CSEError):
    response_status_code = STATUS_CONFLICT


class CSEBadRequest(CSEError):
    response_status_code = STATUS_BAD_REQUEST


class CSESyntaxError(CSEBadRequest):
    response_status_code = STATUS_BAD_REQUEST


class CSEPermissionDenied(CSEError):
    response_status_code = STATUS_ORIGINATOR_HAS_NO_PRIVILEGE


class CSEImpersonationError(CSEBadRequest):
    response_status_code = STATUS_IMPERSONATION_ERROR


class CSEValueError(CSESyntaxError, ValueError):
    pass


class CSETypeError(CSESyntaxError, TypeError):
    pass


class CSEMissingValue(CSESyntaxError):
    pass


class CSEContentsUnacceptable(CSEError):
    response_status_code = STATUS_CONTENTS_UNACCEPTABLE


_error_map = {
    STATUS_INTERNAL_SERVER_ERROR.numeric_code: CSEError
}


def get_error_class(rsc):
    return _error_map.get(int(rsc), CSEError)


def get_response_status(rsc):
    return _status_map.get(int(rsc), STATUS_INTERNAL_SERVER_ERROR)


def all_subclasses(cls):
    return cls.__subclasses__() + [g for s in cls.__subclasses__()
                                   for g in all_subclasses(s)]


for c in all_subclasses(CSEError):
    try:
        code = vars(c)["response_status_code"].numeric_code
    except KeyError:
        continue
    _error_map[code] = c

del c, code
