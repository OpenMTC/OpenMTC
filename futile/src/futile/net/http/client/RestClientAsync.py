'''
Created on 21.05.2011

@author: kca
'''

from base64 import b64encode
from cStringIO import StringIO
from logging import DEBUG
from socket import getservbyname
from urllib2 import quote
from urlparse import urlparse

#import vertx

from aplus import Promise
from futile import ObjectProxy
from futile.logging import LoggerMixin
from futile.net.http.exc import NetworkError, HTTPError


def compose_qs(values):
	return "&".join([ "%s=%s" % (quote(k), quote(v)) for k, v in dict(values).iteritems() ])

class LoggingResponseWrapper(LoggerMixin, ObjectProxy):
	def __init__(self, response, *args, **kw):
		super(LoggingResponseWrapper, self).__init__(proxyobject = response, *args, **kw)
		self.__buffer = StringIO()
		self.__finalized = False

	def __exit__(self, exc_type, exc_val, exc_tb):
		self.close()

	def __enter__(self):
		return self

	def read(self, n = None):
		s = self._o.read(n)
		self.__buffer.write(s)
		return s

	def readline(self):
		s = self._o.readline()
		self.__buffer.write(s)
		return s

	def readlines(self, sizehint = None):
		lines = self._o.readlines(sizehint)
		self.__buffer.write(''.join(lines))
		return lines

	def close(self):
		if self.__finalized:
			self.logger.debug("%s is already finalized" % (self, ))
			return

		self.__finalized = True
		try:
			if not self._o.isclosed():
				self.__buffer.write(self._o.read())
			self.logger.debug("Read data:\n %s", self.__buffer.getvalue())
		except:
			self.logger.exception("Finalizing response failed")
		finally:
			self._o.close()

		self.__buffer.close()


class CachingHttplibResponseWrapper(ObjectProxy, LoggerMixin):
	def __init__(self, response, path, tag, last_modified, cache, *args, **kw):
		super(CachingHttplibResponseWrapper, self).__init__(proxyobject = response, *args, **kw)
		self.__cache = cache
		self.__buffer = StringIO()
		self.__path = path
		self.__tag = tag
		self.__last_modified = last_modified
		self.__finalized = False

	def __exit__(self, exc_type, exc_val, exc_tb):
		self.close()

	def __enter__(self):
		return self

	def read(self, n = None):
		s = self._o.read(n)
		self.__buffer.write(s)
		return s

	def readline(self):
		s = self._o.readline()
		self.__buffer.write(s)
		return s

	def readlines(self, sizehint = None):
		lines = self._o.readlines(sizehint)
		self.__buffer.write(''.join(lines))
		return lines

	def close(self):
		if self.__finalized:
			self.logger.debug("%s is already finalized" % (self, ))
			return

		self.__finalized = True
		try:
			if not self._o.isclosed():
				self.__buffer.write(self._o.read())
			val = self.__buffer.getvalue()
			self.logger.debug("Putting to cache: %s -> %s, %s\n %s", self.__path, self.__tag, self.__last_modified, val)
			self.__cache[self.__path] = (self.__tag, self.__last_modified, val)
		except:
			self.logger.exception("Finalizing response failed")
		finally:
			self._o.close()

		self.__buffer.close()

	def __getattr__(self, name):
		return getattr(self._o, name)


class closing(ObjectProxy):
	def __getattr__(self, k):
		return getattr(self._o, k)

	def __enter__(self):
		return self._o

	def __exit__(self, exc_type, exc_val, exc_tb):
		self._o.close()

	def close(self):
		self._o.close()


