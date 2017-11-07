from futile.logging import get_logger
from openmtc.model import ModelTypeError
from openmtc_cse.methoddomain.filtercriteria import filters
from openmtc_onem2m.exc import CSEBadRequest
from openmtc_onem2m.model import FilterCriteria

_logger = get_logger(__name__)


def check_match(resource, filter_criteria):
    _logger.debug("checking if filter criteria '%s' are matched by "
                  "resource '%s'", filter_criteria, resource)
    for criteria, value in filter_criteria.get_values(True).iteritems():
        if not value:
            continue
        _logger.debug("checking if resource matches: %s=%s", criteria, value)
        try:
            filter_function = getattr(filters, criteria)
        except AttributeError:
            _logger.error("'%s' is not a valid filter criterion", criteria)
            return False
        else:
            if not filter_function(resource, value):
                _logger.debug("resource '%s' does not match criterion '%s=%s'",
                              resource, criteria, value)
                return False

    _logger.debug("resource '%s' matches filter criteria '%s'",
                  resource, filter_criteria)
    return True


def parse_filter_criteria(filter_criteria):
    if filter_criteria is None:
        filter_criteria = {}
    _logger.debug("parsing '%s'", filter_criteria)
    int_criteria = ('stateTagSmaller', 'stateTagBigger', 'resourceType',
                    'sizeAbove', 'sizeBelow', 'filterUsage', 'limit')
    parsed_criteria = {}
    for k, v in filter_criteria.iteritems():
        if k in int_criteria:
            if isinstance(v, list):
                parsed_criteria[k] = map(int, v)
            else:
                parsed_criteria[k] = int(v)
        else:
            parsed_criteria[k] = v

    try:
        return FilterCriteria(**parsed_criteria)
    except ModelTypeError:
        raise CSEBadRequest()
