# Installation of the OpenMTC SDK


## Requirements

* Python (only version 2.7 is supported)  
  
**Note**: Only the *CPython* implementation (the default interpreter) of Python has been tested. *PyPy* might work as well, possibly with some minor adjustments. *Jython* is known not to work since it lacks support for compiled extensions.
  
In order to install the `gevent` package, development headers for both python and libev as well as a C-Compiler and associated toolchain might be required. To install these along with the pip tool the following commands might be used:

Debian based systems (including Ubuntu):

``` sh
$ sudo apt-get install python-pip libev-dev python-dev gcc make automake
```

Redhat based systems (including Fedora, Centos):

``` sh
$ sudo yum install python-pip libev-devel python-devel gcc make automake
```

Additionally, some required Python packages need to be installed. The following command line should suffice to install the required packages:

``` sh
$ pip2 install --user --requirement openmtc-open-source/openmtc-gevent/dependencies.txt
```

## Installing

To install the OpenMTC SDK itself the following steps need to be performed:

Change to the SDK's distribution directory:

``` sh
$ cd openmtc-open-source
```

Run the installer command:

``` sh
$ sudo python setup-sdk.py install
```

## Testing the Installation

The following command can be used to test if the OpenMTC SDK has been correctly installed:

``` sh
$ python2 -c "import openmtc; import openmtc_app"
```

If the SDK has been installed correctly, this command will exit successfully (exit code `0`) and not produce any output.
