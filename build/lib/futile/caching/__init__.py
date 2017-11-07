'''
Created on 17.07.2011

@author: kca
'''

from ..collections import OrderedDict
import futile

class LRUCache(OrderedDict):
	max_items = 100
	
	def __init__(self, max_items = None, threadsafe = None, *args, **kw):
		super(LRUCache, self).__init__(*args, **kw)
		if max_items is not None:
			if max_items <= 0:
				raise ValueError(max_items)
			self.max_items = max_items
			
		if threadsafe is None:
			threadsafe = futile.THREADSAFE
			
		if threadsafe:
			from threading import RLock
			self.__lock = RLock()
		else:
			self.__lock = None
			self.__getitem__ = self._getitem
			self.__setitem__ = self._setitem
		
	def __getitem__(self, k):
		if self.__lock is None:
			return self._getitem(k)
		with self.__lock:
			return self._getitem(k)
		
	def get(self, k, default = None):
		try:
			return self[k]
		except KeyError:
			return default
		
	def _getitem(self, k):
		v = super(LRUCache, self).__getitem__(k)
		del self[k]
		super(LRUCache, self).__setitem__(k, v)
		return v
	
	def __iter__(self):
		for k in  tuple(super(LRUCache, self).__iter__()):
			yield k
	
	def __setitem__(self, k, v):
		if self.__lock is None:
			return self._setitem(k, v)
		with self.__lock:
			self._setitem(k, v)
		
	def _setitem(self, k, v):
		super(LRUCache, self).__setitem__(k, v)
		if len(self) > self.max_items:
			self.popitem(False)
			