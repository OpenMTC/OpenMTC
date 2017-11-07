# Create App Structure Script

This documentation explains the `create-app-structure` script in the main folder
and shows the usage.

It follows the conventions for Apps and IPEs from the `openmtc-guidelines.md`.
It will create a complex app or an IPE based on the input. It will create a
basic set of folders and files. These will be the app structure, the setup
script and the needed docker files in order to run directly the
`create-binary-docker` script.

## Usage

The script shall be called from the command line:

```bash
./create-app-structure 

Usage: $0 [-w] [-d] [-i] [-a <APP_SCRIPT>] APP_NAME

    APP_NAME            Name of the app, used as folder and class name.

    -a <APP_SCRIPT>     If not provided, it will be created automatically by
                        converting the APP_NAME from camel case to snake case.

                        If APP_NAME or APP_SCRIPT ends with IPE or similar, it
                        will be assumed as IPE and will be created under ipes.

    -w                  if true, FlaskRunner is used and basic index.html is
                        created

    -i                  if true, IN-AE is expected and default endpoint is
                        configured to backend

    -d                  if true, no setup file and docker files will be created
```

The first parameter is mandatory and shall be the name of the App in Camel Case.
From the name the script checks if the app shall be an IPE. Examples for apps
are "TestApp", "RobotControlLoop" and "ROSGUI". IPEs can be named like
"ZigBeeIPE" or "CUL868IPE". If names are not easy to guess the snake case form
the second parameter can be used.

### Examples

To create the structure for ZigBeeIPE:

```bash
./create-app-structure ZigBeeIPE
```

This will create the folder `ipes/ZigBeeIPE`, the package `zigbeeipe`, the
module name `zig_bee_ipe` and the start script `zig-bee-ipe`.

To create the structure for ROSGUI:

```bash
./create-app-structure -a ros-gui ROSGUI
```

This will create the folder `apps/ROSGUI`, the package `rosgui`, the module name
`ros_gui` and the start script `ros-gui`.

## Result

The script will produce a bunch of files. For the example `TestApp` it would
create the folder `apps/TestApp` and the script `apps/test-app`.

The folder `apps/TestApp` looks like the following:

```
apps
+-- ComplexApp
|   +-- bin
|   |   +-- openmtc-test-app
|   +-- docker
|   |   +-- configure-testapp-and-start
|   |   +-- testapp-amd64
|   |   +-- testapp-arm
|   +-- etc
|   |   +-- conf
|   |       +-- config.json.dist
|   |   +-- systemd
|   |       +-- system
|   |           +-- openmtc-testapp.service
|   +-- MANIFEST.in
|   +-- setup-testapp.py
|   +-- src
|       +-- complexapp
|           +-- __init__.py
|           +-- __main__.py
|           +-- complex_app.py
|   +-- utils.py
+ test-app
```

The setup script can be used to create a python install package that can be
installed on another machine. The docker files are needed to create a docker
image with the help of the `create-binary-docker` script. See extra
documentation for this.

## Development Options

There are two possibilities to use this script.

1. Start from simple app
2. Start with this script

### Start from simple app

When you want to start with a simple app, you can copy an app from
`doc/training/apps` and name it that it ends with `-final.py`. Then you can
use the script located at `doc/training/start-app.sh` to start your simple app.

When you are satisfied with the functionality, you can use the
`create-app-structure` script in order to create the structure and the files.
After the creation of the files you can copy the code of your simple app into
the main modules. For the example of `TestApp`, you would integrate the parts
below
```python
if __name__ == '__main__':
    from openmtc_app.runner import AppRunner as Runner
```
into `apps/TestApp/src/testapp/__main__.py` and the rest into
`apps/TestApp/src/testapp/test_app.py`.

