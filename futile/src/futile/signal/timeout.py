'''
Created on 20.05.2011

@author: kca
'''

from signal import signal, SIGALRM, alarm
from contextlib import contextmanager
from futile import noop


@contextmanager
def timeout(seconds):
    if not seconds:
        yield
        return
    
    original_handler = signal(SIGALRM, noop)

    try:
        alarm(seconds)
        yield
    finally:
        alarm(0)
        signal(SIGALRM, original_handler)


def Timeout(seconds):
    return lambda: timeout(seconds)
