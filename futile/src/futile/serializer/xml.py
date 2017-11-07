'''
Created on 28.08.2011

@author: kca
'''

from ..logging import LoggerMixin
from logging import DEBUG
from ..etree.impl import ElementTree, XML, ParseError as XMLParseError, XMLSyntaxError, tostring
from abc import ABCMeta, abstractmethod
from futile.serializer.exc import ParseError

class AbstractXMLSerializer(LoggerMixin):
	__metaclass__ = ABCMeta
	
	def load(self, input):		
		if self.logger.isEnabledFor(DEBUG):
			from cStringIO import StringIO
			input = input.read()
			self.logger.debug("Parsing input: %s", input)
			input = StringIO(input)
		root = self._load(input)
		return self._parse_input(root)
	
	def _load(self, input):
		try:
			if isinstance(input, str):
				return XML(input)
			else:	
				return ElementTree().parse(input)
		except Exception, e:
			self._handle_parse_error(e)
			raise ParseError(e)
		
	def _handle_parse_error(self, e):
		self.logger.exception("Error parsing input: %s", e)
			
	@abstractmethod
	def _parse_input(self, root):
		raise NotImplementedError()
	
	def dump(self, o, pretty_print = True):
		raise NotImplementedError()
	
	def dumps(self, o, pretty_print = True):
		xml = self._dump_object(o)
		return tostring(xml, pretty_print = pretty_print)
	
	@abstractmethod
	def _dump_object(self, o):
		raise NotImplementedError()
