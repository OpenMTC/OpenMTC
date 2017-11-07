```sh
user@host:/git$ ./openmtc-open-source/openmtc-gevent/run-backend
PYTHONPATH: :/git/openmtc-open-source/openmtc-gevent/../futile/src:/git/openmtc-open-source/openmtc-gevent/../common/openmtc/lib:/git/openmtc-open-source/openmtc-gevent/../common/openmtc-onem2m/src:/git/openmtc-open-source/openmtc-gevent/../common/openmtc/src:/git/openmtc-open-source/openmtc-gevent/../serializers/*/src:/git/openmtc-open-source/openmtc-gevent/../openmtc-app/src
PYTHONPATH: :/git/openmtc-open-source/openmtc-gevent/../futile/src:/git/openmtc-open-source/openmtc-gevent/../common/openmtc/lib:/git/openmtc-open-source/openmtc-gevent/../common/openmtc-onem2m/src:/git/openmtc-open-source/openmtc-gevent/../common/openmtc/src:/git/openmtc-open-source/openmtc-gevent/../serializers/*/src:/git/openmtc-open-source/openmtc-gevent/../openmtc-app/src:/git/openmtc-open-source/openmtc-gevent/src:/git/openmtc-open-source/openmtc-gevent/../server/openmtc-cse/src:/git/openmtc-open-source/openmtc-gevent/../server/openmtc-server/src
DEBUG:openmtc_gevent.main:Reading config file: config-backend.json
::1 - - [2017-07-27 13:56:51] "POST /~/in-cse-1/onem2m HTTP/1.1" 201 488 0.003584
::1 - - [2017-07-27 13:56:51] "GET /~/in-cse-1/onem2m HTTP/1.1" 200 515 0.000941
::1 - - [2017-07-27 13:57:04] "POST /onem2m HTTP/1.1" 201 470 0.001442
::1 - - [2017-07-27 13:57:04] "GET /onem2m/TestGUI HTTP/1.1" 200 465 0.000659
::1 - - [2017-07-27 13:57:04] "GET /~/mn-cse-1/onem2m?fu=1&lbl=measurements&drt2 HTTP/1.1" 200 183 0.005280
::1 - - [2017-07-27 13:57:04] "GET /~/mn-cse-1/onem2m?fu=1&lbl=commands&drt2 HTTP/1.1" 200 299 0.005015
::1 - - [2017-07-27 13:57:05] "GET /~/mn-cse-1/onem2m?fu=1&cra=2017-07-27+11%3A57%3A04.595851%2B00%3A00&lbl=measurements&drt2 HTTP/1.1" 200 237 0.016746
::1 - - [2017-07-27 13:57:05] "GET /~/mn-cse-1/onem2m?fu=1&cra=2017-07-27+11%3A57%3A04.597361%2B00%3A00&lbl=commands&drt2 HTTP/1.1" 200 183 0.021630
::1 - - [2017-07-27 13:57:05] "GET /~/mn-cse-1/onem2m/TestIPE/devices/Humi-1/measurements HTTP/1.1" 200 574 0.012765
::1 - - [2017-07-27 13:57:05] "POST /~/mn-cse-1/onem2m/TestIPE/devices/Humi-1/measurements HTTP/1.1" 201 507 0.099880
::1 - - [2017-07-27 13:57:06] "GET /~/mn-cse-1/onem2m?fu=1&cra=2017-07-27+11%3A57%3A05.625861%2B00%3A00&lbl=commands&drt2 HTTP/1.1" 200 183 0.018821
::1 - - [2017-07-27 13:57:06] "GET /~/mn-cse-1/onem2m?fu=1&cra=2017-07-27+11%3A57%3A05.739613%2B00%3A00&lbl=measurements&drt2 HTTP/1.1" 200 237 0.008851
::1 - - [2017-07-27 13:57:06] "GET /~/mn-cse-1/onem2m/TestIPE/devices/Humi-2/measurements HTTP/1.1" 200 574 0.004739
::1 - - [2017-07-27 13:57:06] "POST /~/mn-cse-1/onem2m/TestIPE/devices/Humi-2/measurements HTTP/1.1" 201 507 0.090307
::1 - - [2017-07-27 13:57:07] "POST /_/openmtc.org/in-cse-1/CTestGUI HTTP/1.1" 200 161 0.051118
::1 - - [2017-07-27 13:57:07] "GET /~/mn-cse-1/onem2m?fu=1&cra=2017-07-27+11%3A57%3A06.648521%2B00%3A00&lbl=commands&drt2 HTTP/1.1" 200 183 0.018782
::1 - - [2017-07-27 13:57:07] "GET /~/mn-cse-1/onem2m?fu=1&cra=2017-07-27+11%3A57%3A06.850242%2B00%3A00&lbl=measurements&drt2 HTTP/1.1" 200 183 0.018515
::1 - - [2017-07-27 13:57:08] "POST /_/openmtc.org/in-cse-1/CTestGUI HTTP/1.1" 200 161 0.096046
::1 - - [2017-07-27 13:57:08] "GET /~/mn-cse-1/onem2m?fu=1&cra=2017-07-27+11%3A57%3A07.670974%2B00%3A00&lbl=commands&drt2 HTTP/1.1" 200 183 0.018577
::1 - - [2017-07-27 13:57:08] "GET /~/mn-cse-1/onem2m?fu=1&cra=2017-07-27+11%3A57%3A07.871679%2B00%3A00&lbl=measurements&drt2 HTTP/1.1" 200 183 0.026302
::1 - - [2017-07-27 13:57:09] "GET /~/mn-cse-1/onem2m?fu=1&cra=2017-07-27+11%3A57%3A08.692558%2B00%3A00&lbl=commands&drt2 HTTP/1.1" 200 183 0.018213
::1 - - [2017-07-27 13:57:09] "GET /~/mn-cse-1/onem2m?fu=1&cra=2017-07-27+11%3A57%3A08.901452%2B00%3A00&lbl=measurements&drt2 HTTP/1.1" 200 183 0.018222
::1 - - [2017-07-27 13:57:10] "GET /~/mn-cse-1/onem2m?fu=1&cra=2017-07-27+11%3A57%3A09.714743%2B00%3A00&lbl=commands&drt2 HTTP/1.1" 200 183 0.020672
::1 - - [2017-07-27 13:57:10] "GET /~/mn-cse-1/onem2m?fu=1&cra=2017-07-27+11%3A57%3A09.923621%2B00%3A00&lbl=measurements&drt2 HTTP/1.1" 200 237 0.020293
::1 - - [2017-07-27 13:57:10] "GET /~/mn-cse-1/onem2m/TestIPE/devices/Temp-2/measurements HTTP/1.1" 200 579 0.013450
::1 - - [2017-07-27 13:57:11] "POST /~/mn-cse-1/onem2m/TestIPE/devices/Temp-2/measurements HTTP/1.1" 201 508 0.095122
::1 - - [2017-07-27 13:57:11] "GET /~/mn-cse-1/onem2m?fu=1&cra=2017-07-27+11%3A57%3A10.739403%2B00%3A00&lbl=commands&drt2 HTTP/1.1" 200 183 0.021823
::1 - - [2017-07-27 13:57:12] "GET /~/mn-cse-1/onem2m?fu=1&cra=2017-07-27+11%3A57%3A11.062693%2B00%3A00&lbl=measurements&drt2 HTTP/1.1" 200 237 0.005329
::1 - - [2017-07-27 13:57:12] "GET /~/mn-cse-1/onem2m/TestIPE/devices/Temp-1/measurements HTTP/1.1" 200 580 0.003225
::1 - - [2017-07-27 13:57:12] "POST /~/mn-cse-1/onem2m/TestIPE/devices/Temp-1/measurements HTTP/1.1" 201 508 0.095343
::1 - - [2017-07-27 13:57:12] "GET /~/mn-cse-1/onem2m?fu=1&cra=2017-07-27+11%3A57%3A11.764429%2B00%3A00&lbl=commands&drt2 HTTP/1.1" 200 183 0.006962
::1 - - [2017-07-27 13:57:13] "GET /~/mn-cse-1/onem2m?fu=1&cra=2017-07-27+11%3A57%3A12.172755%2B00%3A00&lbl=measurements&drt2 HTTP/1.1" 200 183 0.021495
::1 - - [2017-07-27 13:57:13] "POST /_/openmtc.org/in-cse-1/CTestGUI HTTP/1.1" 200 161 0.046212
::1 - - [2017-07-27 13:57:13] "GET /~/mn-cse-1/onem2m?fu=1&cra=2017-07-27+11%3A57%3A12.772512%2B00%3A00&lbl=commands&drt2 HTTP/1.1" 200 183 0.022092
::1 - - [2017-07-27 13:57:14] "GET /~/mn-cse-1/onem2m?fu=1&cra=2017-07-27+11%3A57%3A13.197370%2B00%3A00&lbl=measurements&drt2 HTTP/1.1" 200 183 0.022078
::1 - - [2017-07-27 13:57:14] "GET /~/mn-cse-1/onem2m?fu=1&cra=2017-07-27+11%3A57%3A13.798782%2B00%3A00&lbl=commands&drt2 HTTP/1.1" 200 183 0.022495
::1 - - [2017-07-27 13:57:15] "GET /~/mn-cse-1/onem2m?fu=1&cra=2017-07-27+11%3A57%3A14.222723%2B00%3A00&lbl=measurements&drt2 HTTP/1.1" 200 183 0.021815
::1 - - [2017-07-27 13:57:15] "POST /_/openmtc.org/in-cse-1/CTestGUI HTTP/1.1" 200 161 0.049609
::1 - - [2017-07-27 13:57:15] "GET /~/mn-cse-1/onem2m?fu=1&cra=2017-07-27+11%3A57%3A14.825227%2B00%3A00&lbl=commands&drt2 HTTP/1.1" 200 183 0.022142
::1 - - [2017-07-27 13:57:16] "GET /~/mn-cse-1/onem2m?fu=1&cra=2017-07-27+11%3A57%3A15.248347%2B00%3A00&lbl=measurements&drt2 HTTP/1.1" 200 183 0.021845
::1 - - [2017-07-27 13:57:16] "POST /_/openmtc.org/in-cse-1/CTestGUI HTTP/1.1" 200 161 0.046456
::1 - - [2017-07-27 13:57:16] "GET /~/mn-cse-1/onem2m?fu=1&cra=2017-07-27+11%3A57%3A15.851501%2B00%3A00&lbl=commands&drt2 HTTP/1.1" 200 183 0.023678
::1 - - [2017-07-27 13:57:17] "GET /~/mn-cse-1/onem2m?fu=1&cra=2017-07-27+11%3A57%3A16.274279%2B00%3A00&lbl=measurements&drt2 HTTP/1.1" 200 183 0.012253
::1 - - [2017-07-27 13:57:17] "GET /~/mn-cse-1/onem2m?fu=1&cra=2017-07-27+11%3A57%3A16.878481%2B00%3A00&lbl=commands&drt2 HTTP/1.1" 200 183 0.007413
::1 - - [2017-07-27 13:57:18] "GET /~/mn-cse-1/onem2m?fu=1&cra=2017-07-27+11%3A57%3A17.289737%2B00%3A00&lbl=measurements&drt2 HTTP/1.1" 200 183 0.027434
::1 - - [2017-07-27 13:57:18] "POST /_/openmtc.org/in-cse-1/CTestGUI HTTP/1.1" 200 161 0.052167
::1 - - [2017-07-27 13:57:18] "GET /~/mn-cse-1/onem2m?fu=1&cra=2017-07-27+11%3A57%3A17.887983%2B00%3A00&lbl=commands&drt2 HTTP/1.1" 200 183 0.023076
::1 - - [2017-07-27 13:57:19] "GET /~/mn-cse-1/onem2m?fu=1&cra=2017-07-27+11%3A57%3A18.321269%2B00%3A00&lbl=measurements&drt2 HTTP/1.1" 200 183 0.023393
::1 - - [2017-07-27 13:57:19] "GET /~/mn-cse-1/onem2m?fu=1&cra=2017-07-27+11%3A57%3A18.914453%2B00%3A00&lbl=commands&drt2 HTTP/1.1" 200 183 0.007408
::1 - - [2017-07-27 13:57:20] "GET /~/mn-cse-1/onem2m?fu=1&cra=2017-07-27+11%3A57%3A19.348526%2B00%3A00&lbl=measurements&drt2 HTTP/1.1" 200 183 0.022457
::1 - - [2017-07-27 13:57:20] "POST /_/openmtc.org/in-cse-1/CTestGUI HTTP/1.1" 200 161 0.056230
::1 - - [2017-07-27 13:57:20] "GET /~/mn-cse-1/onem2m?fu=1&cra=2017-07-27+11%3A57%3A19.924024%2B00%3A00&lbl=commands&drt2 HTTP/1.1" 200 183 0.026688
::1 - - [2017-07-27 13:57:21] "GET /~/mn-cse-1/onem2m?fu=1&cra=2017-07-27+11%3A57%3A20.374134%2B00%3A00&lbl=measurements&drt2 HTTP/1.1" 200 183 0.025529
::1 - - [2017-07-27 13:57:21] "GET /~/mn-cse-1/onem2m?fu=1&cra=2017-07-27+11%3A57%3A20.953640%2B00%3A00&lbl=commands&drt2 HTTP/1.1" 200 183 0.006857
::1 - - [2017-07-27 13:57:22] "GET /~/mn-cse-1/onem2m?fu=1&cra=2017-07-27+11%3A57%3A21.402722%2B00%3A00&lbl=measurements&drt2 HTTP/1.1" 200 183 0.025722
::1 - - [2017-07-27 13:57:22] "GET /~/mn-cse-1/onem2m?fu=1&cra=2017-07-27+11%3A57%3A21.962632%2B00%3A00&lbl=commands&drt2 HTTP/1.1" 200 183 0.022066
::1 - - [2017-07-27 13:57:23] "GET /~/mn-cse-1/onem2m?fu=1&cra=2017-07-27+11%3A57%3A22.431626%2B00%3A00&lbl=measurements&drt2 HTTP/1.1" 200 183 0.023046
::1 - - [2017-07-27 13:57:24] "GET /~/mn-cse-1/onem2m?fu=1&cra=2017-07-27+11%3A57%3A22.988582%2B00%3A00&lbl=commands&drt2 HTTP/1.1" 200 183 0.025497
::1 - - [2017-07-27 13:57:24] "GET /~/mn-cse-1/onem2m?fu=1&cra=2017-07-27+11%3A57%3A23.458088%2B00%3A00&lbl=measurements&drt2 HTTP/1.1" 200 183 0.023691
```
