'''
Created on 23.07.2011

@author: kca
'''
from futile import Base
from futile.logging import LoggerMixin

class SingletonType(type, LoggerMixin):
	__instances = {}
	
	def get_instance(self):
		try:
			i = self.__instances[self]
			self.logger.debug("Reusing singleton instance for %s.%s" % (self.__module__, self.__name__))
		except KeyError:
			self.logger.debug("Creating singleton instance for %s.%s" % (self.__module__, self.__name__))
			i = super(SingletonType, self).__call__()
			self.__instances[self] = i
		return i
	
class ForcedSingletonType(SingletonType):
	def __call__(self, *args, **kw):
		return self.get_instance()
	
class Singleton(Base):
	__metaclass__ = SingletonType
	
class ForcedSingleton(Base):
	__metaclass__ = ForcedSingletonType