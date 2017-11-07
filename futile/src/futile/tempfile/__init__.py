from tempfile import mkdtemp as _mkdtemp
from shutil import rmtree
from .. import Base
from futile import noop

class TempDir(Base):
	delete_on_error = delete = True
	
	def __init__(self, suffix='', prefix='tmp', dir=None, delete = None, delete_on_error = None, *args, **kw):
		super(TempDir, self).__init__(*args, **kw)
		self.__name = _mkdtemp(suffix, prefix, dir)
		if delete is not None:
			self.delete = delete
		if delete_on_error is not None:
			self.delete_on_error = delete_on_error 

	@property
	def name(self):
		return self.__name

	def rmtree(self):
		rmtree(self.__name)
		self.rmtree = noop
		
	def __enter__(self):
		return self
	
	def __exit__(self, exc_type, exc_val, exc_tb):
		if self.delete or (exc_type and self.delete_on_error):
			self.rmtree()
			
	def __del__(self):
		self.__exit__(None, None, None)
		
	def __str__(self):
		return self.__name
	
mkdtemp = TempDir
