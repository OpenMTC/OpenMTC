'''
Created on 25.07.2011

@author: kca
'''

import sys
from .logging import get_logger

try:
    from lxml import etree as impl
    from lxml.etree import tostring as _ts

    get_logger(__name__).debug("Using lxml etree implementation1.")

    def tostring(element, encoding="utf-8", pretty_print=False):
        return _ts(element, encoding=encoding, pretty_print=pretty_print)
except ImportError:
    logger = get_logger(__name__)
    logger.warning(
        "lxml library not found, trying builtin ElementTree implementations. Pretty printing will be disabled.")
    try:
        from xml.etree import cElementTree as impl

        try:
            impl.ParseError = impl.XMLParserError
        except AttributeError:
            pass
        logger.debug("Using native xml.etree.cElementTree")
    except ImportError:
        from xml.etree import ElementTree as impl

        logger.debug("Using python xml.etree.ElementTree")

    _ts = impl.tostring

    def tostring(element, encoding="utf-8", pretty_print=False):
        return _ts(element, encoding=encoding)

    impl.tostring = tostring
    impl.XMLSyntaxError = impl.ParseError

sys.modules[__name__ + ".impl"] = sys.modules[__name__ + ".ElementTree"] = ElementTree = impl

