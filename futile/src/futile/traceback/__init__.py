import sys
from traceback import format_exception

def get_traceback(self, exc_info=None):
    return ''.join(format_exception(*(exc_info or sys.exc_info())))


def current_stack(skip=0):
    try:
        1 / 0
    except ZeroDivisionError:
        f = sys.exc_info()[2].tb_frame
    for _ in xrange(skip + 2):
        f = f.f_back
    lst = []
    while f is not None:
        lst.append((f, f.f_lineno))
        f = f.f_back
    return lst
