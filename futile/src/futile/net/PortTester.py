'''
Created on 15.07.2011

@author: kca
'''

from asyncore import dispatcher, loop
from socket import AF_INET, SOCK_STREAM, error
from sockethelper import socket
from futile.exc import errorstr
from collections import namedtuple
import sys
from time import time

class TestResult(namedtuple("TestResultTuple", ("result", "message"))):
	def __new__(cls, result, message = ""):
		return super(TestResult, cls).__new__(cls, result, message)
		
	def __bool__(self):
		return self.result
	__nonzero__ = __bool__
	
	def __str__(self):
		if self.message:
			return "%s - %s" % (self.result, self.message)
		return str(self.result)
	
	def __eq__(self, o):
		try:
			return self.result == o.result
		except AttributeError:
			return False
		
	def __ne__(self, o):
		return not (self == o)

def test_port(host, port, family = AF_INET, type = SOCK_STREAM):
	try:
		with socket(family, type) as s:
			s.connect((host, port))
	except error, e:
		return TestResult(False, "%s (%d)" % (e.strerror, e.errno))
	except Exception, e:
		return TestResult(False, errorstr(e))
	return TestResult(True)

class PortTester(dispatcher):
	result = TestResult(False, "Test did not run")
	
	def __init__(self, host, port, family = AF_INET, type = SOCK_STREAM, map = None):
		dispatcher.__init__(self, map = map)
		self.create_socket(family, type)
		self.connect((host, port))
		self.host = host
		self.port = port

	def handle_connect(self):
		self.result = TestResult(True)
		self.close()

	def handle_error(self):
		self.result = TestResult(False, errorstr(sys.exc_value))
		self.close()
	
def run_test(map, timeout = 0.0):
	if timeout and timeout > 0.0:
		timeout = float(timeout)
		start = time()
		while True:
			loop(map = map, timeout = timeout, count = 1)
			if map:
				now = time()
				timeout -= now - start
				if timeout <= 0.0:
					for r in map.itervalues():
						r.result = TestResult(False, "Timeout")
					break
				start = now
			else:
				break
	else:
		loop(map = map)
			