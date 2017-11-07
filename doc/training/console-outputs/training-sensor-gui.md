```sh
user@host:/git$ ./openmtc-open-source/doc/training/start-app.sh
[1] onem2m-ipe-sensors-final.py
[2] onem2m-ipe-sensors-actuators-final.py
[3] onem2m-gui-sensors-final.py
[4] onem2m-gui-sensors-actuators-final.py
Choose the app to start: 3
PYTHONPATH: :/git/openmtc-open-source/doc/../futile/src:/git/openmtc-open-source/doc/../common/openmtc/lib:/git/openmtc-open-source/doc/../common/openmtc-onem2m/src:/git/openmtc-open-source/doc/../common/openmtc/src:/git/openmtc-open-source/doc/../serializers/*/src:/git/openmtc-open-source/doc/../openmtc-app/src
Subscribing to Resource: /mn-cse-1/onem2m/TestIPE/devices/Temp-2/measurements
Subscribing to Resource: /mn-cse-1/onem2m/TestIPE/devices/Humi-2/measurements
Subscribing to Resource: /mn-cse-1/onem2m/TestIPE/devices/Humi-1/measurements
Subscribing to Resource: /mn-cse-1/onem2m/TestIPE/devices/Temp-1/measurements
127.0.0.1 - - [2017-07-27 12:09:34] "POST / HTTP/1.1" 200 160 0.008250
handle measurements..
container: /mn-cse-1/onem2m/TestIPE/devices/Temp-1/measurements
data: {u'type': u'temperature', u'value': 28, u'unit': u'degreeC'}

127.0.0.1 - - [2017-07-27 12:09:36] "POST / HTTP/1.1" 200 160 0.045183
handle measurements..
container: /mn-cse-1/onem2m/TestIPE/devices/Humi-2/measurements
data: {u'type': u'humidity', u'value': 55, u'unit': u'percentage'}

127.0.0.1 - - [2017-07-27 12:09:37] "POST / HTTP/1.1" 200 160 0.044600
handle measurements..
container: /mn-cse-1/onem2m/TestIPE/devices/Temp-1/measurements
data: {u'type': u'temperature', u'value': 25, u'unit': u'degreeC'}

127.0.0.1 - - [2017-07-27 12:09:38] "POST / HTTP/1.1" 200 160 0.043332
handle measurements..
container: /mn-cse-1/onem2m/TestIPE/devices/Humi-1/measurements
data: {u'type': u'humidity', u'value': 66, u'unit': u'percentage'}

127.0.0.1 - - [2017-07-27 12:09:40] "POST / HTTP/1.1" 200 160 0.044541
handle measurements..
container: /mn-cse-1/onem2m/TestIPE/devices/Humi-2/measurements
data: {u'type': u'humidity', u'value': 60, u'unit': u'percentage'}

127.0.0.1 - - [2017-07-27 12:09:41] "POST / HTTP/1.1" 200 160 0.047174
handle measurements..
container: /mn-cse-1/onem2m/TestIPE/devices/Humi-1/measurements
data: {u'type': u'humidity', u'value': 34, u'unit': u'percentage'}
```
