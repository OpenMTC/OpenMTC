#!/usr/bin/env python

from setuptools import setup
from distutils.core import setup
from utils import get_packages, OpenMTCSdist

# name and version
NAME = "sdk"
SETUP_NAME = "openmtc-" + NAME
SETUP_VERSION = "4.99.0"
SETUP_DESCRIPTION = "The OpenMTC Python SDK"

# meta
SETUP_AUTHOR = "Konrad Campowsky"
SETUP_AUTHOR_EMAIL = "konrad.campowsky@fraunhofer.fokus.de"
SETUP_URL = "http://www.openmtc.org"
SETUP_LICENSE = "Fraunhofer FOKUS proprietary"

# requirements
SETUP_REQUIRES = [
    "urllib3", "gevent (>=1.0)", "iso8601 (>=0.1.5)", "werkzeug (>=0.9)",
    "blist", "simplejson", "ujson", "python_socketio", "gevent_websocket",
    "flask", "pyxb (==1.2.3)", "enum34", "dtls", "geventhttpclient"
]
SETUP_INSTALL_REQUIRES = [
    "urllib3", "gevent >= 1.0", "iso8601 >= 0.1.5", "werkzeug >= 0.9",
    "blist", "simplejson", "ujson", "python_socketio", "gevent_websocket",
    "flask", "pyxb == 1.2.3", "enum34", "dtls", "geventhttpclient"
]

# packages
PACKAGES = ["aplus", "openmtc", "openmtc_onem2m", "futile", "openmtc_app"]
PACKAGE_DIR = {
    "": "common/openmtc/lib",
    "openmtc": "common/openmtc/src/openmtc",
    "openmtc_onem2m": "common/openmtc-onem2m/src/openmtc_onem2m",
    "openmtc_app": "openmtc-app/src/openmtc_app",
    "futile": "futile/src/futile"
}
all_packages = []
for package in PACKAGES:
    all_packages.extend(get_packages(package, PACKAGE_DIR))

# scripts
SETUP_SCRIPTS = []

# package data
PACKAGE_DATA = {NAME: []}

# data files
DATA_FILES = []

# cmd class
CMD_CLASS = {'sdist': OpenMTCSdist}

if __name__ == "__main__":
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
          cmdclass=CMD_CLASS,
          py_modules=["pyio"]
          )
