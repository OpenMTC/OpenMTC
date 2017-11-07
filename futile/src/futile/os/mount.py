'''
Created on 24.01.2012

@author: kca
'''

from ..path import Path
from ..subprocess import check_output

def umount(where, force = False):
	cmd = [ "umount", where ]
	if force:
		cmd.append("-f")
	check_output(cmd)
unmount = umount

def mount(what, where, fstype = None, options = None):
	return Mount(what, where, fstype, options).mount()

class Mount(object):
	def __init__(self, what, where, fstype = None, options = None):
		self.what = Path(what)
		self.where = Path(where)
		self.fstype = fstype
		options = self.options = options and set(options) or set()
		if what.isfile():
			options.add("loop")
		elif not what.isblockdev():
			raise ValueError("Mount source must be a file or block device: %s" % (what, ))
		
	def mount(self, fstype = None, options = None):	
		cmd = [ "mount", self.what, self.where ]
		
		fstype = fstype or self.fstype
		if fstype:
			cmd += [ "-t", self.fstype ]
		
		opts = self.options
		if options:
			opts += set(self.options)
		if opts:
			cmd += [ "-o", ','.join(self.options) ]
			
		check_output(cmd)
		return self
	__enter__ = mount
	
	def umount(self, force = False):
		umount(self.where, force)
	unmount = umount
		
	def __exit__(self, exc_type, exc_val, exc_tb):
		self.umount(True)
