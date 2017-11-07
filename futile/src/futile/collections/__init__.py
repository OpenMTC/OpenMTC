'''
Created on 17.07.2011

@author: kca
'''

import futile
from futile.basictypes import basestring

try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict

from abc import ABCMeta
from collections import Iterable, Sequence


def is_iterable(o):
    return isinstance(o, Iterable) and not isinstance(o, basestring)


def get_iterable(o):
    if o is None:
        return ()
    return ((not isinstance(o, Iterable) or isinstance(o, basestring))
             and (o,) or o)


def get_list(o):
    if o is None:
        return []
    return ((not isinstance(o, Iterable) or isinstance(o, basestring))
             and [o] or list(o))


def yield_buffer(buffer, chunk_size=None):
    chunk_size = chunk_size or futile.DEFAULT_CHUNK_SIZE

    while True:
        chunk = buffer.read(chunk_size)
        if not chunk:
            return
        yield chunk
