from futile.logging import get_logger
from futile.collections import get_iterable

_logger = get_logger(__name__)

"""
check TS-0001-oneM2M-Functional-Architecture-V-2014-08, page 59
"""


def modifiedSince(resource, value):
    try:
        return resource.lastModifiedTime > value
    except AttributeError:
        pass


def unmodifiedSince(resource, value):
    try:
        return resource.lastModifiedTime < value
    except AttributeError:
        pass


def createdAfter(resource, value):
    try:
        return resource.creationTime > value
    except AttributeError:
        pass


def createdBefore(resource, value):
    try:
        return resource.creationTime < value
    except AttributeError:
        pass


def contentType(resource, value):
    try:
        return any(map(resource.contentType.__contains__, get_iterable(value)))
    except AttributeError:
        pass


def stateTagSmaller(resource, value):
    """
    Check if the stateTag attribute of the resource is smaller than the specified value.

    :param resource:
    :param value:
    :return:
    :rtype: bool
    """
    try:
        return resource.stateTag < value
    except AttributeError:
        pass


def stateTagBigger(resource, value):
    """
    Check if the stateTag attribute of the resource is bigger than the specified value.
    :param resource:
    :type resource:
    :param value:
    :type value:
    :return:
    :rtype: bool
    """
    try:
        return resource.stateTag > value
    except AttributeError:
        pass


def expireBefore(resource, value):
    """
    Check if the expirationTime attribute of the resource is chronologically before the specified value.

    :param resource:
    :type resource:
    :param value:
    :type value:
    :return:
    :rtype:
    """
    try:
        return resource.expirationTime < value
    except AttributeError:
        pass


def expireAfter(resource, value):
    """
    Check if the expirationTime attribute of the resource is chronologically after the specified value.

    :param resource:
    :type resource:
    :param value:
    :type value:
    :return:
    :rtype:
    """
    try:
        return resource.expirationTime > value
    except AttributeError:
        pass


def labels(resource, values):
    """
    Check if the labels attributes of the resource matches the specified value.
    :param resource:
    :type resource:
    :param values:
    :type values:
    :return:
    :rtype:
    """
    def test(value):
        try:
            return value in resource.labels
        except (AttributeError, TypeError):
            return False

    return any(map(test, values))


def resourceType(resource, values):
    """
    The resourceType attribute of the resource is the same as the specified
    value. It also allows discriminating between normal and announced resources.

    :param resource:
    :type resource:
    :param values:
    :type values:
    :return:
    :rtype:
    """
    def test(value):
        try:
            return resource.resourceType == int(value)
        except AttributeError:
            return False

    return any(map(test, values))


def sizeAbove(resource, value):
    """
    Check if the contentSize attribute of the <contentInstance> resource is
    equal to or greater than the specified value.
    :param resource:
    :type resource:
    :param value:
    :type value:
    :return:
    :rtype:
    """
    try:
        return resource.contentSize >= value
    except AttributeError:
        pass


def sizeBelow(resource, value):
    """
    Check if the contentSize attribute of the <contentInstance> resource is smaller than the specified value.
    :param resource:
    :type resource:
    :param value:
    :type value: int
    :return:
    :rtype:
    """
    try:
        return resource.contentSize < value
    except AttributeError:
        pass


def limit(resource, value):
    """
    Check if this is a valid limit for the number of matching resources to be specified.

    :param resource:
    :type resource:
    :param value: specified limit
    :type value: int
    :return: True if valid limit, False otherwise
    :rtype: bool
    """
    return value > 0


def filterUsage(resource, value):
    """
    Indicates how the filter criteria is used.
    E.g., if this parameter is not provided, the Retrieve operation is for generic retrieve operation.
    If filterUsage is provided, the Retrieve operation is for resource <discovery>.

    :param resource:
    :type resource:
    :param value:
    :type value: bool
    :return:
    :rtype: bool
    """
    # if value:
    #     return True
    # else:
    #     return False
    return True


filters = [stateTagSmaller, stateTagBigger, expireBefore, expireAfter, labels,
           resourceType, sizeAbove, sizeBelow, limit, filterUsage]