class RestClient(LoggerMixin):
	ERROR_RESPONSE_MAX = 320

	get_timeout = timeout = 120.0

	def __init__(self, uri, username=None, password=None, certfile=None,
				 keyfile=None, content_type="text/plain", headers=None,
				 cache=True, timeout=None, get_timeout=None,
				 component_name = "server", connection_manager = None,
				 *args, **kw):
		super(RestClient, self).__init__(*args, **kw)

		self.logger.debug("Creating RestClient for %s", uri)

		self.timeout = timeout or self.timeout
		self.get_timeout = get_timeout or timeout or self.get_timeout

		if cache:
			if cache is True:
				from futile.caching import LRUCache
				cache = LRUCache()
			self.__cache = cache

		if "://" not in uri:
			uri = "http://" + uri

		self.__content_type = content_type
		self.component_name = component_name

		info = urlparse(uri)

		if info.scheme == "https":
			if bool(certfile) ^ bool(keyfile):
				raise ValueError("Must give both certfile and keyfile if any")
			if certfile:
				from os.path import exists
				if not exists(certfile):
					raise ValueError("Certificate file not found: %s" % (certfile, ))
				if not exists(keyfile):
					raise ValueError("Key file not found: %s" % (keyfile, ))
		elif info.scheme != "http":
			raise ValueError(info.scheme)

		port = info.port and int(info.port) or getservbyname(info.scheme)

		self.__base = info.path or ""
		#if not self.__base.endswith("/"):
		#	self.__base += "/"

		if not username:
			username = info.username

		if not headers:
			headers = {}

		headers.setdefault("Accept", "*/*")
		headers["Accept-Encoding"] = "identity"

		if username:
			password = password or info.password or ""
			headers["Authorization"] = "Basic " + b64encode("%s:%s" % (username, password))

		self.__headers = headers

		#if not connection_manager:
		#	#from SimpleConnectionManager import SimpleConnectionManager as connection_manager
		#	from ConnectionPoolManager import ConnectionPoolManager as connection_manager
		#
		# self.__connection_manager = connection_manager(host = info.hostname, port = port,
		#				certfile = certfile, keyfile = keyfile, force_ssl = info.scheme == "https")
		#

		self.client= vertx.create_http_client()
		self.client.host = info.netloc.split(":")[0]
		self.client.port = port

		#temporary test server
		#import json
		#self.srv = vertx.create_http_server()
		#def srv_handle(re):
		#	re.response.put_header("Content-Type","application/json; charset=utf-8")
		#	re.response.put_header("Location","locationlocation.location")
	#	re.response.end(json.dumps({"One":"Two"}))
		#self.srv.request_handler(srv_handle)
		#self.srv.listen(5000)

	def request(self, method, path, data = None, headers = {}, args = None):
		if isinstance(data, unicode):
			data = data.encode("utf-8")
		fullpath = self.__base + path
		request_headers = self.__headers.copy()

		if args:
			fullpath += ("?" in fullpath and "&" or "?") + compose_qs(args)

		if headers:
			request_headers.update(headers)

		if method == "GET":
			timeout = self.get_timeout
			try:
				etag, modified, cached = self.__cache[fullpath]
				if etag:
					request_headers["If-None-Match"] = etag
				request_headers["If-Modified-Since"] = modified
			except KeyError:
				request_headers.pop("If-None-Match", None)
				request_headers.pop("If-Modified-Since", None)
		else:
			timeout = self.timeout
			request_headers.setdefault("Content-Type", self.__content_type)

		log_headers = request_headers
		if self.logger.isEnabledFor(DEBUG) and "Authorization" in request_headers:
			log_headers = request_headers.copy()
			log_headers["Authorization"] = "<purged>"

		if method == "GET":
			self.logger.debug("%s: %s (%s)", method, fullpath, log_headers)
		else:
			self.logger.debug("%s: %s (%s)\n%s", method, fullpath, log_headers, repr(data))

		#t = time()
		promise=Promise()
		try:
			#response = self.__connection_manager.request(method, fullpath, data, request_headers, timeout)

			def response_handler(resp):
				if resp.status_code == 304:
					try:
						promise.fulfill(closing(StringIO(cached)))
					except NameError:
						promise.reject(NetworkError("Error: The %s returned 304 though no cached version is available. Request was: %s %s" % (self.component_name, method, fullpath)))
				if resp.status_code < 200 or resp.status_code >= 300:
					try:
						promise.reject(HTTPError(msg = resp.status_message, status = resp.status_code))
					except:
						promise.reject(HTTPError(msg = "Http error", status = response.status))
				else:
					promise.fulfill(resp)

			req=self.client.request(method,fullpath,response_handler)
			for head,value in request_headers.items():
				req.put_header(head,value)
			if data:
				req.chunked = True
				req.write_str(data)
			req.end()

		except Exception as e:
			print "Exception triggered: %s"%e
			promise.reject(e)

		return promise

		#if method == "DELETE":
		#	try:
		#		self.__cache.pop(fullpath, None)
		#	except AttributeError:
		#		pass
		#else:
		#	etag = response.getheader("Etag")
		#	modified = response.getheader("Last-Modified")
		#	if etag or modified:
		#		if not modified:
		#			modified = datetime.utcnow().strftime("%a, %d %b %Y %X GMT")
		#		response = CachingHttplibResponseWrapper(response, fullpath, etag, modified, self.__cache)
		#	elif self.logger.isEnabledFor(DEBUG):
		#		response = LoggingResponseWrapper(response)




	def get(self, path, headers = None, args = None):
		p = self.request("GET", path, headers = headers, args = args)
		return p

	def post(self, path, data, headers = None):
		p = self.request("POST", path, data, headers)
		return p
	add = post

	def put(self, path, data, headers = None):
		p = self.request("PUT", path, data)
		return p
	update = put

	def delete(self, path, headers = None):
		p = self.request("DELETE", path, None, headers)
		return p
