'''
Created on 30.08.2011

@author: kca
'''

from logging.handlers import BufferingHandler as _BufferingHandler

class BufferingHandler(_BufferingHandler):
	def __init__(self, capacity = None):
		_BufferingHandler.__init__(self, capacity = capacity)
		
	def shouldFlush(self, record):
		return self.capacity and super(BufferingHandler, self).shouldFlush(record) or False
