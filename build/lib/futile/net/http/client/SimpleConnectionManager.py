'''
Created on 19.03.2013

@author: kca
'''

from httplib import HTTPConnection, HTTPSConnection
from futile.logging import LoggerMixin

class HttplibResponseWrapper(LoggerMixin):
	def __init__(self, connection, *args, **kw):
		super(HttplibResponseWrapper, self).__init__(*args, **kw)
		
		self.__response = connection.getresponse()
		self.__connection = connection
		
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
			self.logger.exception("Error closing response")
		finally:
			self.__connection.close()

class SimpleConnectionManager(LoggerMixin):
	def __init__(self, host, port, certfile = None, keyfile = None, force_ssl = False, *args, **kw):
		super(SimpleConnectionManager, self).__init__(*args, **kw)
		
		self.logger.debug("Creating SimpleConnectionManager for %s:%s", host, port)
		
		if keyfile or certfile or force_ssl:
			self.__certfile = certfile
			self.__keyfile = keyfile
			self._get_connection = self._get_secure_connection
		
		self.__host = host
		self.__port = port
		
	def request(self, method, path, body, headers, timeout):
		connection = self._get_connection(timeout)
		try:
			connection.request(method, path, body, headers)
			return HttplibResponseWrapper(connection)
		except:
			connection.close()
			raise

	def _get_connection(self, timeout):
		return HTTPConnection(self.__host, self.__port, timeout = timeout)
	
	def _get_secure_connection(self, timeout):
		return HTTPSConnection(self.__host, self.__port, self.__keyfile, self.__certfile, timeout = timeout)
