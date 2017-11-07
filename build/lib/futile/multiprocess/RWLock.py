'''
Created on 30.04.2011

@author: kca
'''

import os
from fcntl import lockf, LOCK_EX, LOCK_SH, LOCK_UN
from contextlib import contextmanager
from futile.signal import timeout

class RWLock(object):
	def __init__(self, path = None, threadsafe = True, *args, **kw):
		if not path:
			raise NotImplementedError()
		
		if not os.path.exists(path):
			open(path, "a").close()
			
		self.__path = path
		
		if threadsafe:
			import threading
			self.__local = threading.local()
		else:
			class Local(object):
				pass
			self.__local = Local
			
		self.__local.f = None
			
			
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
	
	def __acquire(self, fmode, lmode, to):
		assert getattr(self.__local, "f", None) is None
		f = open(self.__path, fmode)
		try:
			if timeout:
				with timeout(to):
					lockf(f, lmode)
			else:
				lockf(f, lmode)
		except:
			f.close()
			raise
		self.__local.f = f
		return f

	def read_acquire(self, timeout = None):
		return self.__acquire("r", LOCK_SH, timeout)
	
	def read_release(self):
		with self.__local.f as f:
			self.__local.f = None
			lockf(f, LOCK_UN)

	write_release = read_release
	
	def write_acquire(self, timeout = None):
		return self.__acquire("a", LOCK_EX, timeout)
	
	__enter__ = write_acquire
	
	def __exit__(self, *args):
		self.write_release()
