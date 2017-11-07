#!/usr/bin/env python

from setuptools import setup
from distutils.core import setup
from glob import glob
import sys
import os

from utils import (get_packages, OpenMTCSdist, OpenMTCBuildPy,
                   OpenMTCBuildPyBinary, OpenMTCSdistBinary,
                   create_openmtc_user, move_config_files, enable_init_files)


# name and version
SETUP_NAME = "openmtc-all"
SETUP_VERSION = "4.99.0"
SETUP_DESCRIPTION = "The OpenMTC Backend and Gateway (GEvent version)"

# meta
SETUP_AUTHOR = "Konrad Campowsky"
SETUP_AUTHOR_EMAIL = "konrad.campowsky@fraunhofer.fokus.de"
SETUP_URL = "http://www.openmtc.org"
SETUP_LICENSE = "Fraunhofer FOKUS proprietary"

# requirements
SETUP_REQUIRES = [
    "urllib3", "gevent (>=1.0)", "iso8601 (>=0.1.5)", "werkzeug (>=0.9)",
    "blist", "simplejson", "ujson", "python_socketio", "gevent_websocket",
    "flask", "pyxb (==1.2.3)", "enum34", "dtls", "geventhttpclient",
    # server only
    "funcy", "netifaces", "decorator", "mimeparse", "coapthon", "rdflib",
    "fyzz", "yapps"
]
SETUP_INSTALL_REQUIRES = [
    "urllib3", "gevent >= 1.0", "iso8601 >= 0.1.5", "werkzeug >= 0.9",
    "blist", "simplejson", "ujson", "python_socketio", "gevent_websocket",
    "flask", "pyxb == 1.2.3", "enum34", "dtls", "geventhttpclient",
    # server only
    "funcy", "netifaces", "decorator", "mimeparse", "coapthon", "rdflib",
    "fyzz", "yapps"
]

# packages
PACKAGES = ["aplus", "openmtc", "openmtc_onem2m", "futile", "openmtc_app",
            "openmtc_gevent", "openmtc_cse", "openmtc_server"]
PACKAGE_DIR = {
    "": "common/openmtc/lib",
    "openmtc": "common/openmtc/src/openmtc",
    "openmtc_onem2m": "common/openmtc-onem2m/src/openmtc_onem2m",
    "futile": "futile/src/futile",
    "openmtc_app": "openmtc-app/src/openmtc_app",
    "openmtc_gevent": "openmtc-gevent/src/openmtc_gevent",
    "openmtc_cse": "server/openmtc-cse/src/openmtc_cse",
    "openmtc_server": "server/openmtc-server/src/openmtc_server"
}
all_packages = []
EXCLUDE = []
for package in PACKAGES:
    all_packages.extend(get_packages(package, PACKAGE_DIR, EXCLUDE))

# scripts
SETUP_SCRIPTS = glob("openmtc-gevent/bin/*")

# package data
PACKAGE_DATA = {}

# data files
DB_DIR = "/var/lib/openmtc"
LOG_DIR = "/var/log/openmtc"
LOG_ROTATE_DIR = "/etc/logrotate.d"
LOG_ROTATE_FILES = ("openmtc-gevent/etc/logrotate.d/openmtc",)
INIT_DIR = "/etc/init.d"
INIT_DIST_FILES = ("openmtc-gevent/etc/init.d/openmtc-gateway",
                   "openmtc-gevent/etc/init.d/openmtc-backend")
CONFIG_FILES = ("config-backend.json", "config-gateway.json")
CONFIG_DIR = "/etc/openmtc/gevent"
CONFIG_DIST_FILES = ("openmtc-gevent/etc/conf/config-backend.json.dist",
                     "openmtc-gevent/etc/conf/config-gateway.json.dist")
SSL_CERT_DIR = "/etc/openmtc/certs"
SSL_CERT_FILES = tuple(map(lambda x: os.path.join('openmtc-gevent/certs/', x),
                           os.listdir('openmtc-gevent/certs')))
DATA_FILES = [
    (DB_DIR, ""),
    (LOG_DIR, ""),
    (LOG_ROTATE_DIR, LOG_ROTATE_FILES),
    (INIT_DIR, INIT_DIST_FILES),
    (CONFIG_DIR, CONFIG_DIST_FILES),
    (SSL_CERT_DIR, SSL_CERT_FILES),
]

# handle binary only
binary_only = "--binary-only" in sys.argv
if binary_only:
    sys.argv.remove("--binary-only")
    CMD_CLASS = {'build_py': OpenMTCBuildPyBinary, 'sdist': OpenMTCSdistBinary}
else:
    CMD_CLASS = {'build_py': OpenMTCBuildPy, 'sdist': OpenMTCSdist}

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

    ############################################################################
    # install
    if "install" in sys.argv:
        # only do this during install
        enable_init_files(INIT_DIR, INIT_DIST_FILES)

        move_config_files(CONFIG_DIR, CONFIG_FILES)

        create_openmtc_user(DB_DIR, LOG_DIR)
