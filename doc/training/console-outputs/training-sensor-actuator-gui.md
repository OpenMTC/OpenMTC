```sh
user@host:/git$ ./openmtc-open-source/doc/training/start-app.sh
[1] onem2m-ipe-sensors-final.py
[2] onem2m-ipe-sensors-actuators-final.py
[3] onem2m-gui-sensors-final.py
[4] onem2m-gui-sensors-actuators-final.py
Choose the app to start: 4
PYTHONPATH: :/git/openmtc-open-source/doc/../futile/src:/git/openmtc-open-source/doc/../common/openmtc/lib:/git/openmtc-open-source/doc/../common/openmtc-onem2m/src:/git/openmtc-open-source/doc/../common/openmtc/src:/git/openmtc-open-source/doc/../serializers/*/src:/git/openmtc-open-source/doc/../openmtc-app/src
discovered commands container: /mn-cse-1/onem2m/TestIPE/devices/Switch-Window/commands

discovered commands container: /mn-cse-1/onem2m/TestIPE/devices/Switch-AirCon/commands

Subscribing to Resource: /mn-cse-1/onem2m/TestIPE/devices/Humi-1/measurements
Subscribing to Resource: /mn-cse-1/onem2m/TestIPE/devices/Humi-2/measurements
127.0.0.1 - - [2017-07-27 13:57:07] "POST / HTTP/1.1" 200 160 0.001971
handle_measurements...
container: /mn-cse-1/onem2m/TestIPE/devices/Humi-1/measurements
data: {u'type': u'humidity', u'value': 34, u'unit': u'percentage'}
Humidity = 34 < 65. CLOSE Window

127.0.0.1 - - [2017-07-27 13:57:08] "POST / HTTP/1.1" 200 160 0.045359
handle_measurements...
container: /mn-cse-1/onem2m/TestIPE/devices/Humi-2/measurements
data: {u'type': u'humidity', u'value': 78, u'unit': u'percentage'}
Humidity = 78 >= 65. OPEN Window

Subscribing to Resource: /mn-cse-1/onem2m/TestIPE/devices/Temp-2/measurements
Subscribing to Resource: /mn-cse-1/onem2m/TestIPE/devices/Temp-1/measurements
127.0.0.1 - - [2017-07-27 13:57:13] "POST / HTTP/1.1" 200 160 0.043167
handle_measurements...
container: /mn-cse-1/onem2m/TestIPE/devices/Humi-1/measurements
data: {u'type': u'humidity', u'value': 42, u'unit': u'percentage'}
Humidity = 42 < 65. CLOSE Window

127.0.0.1 - - [2017-07-27 13:57:15] "POST / HTTP/1.1" 200 160 0.041397
handle_measurements...
container: /mn-cse-1/onem2m/TestIPE/devices/Humi-1/measurements
data: {u'type': u'humidity', u'value': 67, u'unit': u'percentage'}
Humidity = 67 >= 65. OPEN Window

127.0.0.1 - - [2017-07-27 13:57:16] "POST / HTTP/1.1" 200 160 0.043280
handle_measurements...
container: /mn-cse-1/onem2m/TestIPE/devices/Temp-2/measurements
data: {u'type': u'temperature', u'value': 27, u'unit': u'degreeC'}
Temperature = 27 >= 22. Turning AirConditioning ON

127.0.0.1 - - [2017-07-27 13:57:18] "POST / HTTP/1.1" 200 160 0.047879
handle_measurements...
container: /mn-cse-1/onem2m/TestIPE/devices/Temp-1/measurements
data: {u'type': u'temperature', u'value': 20, u'unit': u'degreeC'}
Temperature = 20 < 22. Turning AirConditioning OFF

^C127.0.0.1 - - [2017-07-27 13:57:20] "POST / HTTP/1.1" 200 160 0.046181
handle_measurements...
container: /mn-cse-1/onem2m/TestIPE/devices/Temp-1/measurements
data: {u'type': u'temperature', u'value': 23, u'unit': u'degreeC'}
Temperature = 23 >= 22. Turning AirConditioning ON
```
