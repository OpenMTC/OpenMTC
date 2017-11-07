from .json import OneM2MJsonSerializer
from openmtc_onem2m.exc import CSEBadRequest, CSEContentsUnacceptable
from werkzeug import Accept, parse_accept_header
from futile.logging import get_logger
from openmtc.exc import OpenMTCError

_factories = {"application/json": OneM2MJsonSerializer,
              "application/vnd.onem2m-res+json": OneM2MJsonSerializer,
              "application/vnd.onem2m-ntfy+json": OneM2MJsonSerializer,
              "application/vnd.onem2m-attrs+json": OneM2MJsonSerializer,
              "text/plain": OneM2MJsonSerializer}
_serializers = {}


def create_onem2m_serializer(content_type):
    try:
        factory = _factories[content_type]
    except KeyError:
        raise CSEBadRequest("Unsupported content type: %s. Try one of %s" %
                            (content_type, ', '.join(_factories.keys())))
    return factory()


def get_onem2m_supported_content_types():
    return _factories.keys()


def get_onem2m_decoder(content_type):
    # TODO: Check if this is faster than split
    content_type, _, _ = content_type.partition(";")

    content_type = content_type.strip().lower()

    try:
        return _serializers[content_type]
    except KeyError:
        serializer = create_onem2m_serializer(content_type)
        _serializers[content_type] = serializer
        return serializer
get_serializer = get_onem2m_decoder


def get_onem2m_encoder(accept):
    # TODO: optimize
    if accept:
        parsed_accept_header = parse_accept_header(accept, Accept)
        """:type : Accept"""
        supported = get_onem2m_supported_content_types()
        accepted_type = parsed_accept_header.best_match(supported)
        if not accepted_type:
            raise CSEContentsUnacceptable("%s is not supported. "
                                          "Supported content types are: %s" %
                                          (accept, ', '.join(supported)))
    else:
        # TODO: use config["default_content_type"]
        accepted_type = "application/json"

    # TODO: optimize
    return get_serializer(accepted_type)


def register_onem2m_serializer(content_type, factory):
    set_value = _factories.setdefault(content_type, factory)

    if set_value is not factory:
        raise OpenMTCError("Content type is already registered: %s" %
                           (content_type, ))

################################################################################
# import other serializers at serializers
################################################################################
# import impl
# import pkgutil
#
# logger = get_logger(__name__)
#
# for _importer, modname, ispkg in pkgutil.iter_modules(impl.__path__):
#     modname = impl.__name__ + "." + modname
#     logger.debug("Found onem2m serializer module %s (is a package: %s)" %
#                  (modname, ispkg))
#     try:
#         __import__(modname)
#     except:
#         logger.error("Failed to import serializer %s", modname)
#         raise
#     del _importer
#     del modname
#     del ispkg
#
# del impl
# del pkgutil
# del logger