Check [later chapter](#files-to-work-on) to see which files need to be
adjusted.

### Start with script

When you start from scratch, you run the script in order to create the
structure. Then you can start developing. For the example of `TestApp`, you
start with `apps/TestApp/src/testapp/test_app.py`.

Check [later chapter](#files-to-work-on) to see which files can be changed, if
needed.

### Files to work on

The script will create the structure. Some files need some changes, other files
can be changed, if necessary.

#### `apps/TestApp/src/testapp/__init__.py`

```python
"""
TODO: Add description here
"""

__version__ = "ADD-VERSION-HERE"
__description__ = "TestApp"
__author_name__ = "ADD_AUTHOR_HERE"
__author_mail__ = "ADD_MAIL_HERE"
__requires__ = []
```

* These entries will be used in the `setup-testapp.py` script to build the
python package.
* All values are self-explanatory.
* `__requires__` can be used, if other python libs are needed.

#### `apps/TestApp/src/testapp/test_app.py`

```python
from openmtc_app.onem2m import XAE


class TestApp(XAE):
    interval = 10

    def _on_register(self):
        # start endless loop
        self.run_forever(self.interval)
```

* This file contains the start of the program logic.
* More modules can be added.
* TestApp can be extended with additional parameters:

```python
class TestApp(XAE):

    def __init__(self, additional_parameter, *kw, **args):
        super(TestApp, self).__init__(*kw, **args)
        self._additional_parameter = additional_parameter
```

* To add `*kw, **args` makes it easier to add the parameter as well in the
config as also in the `__main__` module. See other files.

#### `apps/TestApp/config.json`

```json
{
    "name": "TestApp",
    "ep": "http://localhost:8000",
    "cse_base": "onem2m",
    "poas": [
        "http://auto:29260"
    ],
    "originator_pre": "//openmtc.org/mn-cse-1",
    "ssl_certs": {
        "cert_file": null,
        "key_file": null,
        "ca_certs": null
    },
    "logging": {
        "level": "ERROR",
        "file": null
    }
}
```

* Most of the parameters are quite fine. But can be changed:
  * `name` is the name how the AE/IPE is registering itself.
  * `ep` is the endpoint of the AE. Needs to be a Gateway or a backend.
  * `cse_base` is the path to the `CSE-BASE` of the endpoint.
  * `poas` is used in order to receive notifications. `http:` and `mqtt:` are
  supported.
  * `originator_pre` needs to be set, if SSL certificates are used. Needs to
  match the CSE where the AE shall be register to.
  * `ssl_certs` has to be set to the locations of the required certificate
  files.
  * `logging` can be used to change the log level and also to set a file to log
  to.
* To add additional parameters, just add the parameter into the JSON.
* In order to use docker, all changes have to be made as well in
`apps/TestApp/etc/conf/config.json.dist`.

#### `apps/TestApp/src/testapp/__main__.py`

```python
from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser

from openmtc_app.util import prepare_app, get_value
from openmtc_app.runner import AppRunner as Runner
from .test_app import TestApp

# defaults
default_name = "TestApp"
default_ep = "http://localhost:8000"

# args parser
parser = ArgumentParser(
    description="An IPE called TestApp",
    prog="TestApp",
    formatter_class=ArgumentDefaultsHelpFormatter)
parser.add_argument("-n", "--name", help="Name used for the AE.")
parser.add_argument("-s", "--ep", help="URL of the local Endpoint.")

# args, config and logging
args, config = prepare_app(parser, __loader__, __name__, "config.json")

# variables
nm = get_value("name", (unicode, str), default_name, args, config)
cb = config.get("cse_base", "onem2m")
ep = get_value("ep", (unicode, str), default_ep, args, config)
poas = config.get("poas", ["http://auto:29260"])
originator_pre = config.get("originator_pre", "//openmtc.org/mn-cse-1")
ssl_certs = config.get("ssl_certs", {})

# start
app = TestApp(
    name=nm, cse_base=cb, poas=poas,
    originator_pre=originator_pre, **ssl_certs
)
Runner(app).run(ep)

print ("Exiting....")
```

* The module is ready for starting the app itself.
* When `test_app.py` was extended with an additional parameter and it was added
to the config, the init of the App needs to be changed:
```python
ssl_certs = config.get("ssl_certs", {})
additional_parameter = config.get("additional_parameter", None)

# start
app = TestApp(
    additional_parameter=additional_parameter,
    name=nm, cse_base=cb, poas=poas,
    originator_pre=originator_pre, **ssl_certs
)
Runner(app).run(ep)
```
