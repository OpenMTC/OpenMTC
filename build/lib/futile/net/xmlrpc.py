'''
Created on 17.07.2011

@author: kca
'''

from futile import Base
from SimpleXMLRPCServer import SimpleXMLRPCDispatcher

class WSGIXMLRPCRequestHandler(SimpleXMLRPCDispatcher, Base):
	def __init__(self, encoding=None):
		SimpleXMLRPCDispatcher.__init__(self, allow_none = True, encoding = encoding)

	def __call__(self, environ, start_response):
		if environ["REQUEST_METHOD"] != "POST":
			headers = [("Content-type", "text/html")]

			if environ["REQUEST_METHOD"] == "HEAD":
				data = ""
			else:
				data = "<html><head><title>400 Bad request</title></head><body><h1>400 Bad request</h1></body></html>"
			headers.append(("Content-length", str(len(data))))
			start_response("400 Bad request", headers)
			return (data, )

		l = int(environ["CONTENT_LENGTH"])
		request = environ["wsgi.input"].read(l)
		response = self._marshaled_dispatch(request)
		headers = [("Content-type", "text/xml"), ("Content-length", str(len(response)))]
		start_response("200 OK", headers)
		return (response, )

	def _dispatch(self, *args, **kw):
		try:
			result = SimpleXMLRPCDispatcher._dispatch(self, *args, **kw)
		#	self.logger.debug("Result: %s" % (result, ))
			return result
		except:
			self.logger.exception("Error while processing request")
			raise