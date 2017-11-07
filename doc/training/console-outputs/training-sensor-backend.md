```sh
user@host:/git$ ./openmtc-open-source/openmtc-gevent/run-backend   
PYTHONPATH: :/git/openmtc-open-source/openmtc-gevent/../futile/src:/git/openmtc-open-source/openmtc-gevent/../common/openmtc/lib:/git/openmtc-open-source/openmtc-gevent/../common/openmtc-onem2m/src:/git/openmtc-open-source/openmtc-gevent/../common/openmtc/src:/git/openmtc-open-source/openmtc-gevent/../serializers/*/src:/git/openmtc-open-source/openmtc-gevent/../openmtc-app/src
PYTHONPATH: :/git/openmtc-open-source/openmtc-gevent/../futile/src:/git/openmtc-open-source/openmtc-gevent/../common/openmtc/lib:/git/openmtc-open-source/openmtc-gevent/../common/openmtc-onem2m/src:/git/openmtc-open-source/openmtc-gevent/../common/openmtc/src:/git/openmtc-open-source/openmtc-gevent/../serializers/*/src:/git/openmtc-open-source/openmtc-gevent/../openmtc-app/src:/git/openmtc-open-source/openmtc-gevent/src:/git/openmtc-open-source/openmtc-gevent/../server/openmtc-cse/src:/git/openmtc-open-source/openmtc-gevent/../server/openmtc-server/src
DEBUG:openmtc_gevent.main:Reading config file: config-backend.json
::1 - - [2017-07-27 12:09:15] "POST /~/in-cse-1/onem2m HTTP/1.1" 201 488 0.004198
::1 - - [2017-07-27 12:09:15] "GET /~/in-cse-1/onem2m HTTP/1.1" 200 515 0.000929
::1 - - [2017-07-27 12:09:33] "POST /onem2m HTTP/1.1" 201 470 0.001444
::1 - - [2017-07-27 12:09:33] "GET /onem2m/TestGUI HTTP/1.1" 200 465 0.000686
::1 - - [2017-07-27 12:09:33] "GET /~/mn-cse-1/onem2m?fu=1&lbl=measurements&drt2 HTTP/1.1" 200 403 0.005261
::1 - - [2017-07-27 12:09:33] "GET /~/mn-cse-1/onem2m/TestIPE/devices/Temp-2/measurements HTTP/1.1" 200 651 0.003173
::1 - - [2017-07-27 12:09:33] "POST /~/mn-cse-1/onem2m/TestIPE/devices/Temp-2/measurements HTTP/1.1" 201 507 0.102775
::1 - - [2017-07-27 12:09:33] "GET /~/mn-cse-1/onem2m/TestIPE/devices/Humi-2/measurements HTTP/1.1" 200 574 0.011672
::1 - - [2017-07-27 12:09:33] "POST /~/mn-cse-1/onem2m/TestIPE/devices/Humi-2/measurements HTTP/1.1" 201 507 0.101555
::1 - - [2017-07-27 12:09:33] "GET /~/mn-cse-1/onem2m/TestIPE/devices/Humi-1/measurements HTTP/1.1" 200 574 0.014317
::1 - - [2017-07-27 12:09:34] "POST /~/mn-cse-1/onem2m/TestIPE/devices/Humi-1/measurements HTTP/1.1" 201 507 0.100284
::1 - - [2017-07-27 12:09:34] "GET /~/mn-cse-1/onem2m/TestIPE/devices/Temp-1/measurements HTTP/1.1" 200 651 0.016302
::1 - - [2017-07-27 12:09:34] "POST /~/mn-cse-1/onem2m/TestIPE/devices/Temp-1/measurements HTTP/1.1" 201 507 0.099349
::1 - - [2017-07-27 12:09:34] "POST /_/openmtc.org/in-cse-1/CTestGUI HTTP/1.1" 200 161 0.064469
::1 - - [2017-07-27 12:09:35] "GET /~/mn-cse-1/onem2m?fu=1&cra=2017-07-27+10%3A09%3A34.227461%2B00%3A00&lbl=measurements&drt2 HTTP/1.1" 200 183 0.021622
::1 - - [2017-07-27 12:09:36] "GET /~/mn-cse-1/onem2m?fu=1&cra=2017-07-27+10%3A09%3A35.252923%2B00%3A00&lbl=measurements&drt2 HTTP/1.1" 200 183 0.019777
::1 - - [2017-07-27 12:09:36] "POST /_/openmtc.org/in-cse-1/CTestGUI HTTP/1.1" 200 161 0.095844
::1 - - [2017-07-27 12:09:37] "GET /~/mn-cse-1/onem2m?fu=1&cra=2017-07-27+10%3A09%3A36.276019%2B00%3A00&lbl=measurements&drt2 HTTP/1.1" 200 183 0.021947
::1 - - [2017-07-27 12:09:37] "POST /_/openmtc.org/in-cse-1/CTestGUI HTTP/1.1" 200 161 0.053290
::1 - - [2017-07-27 12:09:38] "GET /~/mn-cse-1/onem2m?fu=1&cra=2017-07-27+10%3A09%3A37.301073%2B00%3A00&lbl=measurements&drt2 HTTP/1.1" 200 183 0.026539
::1 - - [2017-07-27 12:09:38] "POST /_/openmtc.org/in-cse-1/CTestGUI HTTP/1.1" 200 161 0.053452
::1 - - [2017-07-27 12:09:39] "GET /~/mn-cse-1/onem2m?fu=1&cra=2017-07-27+10%3A09%3A38.330637%2B00%3A00&lbl=measurements&drt2 HTTP/1.1" 200 183 0.020305
::1 - - [2017-07-27 12:09:40] "GET /~/mn-cse-1/onem2m?fu=1&cra=2017-07-27+10%3A09%3A39.354340%2B00%3A00&lbl=measurements&drt2 HTTP/1.1" 200 183 0.020969
::1 - - [2017-07-27 12:09:40] "POST /_/openmtc.org/in-cse-1/CTestGUI HTTP/1.1" 200 161 0.050797
::1 - - [2017-07-27 12:09:41] "GET /~/mn-cse-1/onem2m?fu=1&cra=2017-07-27+10%3A09%3A40.378678%2B00%3A00&lbl=measurements&drt2 HTTP/1.1" 200 183 0.022431
::1 - - [2017-07-27 12:09:41] "POST /_/openmtc.org/in-cse-1/CTestGUI HTTP/1.1" 200 161 0.054525
::1 - - [2017-07-27 12:09:42] "GET /~/mn-cse-1/onem2m?fu=1&cra=2017-07-27+10%3A09%3A41.405124%2B00%3A00&lbl=measurements&drt2 HTTP/1.1" 200 183 0.029247
::1 - - [2017-07-27 12:09:43] "GET /~/mn-cse-1/onem2m?fu=1&cra=2017-07-27+10%3A09%3A42.437767%2B00%3A00&lbl=measurements&drt2 HTTP/1.1" 200 183 0.003374
::1 - - [2017-07-27 12:09:43] "DELETE /~/in-cse-1/onem2m/mn-cse-1 HTTP/1.1" 200 161 0.003337
::1 - - [2017-07-27 12:09:44] "GET /~/mn-cse-1/onem2m?fu=1&cra=2017-07-27+10%3A09%3A43.442350%2B00%3A00&lbl=measurements&drt2 HTTP/1.1" 404 168 0.003254
```
