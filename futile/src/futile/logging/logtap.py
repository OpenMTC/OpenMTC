'''
Created on 29.08.2011

@author: kca
'''

import logging
from . import ThreadFilter
from ..collections import get_list
from futile import NOT_SET
from logging import LogRecord, DEBUG
from futile.logging import ErrorLogger

class LogTap(ErrorLogger):
	def __init__(self, handler, logger = None, name = None, level = DEBUG, *args, **kw):
		super(LogTap, self).__init__(name = name, logger = logger, level = level, *args, **kw)
		handler = get_list(handler)
		self.handlers = handler
		self.target_logger = logger or logging.root
			
	def attach(self):
		map(self.target_logger.addHandler, self.handlers)
		
	def detach(self):
		for handler in self.handlers:
			self.target_logger.removeHandler(handler)
			handler.close()
			
	def emit(self, record):
		for handler in self.handlers:
			handler.emit(record)
		
	def __enter__(self):
		self.attach()
		return super(LogTap, self).__enter__()
	
	def __exit__(self, type, value, traceback):
		super(LogTap, self).__exit__(type, value, traceback)
		self.detach()
		
class BufferingLogTap(LogTap):
	log = None
	
	def __init__(self, handler = None, name = None, logger = None, level = DEBUG, capacity = None, memhandler = None, *args, **kw):
		if not memhandler:
			from handlers import BufferingHandler
			memhandler = BufferingHandler(capacity)
			memhandler.addFilter(ThreadFilter())
		self.memhandler = memhandler
		handler = [ memhandler ] + get_list(handler)
		super(BufferingLogTap, self).__init__(handler = handler, logger = logger, name = name, level = level, *args, **kw)
		
	def detach(self):
		self.log = map(lambda r: isinstance(r, LogRecord) and self.memhandler.format(r) or r, self.memhandler.buffer)
		super(BufferingLogTap, self).detach()
		
	def emit(self, record, level = NOT_SET):
		if isinstance(record, LogRecord):
			return super(BufferingLogTap, self).emit(record)
		self.memhandler.buffer.append(record)
