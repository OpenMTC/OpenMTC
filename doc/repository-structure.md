# OpenMTC Code Repository Structure

The following provides a description of the structure of the OpenMTC
code repository.

```
openmtc-open-source
|-- common -> common part used by CSE and AE
    |-- openmtc/lib
    |-- openmtc/src/openmtc
    |-- openmtc-onem2m/src/openmtc_onem2m
|-- doc -> tutorials, docu, example apps
|-- docker -> docker utils for CSE and SDK
|-- futile/src/futile -> needs to be checked if needed (lib of Konrad)
|-- openmtc-app/src/openmtc_app -> app framework (AE)
|-- openmtc-gevent -> start CSE components
    |-- bin, etc -> for packaging (check if needed)
    |-- certs -> for auth (fake cert for out-of-the-box usage?)
    |-- src/openmtc_gevent
    |-- config + scripts -> start scripts for gevent platform (no other probably needed)
|-- server -> CSE components
    |-- openmtc-cse/src/openmtc_cse
    |-- openmtc-server/src/openmtc_server
|-- testing -> testing framework
|-- util
|-- git files
|-- scripts -> create-binary-docker
|-- setup files -> CSE, SDK
```
