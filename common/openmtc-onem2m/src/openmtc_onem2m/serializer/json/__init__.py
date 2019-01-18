from openmtc_onem2m.serializer.base import OneM2MDictSerializer
from json import JSONEncoder
from futile.logging import get_logger
from datetime import datetime
from openmtc_onem2m.model import ContentInstance

logger = get_logger(__name__)

# rst: ujson and yajl are not supporting object_hooks, but conversion is needed
# rst: some measurements are necessary what is better
# try:
#     from ujson import load, loads
#     logger.debug("using ujson for decoding JSON")
# except ImportError:
# try:
#     from yajl import load, loads
#     logger.debug("using yajl for decoding JSON")
# except ImportError:
try:
    # simplejson is faster on decoding, tiny bit slower on encoding
    from simplejson import load, loads
    logger.debug("using simplejson for decoding JSON")
except ImportError:
    logger.debug("using builtin json for decoding JSON")
    from json import load, loads


del logger


def _default(x):
    if isinstance(x, datetime):
        return x.strftime("%Y%m%dT%H%M%S")
    elif isinstance(x, ContentInstance):
        return x.resourceID
    else:
        try:  # handle model classes
            return x.values
        except AttributeError:
            raise TypeError("%s (%s)" % (x, type(x)))


_simple_encoder = JSONEncoder(check_circular=False, separators=(',', ':'),
                              default=_default)

_pretty_encoder = JSONEncoder(default=_default, indent=2,
                              separators=(',', ':'),
                              check_circular=False)


class OneM2MJsonSerializer(OneM2MDictSerializer):
    def __init__(self, *args, **kw):

        self.loads = loads
        self.load = load
        self.dumps = _simple_encoder.encode
        self.pretty_dumps = _pretty_encoder.encode
