#! /usr/bin/env python
'''
Created on 01.04.2011

@author: kca
'''
#TODO: proper timeout handling
from __future__ import with_statement

from threading import Lock, Event
from contextlib import contextmanager

class Timeout(Exception):
    pass

class ReverseSemaphore(object):
    def __init__(self, *args, **kw):
        super(ReverseSemaphore, self).__init__(*args, **kw)
        
        self.counter = 0
        self.lock = Lock()
        self.event = Event()
        self.event.set()
        pass
        
    def acquire(self):
        with self.lock:
            self.counter += 1
            self.event.clear()
            pass
        pass
    
    def release(self):
        with self.lock:
            self.counter -= 1
            if self.counter == 0:
                self.event.set()
            if self.counter < 0:
                self.counter = 0
                pass
            pass
        pass
    
    def wait(self):
        return self.event.wait()
        pass
    
    def __enter__(self):
        self.acquire()
        pass
    
    def __exit__ (self, type, value, tb):
        self.release()
        pass
    pass


class RWLock(object):
    def __init__(self, *args, **kw):
        super(RWLock, self).__init__(*args, **kw)
        
        self.write_lock = Lock()
        self.read_lock = ReverseSemaphore()
        self.write_event = Event()
        self.write_event.set()
    
    @contextmanager
    def read_transaction(self, timeout = None):
        self.read_acquire(timeout = timeout) 
        try:
            yield
        finally:
            self.read_release()
            pass
        pass
    
    @contextmanager
    def write_transaction(self, timeout = None):
        self.write_acquire(timeout = timeout)
        try:
            yield
        finally:
            self.write_release()
            pass
        pass
    
    def read_acquire(self, timeout = None):
        self.write_event.wait(timeout = timeout)
        if not self.write_event.is_set():
            raise Timeout()
        self.read_lock.acquire()
        return True
    
    def read_release(self):
        self.read_lock.release()
        pass
    
    def write_acquire(self, timeout = None):
        self.write_lock.acquire() 
        self.write_event.clear()
        self.read_lock.wait()
        pass
    
    def write_release(self):
        self.write_event.set()
        self.write_lock.release()
