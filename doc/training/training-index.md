# Write your first OpenMTC applications


## Introduction
OpenMTC is delivered with some incremental demo applications which can be consulted for further understanding or as template for other applications. The oneM2M demo applications can be found in the [OpenMTC Repository on Github](https://github.com/OpenMTC/OpenMTC/tree/master/doc/training/apps/onem2m).

The training is subdivided into examples for GUI-applications and IPE-applications. Both of these provide incremental demo applications for either sensor-actuator-applications or only sensor-applications. These are explained in the following sections.


## The start-app Script

The [training folder](https://github.com/OpenMTC/OpenMTC/tree/master/doc/training) contains the [start-app.sh](https://github.com/OpenMTC/OpenMTC/blob/master/doc/training/start-app.sh) script. This script allows to run one of the four complete demo applications:

```sh
user@host:/git$ ./openmtc-open-source/doc/training/start-app.sh
[1] onem2m-ipe-sensors-final.py
[2] onem2m-ipe-sensors-actuators-final.py
[3] onem2m-gui-sensors-final.py
[4] onem2m-gui-sensors-actuators-final.py
Choose the app to start:
```

## Getting started

First of all, OpenMTC needs to be install on your system. If you have not yet installed OpenMTC, please do so following these [instructions](../install-sdk.md).

### Sensor only demo applications

To run the sensor only demo application, you will need four consoles. Proceed in the following order, since both the IPE and the GUI require a running CSE.

**Console 1:** Backend
* start the Backend by executing the following:
* `./openmtc-open-source/openmtc-gevent/run_backend`
* After you started all four consoles, you should get something like [this](console-outputs/training-sensor-backend.md).

**Console 2:** Gateway
* start the Gateway by executing the following:
* `./openmtc-open-source/openmtc-gevent/run_gateway`
* After you started all four consoles, you should get something like [this](console-outputs/training-sensor-gateway.md).

**Console 3:** IPE
* start the IPE by executing the following:
* `./openmtc-open-source/doc/training/start-app.sh`
* type `1`
* you should get something like [this](console-outputs/training-sensor-ipe.md).

**Console 4:** GUI
* start the GUI by executing the following:
* `./openmtc-open-source/doc/training/start-app.sh`
* type `3`
* you should get something like [this](console-outputs/training-sensor-gui.md).


### Sensor-Actuator demo applications

To run the sensor-actuator demo application, you will also need four consoles. Proceed in the following order, since both the IPE and the GUI require a running CSE.

**Console 1:** Backend
* start the Backend by executing the following:
* `./openmtc-open-source/openmtc-gevent/run_backend`
* After you started all four consoles, you should get something like [this](console-outputs/training-sensor-actuator-backend.md).

**Console 2:** Gateway
* start the Gateway by executing the following:
* `./openmtc-open-source/openmtc-gevent/run_gateway`
* After you started all four consoles, you should get something like [this](console-outputs/training-sensor-actuator-gateway.md).

**Console 3:** IPE
* start the IPE by executing the following:
* `./openmtc-open-source/doc/training/start-app.sh`
* type `2`
* you should get something like [this](console-outputs/training-sensor-actuator-ipe.md).

**Console 4:** GUI
* start the GUI by executing the following:
* `./openmtc-open-source/doc/training/start-app.sh`
* type `4`
* you should get something like [this](console-outputs/training-sensor-actuator-gui.md).


## IPE demo applications

IPE stands for Interworking Proxy Application Entity. The IPE demo applications attaches (virtual) sensors and (virtual) actuators to the CSE by sending (simulated) sensors readings and receiving and processing commands meant for (virtual) actuators attached to the hardware this IPE demo app is running on.

The [IPE demo applications](https://github.com/OpenMTC/OpenMTC/tree/master/doc/training/apps/onem2m/ipe) are available as sensor-actuator-applications or only as sensor-applications.

**Incremental IPE demo applications**
* [ipe-sensors](training-ipe-sensors.md) provides virtual sensors
* [ipe-sensors-actuators](training-ipe-sensors-actuators.md) provides virtual sensors and actuators


## GUI demo applications

GUI stands for Graphical User Interface. This is somewhat misleading, as these demo apps do not provide a real GUI. These GUI demo applications rather provide a textual user interface which receives (and eventually displays to the user) the (virtual) sensor data provided by the ipe-demo-apps. Further, they send commands to the (virtual) actuators attached to the ipe-demo-apps.

The [GUI demo applications](https://github.com/OpenMTC/OpenMTC/tree/master/doc/training/apps/onem2m/gui) are available as sensor-actuator-applications or only as sensor-applications.

**Incremental GUI demo applications**
* [GUI-sensors](training-gui-sensors.md) receives and displays sensor data
* [GUI-sensors-actuators](training-gui-sensors-actuators.md) receives and displays sensor data and issues commands to actuators
