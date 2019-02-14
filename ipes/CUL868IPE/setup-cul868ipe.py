#!/usr/bin/env python3

from setuptools import setup
from distutils.core import setup
from glob import glob
import sys

from utils import get_packages, get_pkg_files, OpenMTCSdist, move_config_files

# name and dir
NAME = "cul868ipe"
BASE_DIR = "."

# import pkg
sys.path.append(BASE_DIR + "/src")
pkg = __import__(NAME)

# setup name and version
SETUP_NAME = "openmtc-" + NAME
SETUP_VERSION = pkg.__version__
SETUP_DESCRIPTION = pkg.__description__

# meta
SETUP_AUTHOR = pkg.__author_name__
SETUP_AUTHOR_EMAIL = pkg.__author_mail__
SETUP_URL = "http://www.openmtc.org"
SETUP_LICENSE = "Fraunhofer FOKUS proprietary"

# requirements
SETUP_REQUIRES = pkg.__requires__
SETUP_INSTALL_REQUIRES = pkg.__requires__

# packages
PACKAGES = [NAME]
PACKAGE_DIR = {"": BASE_DIR + "/src"}
all_packages = []
for package in PACKAGES:
    all_packages.extend(get_packages(package, PACKAGE_DIR))

# scripts
SETUP_SCRIPTS = glob(BASE_DIR + "/bin/*")

# package data
PACKAGE_DATA = {NAME: get_pkg_files(BASE_DIR, NAME)}

# data files
CONFIG_FILES = ("config.json",)
CONFIG_DIR = "/etc/openmtc/" + NAME
CONFIG_DIST_FILES = (BASE_DIR + "/etc/conf/config.json.dist",)
DATA_FILES = [(CONFIG_DIR, CONFIG_DIST_FILES)]

# cmd class
CMD_CLASS = {'sdist': OpenMTCSdist}

if __name__ == "__main__":
    if 'bdist_wheel' in sys.argv:
        raise RuntimeError("This setup.py does not support wheels")

    ############################################################################
    # setup
    setup(name=SETUP_NAME,
          version=SETUP_VERSION,
          description=SETUP_DESCRIPTION,
          author=SETUP_AUTHOR,
          author_email=SETUP_AUTHOR_EMAIL,
          url=SETUP_URL,
          license=SETUP_LICENSE,
          requires=SETUP_REQUIRES,
          install_requires=SETUP_INSTALL_REQUIRES,
          package_dir=PACKAGE_DIR,
          packages=all_packages,
          scripts=SETUP_SCRIPTS,
          package_data=PACKAGE_DATA,
          data_files=DATA_FILES,
          cmdclass=CMD_CLASS
          )

    ############################################################################
    # install
    if "install" in sys.argv:
        # only do this during install
        move_config_files(CONFIG_DIR, CONFIG_FILES)
