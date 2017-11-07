'''
Created on 17.07.2011

@author: kca
'''
try:
	from httplib import HTTPConnection as _HTTPConnection, HTTPSConnection as _HTTPSConnection
except ImportError:
	from http.client import HTTPConnection as _HTTPConnection, HTTPSConnection as _HTTPSConnection
	
from futile.contextlib import closing
from futile import NOT_SET
import socket
from . import exc as _exc
import sys
import types

try:
	from urllib import quote, quote_plus, unquote, unquote_plus
except ImportError:
	from urllib.parse import quote, quote_plus, unquote, unquote_plus

class HTTPResponseWrapper(object):
	def __init__(self, connection, response, *args, **kw):
		super(HTTPResponseWrapper, self).__init__(*args, **kw)
		
		self.__response = response
		self.__connection = connection
		
	#def __del__(self):
	#	self.close()
		
	def __getattr__(self, k):
		return getattr(self.__response, k)
	
	def __enter__(self):
		return self.__response
		
	def __exit__(self, exc_type, exc_val, exc_tb):
		self.close()
		
	def close(self):
		try:
			self.__response.close()
		except:
			pass
		finally:
			self.__connection.close()
			
class HTTPConnection(_HTTPConnection):
	response_wrapper = closing
	
	def __init__(self, host, port=None, strict=None, timeout=socket._GLOBAL_DEFAULT_TIMEOUT, source_address=None, response_wrapper = NOT_SET):
		_HTTPConnection.__init__(self, host, port, strict, timeout, source_address)
		if response_wrapper is not NOT_SET:
			self.response_wrapper = response_wrapper
		
	def getresponse(self, buffering = False):
		r = _HTTPConnection.getresponse(self, buffering)
		if self.response_wrapper:
			r = self.response_wrapper(r)
		return r
	
class HTTPSConnection(_HTTPSConnection):
	response_wrapper = closing
	
	def __init__(self, host, port=None, key_file = None, cert_file = None, strict=None, timeout=socket._GLOBAL_DEFAULT_TIMEOUT, source_address=None, response_wrapper = NOT_SET):
		_HTTPSConnection.__init__(self, host, port, key_file = key_file, cert_file = cert_file, strict = strict, timeout = timeout, source_address = source_address)
		if response_wrapper is not NOT_SET:
			self.response_wrapper = response_wrapper
		
	def getresponse(self, buffering = False):
		r = _HTTPSConnection.getresponse(self, buffering)
		if self.response_wrapper:
			r = self.response_wrapper(r)
		return r
	

class exc(types.ModuleType):
	def __getattr__(self, k):
		try:
			v = getattr(_exc, k)
		except AttributeError:
			if not k.startswith("HTTPError"):
				raise	
			v = _exc.get_error_class(k[9:])
		setattr(self, k, v)
		return v

		
name = __name__ + ".exc"
exc = exc(name)
sys.modules[name] = exc
del name

			