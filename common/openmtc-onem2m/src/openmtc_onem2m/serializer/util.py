from futile.logging import get_logger
from openmtc_onem2m.exc import CSEValueError
from openmtc_onem2m.serializer import get_onem2m_encoder, get_onem2m_decoder

logger = get_logger(__name__)


def decode_onem2m_content(content, content_type):
    if content == "":
        content = None
    if content_type and content is not None:
        serializer = get_onem2m_decoder(content_type)
        try:
            data = serializer.decode(content)
        except CSEValueError as e:
            logger.exception("Error reading input")
            raise e

        return data
    return None


def encode_onem2m_content(content, content_type, pretty=False, path=None,
                          fields=None):
    logger.debug("Encoding result: %s - %s", content, content_type)

    if content is None:
        return None, None

    serializer = get_onem2m_encoder(content_type)

    data = serializer.encode_resource(content, pretty=pretty, path=path,
                                      fields=fields)

    return content_type + "; charset=utf-8", data
