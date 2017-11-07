```sh
user@host:/git$ ./openmtc-open-source/openmtc-gevent/run_gateway
PYTHONPATH: :/git/openmtc-open-source/openmtc-gevent/../futile/src:/git/openmtc-open-source/openmtc-gevent/../common/openmtc/lib:/git/openmtc-open-source/openmtc-gevent/../common/openmtc-onem2m/src:/git/openmtc-open-source/openmtc-gevent/../common/openmtc/src:/git/openmtc-open-source/openmtc-gevent/../serializers/*/src:/git/openmtc-open-source/openmtc-gevent/../openmtc-app/src
PYTHONPATH: :/git/openmtc-open-source/openmtc-gevent/../futile/src:/git/openmtc-open-source/openmtc-gevent/../common/openmtc/lib:/git/openmtc-open-source/openmtc-gevent/../common/openmtc-onem2m/src:/git/openmtc-open-source/openmtc-gevent/../common/openmtc/src:/git/openmtc-open-source/openmtc-gevent/../serializers/*/src:/git/openmtc-open-source/openmtc-gevent/../openmtc-app/src:/git/openmtc-open-source/openmtc-gevent/src:/git/openmtc-open-source/openmtc-gevent/../server/openmtc-cse/src:/git/openmtc-open-source/openmtc-gevent/../server/openmtc-server/src
DEBUG:openmtc_gevent.main:Reading config file: config-gateway.json
::1 - - [2017-07-27 12:09:24] "POST /onem2m HTTP/1.1" 201 438 0.001517
::1 - - [2017-07-27 12:09:24] "GET /onem2m/TestIPE HTTP/1.1" 200 433 0.000697
::1 - - [2017-07-27 12:09:24] "POST /onem2m/TestIPE HTTP/1.1" 201 471 0.050511
::1 - - [2017-07-27 12:09:24] "POST /onem2m/TestIPE/devices HTTP/1.1" 201 465 0.049690
::1 - - [2017-07-27 12:09:24] "POST /onem2m/TestIPE/devices/Humi-1 HTTP/1.1" 201 488 0.050775
::1 - - [2017-07-27 12:09:24] "POST /onem2m/TestIPE/devices/Humi-1/measurements HTTP/1.1" 201 531 0.047327
::1 - - [2017-07-27 12:09:25] "POST /onem2m/TestIPE/devices HTTP/1.1" 201 465 0.048645
::1 - - [2017-07-27 12:09:26] "POST /onem2m/TestIPE/devices/Humi-2 HTTP/1.1" 201 488 0.042868
::1 - - [2017-07-27 12:09:26] "POST /onem2m/TestIPE/devices/Humi-2/measurements HTTP/1.1" 201 531 0.044007
::1 - - [2017-07-27 12:09:29] "POST /onem2m/TestIPE/devices HTTP/1.1" 201 465 0.046697
::1 - - [2017-07-27 12:09:29] "POST /onem2m/TestIPE/devices/Temp-2 HTTP/1.1" 201 491 0.045791
::1 - - [2017-07-27 12:09:29] "POST /onem2m/TestIPE/devices/Temp-2/measurements HTTP/1.1" 201 531 0.047106
::1 - - [2017-07-27 12:09:31] "POST /onem2m/TestIPE/devices HTTP/1.1" 201 465 0.049131
::1 - - [2017-07-27 12:09:31] "POST /onem2m/TestIPE/devices/Temp-1 HTTP/1.1" 201 491 0.047133
::1 - - [2017-07-27 12:09:31] "POST /onem2m/TestIPE/devices/Temp-1/measurements HTTP/1.1" 201 531 0.046603
::1 - - [2017-07-27 12:09:32] "POST /onem2m/TestIPE/devices/Temp-2/measurements HTTP/1.1" 201 531 0.043829
::1 - - [2017-07-27 12:09:33] "POST /onem2m/TestIPE/devices/Temp-1/measurements HTTP/1.1" 201 531 0.046445
::1 - - [2017-07-27 12:09:33] "GET /~/mn-cse-1/onem2m?lbl=measurements&fu=1 HTTP/1.1" 200 403 0.002203
::1 - - [2017-07-27 12:09:33] "GET /~/mn-cse-1/onem2m/TestIPE/devices/Temp-2/measurements HTTP/1.1" 200 675 0.000822
::1 - - [2017-07-27 12:09:33] "POST /~/mn-cse-1/onem2m/TestIPE/devices/Temp-2/measurements HTTP/1.1" 201 507 0.050772
::1 - - [2017-07-27 12:09:33] "GET /~/mn-cse-1/onem2m/TestIPE/devices/Humi-2/measurements HTTP/1.1" 200 598 0.005506
::1 - - [2017-07-27 12:09:33] "POST /~/mn-cse-1/onem2m/TestIPE/devices/Humi-2/measurements HTTP/1.1" 201 507 0.047209
::1 - - [2017-07-27 12:09:33] "GET /~/mn-cse-1/onem2m/TestIPE/devices/Humi-1/measurements HTTP/1.1" 200 598 0.004212
::1 - - [2017-07-27 12:09:34] "POST /~/mn-cse-1/onem2m/TestIPE/devices/Humi-1/measurements HTTP/1.1" 201 507 0.049078
::1 - - [2017-07-27 12:09:34] "GET /~/mn-cse-1/onem2m/TestIPE/devices/Temp-1/measurements HTTP/1.1" 200 675 0.005679
::1 - - [2017-07-27 12:09:34] "POST /~/mn-cse-1/onem2m/TestIPE/devices/Temp-1/measurements HTTP/1.1" 201 507 0.048767
::1 - - [2017-07-27 12:09:34] "POST /onem2m/TestIPE/devices/Temp-1/measurements HTTP/1.1" 201 531 0.048999
::1 - - [2017-07-27 12:09:35] "GET /~/mn-cse-1/onem2m?cra=2017-07-27+10%3A09%3A34.227461%2B00%3A00&lbl=measurements&fu=1 HTTP/1.1" 200 183 0.015252
::1 - - [2017-07-27 12:09:36] "GET /~/mn-cse-1/onem2m?cra=2017-07-27+10%3A09%3A35.252923%2B00%3A00&lbl=measurements&fu=1 HTTP/1.1" 200 183 0.013147
::1 - - [2017-07-27 12:09:36] "POST /onem2m/TestIPE/devices/Humi-2/measurements HTTP/1.1" 201 531 0.047898
::1 - - [2017-07-27 12:09:37] "GET /~/mn-cse-1/onem2m?cra=2017-07-27+10%3A09%3A36.276019%2B00%3A00&lbl=measurements&fu=1 HTTP/1.1" 200 183 0.016102
::1 - - [2017-07-27 12:09:37] "POST /onem2m/TestIPE/devices/Temp-1/measurements HTTP/1.1" 201 531 0.048973
::1 - - [2017-07-27 12:09:38] "GET /~/mn-cse-1/onem2m?cra=2017-07-27+10%3A09%3A37.301073%2B00%3A00&lbl=measurements&fu=1 HTTP/1.1" 200 183 0.019646
::1 - - [2017-07-27 12:09:38] "POST /onem2m/TestIPE/devices/Humi-1/measurements HTTP/1.1" 201 531 0.049452
::1 - - [2017-07-27 12:09:39] "GET /~/mn-cse-1/onem2m?cra=2017-07-27+10%3A09%3A38.330637%2B00%3A00&lbl=measurements&fu=1 HTTP/1.1" 200 183 0.014191
::1 - - [2017-07-27 12:09:40] "GET /~/mn-cse-1/onem2m?cra=2017-07-27+10%3A09%3A39.354340%2B00%3A00&lbl=measurements&fu=1 HTTP/1.1" 200 183 0.014929
::1 - - [2017-07-27 12:09:40] "POST /onem2m/TestIPE/devices/Humi-2/measurements HTTP/1.1" 201 533 0.047670
::1 - - [2017-07-27 12:09:41] "GET /~/mn-cse-1/onem2m?cra=2017-07-27+10%3A09%3A40.378678%2B00%3A00&lbl=measurements&fu=1 HTTP/1.1" 200 183 0.015533
::1 - - [2017-07-27 12:09:41] "POST /onem2m/TestIPE/devices/Humi-1/measurements HTTP/1.1" 201 533 0.049902
::1 - - [2017-07-27 12:09:42] "GET /~/mn-cse-1/onem2m?cra=2017-07-27+10%3A09%3A41.405124%2B00%3A00&lbl=measurements&fu=1 HTTP/1.1" 200 183 0.021273
::1 - - [2017-07-27 12:09:42] "DELETE /onem2m/TestIPE HTTP/1.1" 200 161 0.029264
::1 - - [2017-07-27 12:09:43] "GET /~/mn-cse-1/onem2m?cra=2017-07-27+10%3A09%3A42.437767%2B00%3A00&lbl=measurements&fu=1 HTTP/1.1" 200 183 0.001473
```
