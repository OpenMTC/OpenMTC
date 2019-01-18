# Conformance testing

Based on [pyresttest](https://github.com/svanoort/pyresttest). It implements the tests from [TS-0013](http://www.onem2m.org/component/rsfiles/download-file/files?path=Release_2_Draft_TS%255CTS-0013-Interoperability_Testing-V2_6_0.DOC&Itemid=238).

## Prerequisites

The python module pyresttest has to be installed.

```bash
$ pip install pyresttest
```

## Running the Tests

The tests can be run from the command line. Make sure that a instance is running.

Assuming that a gateway is running at localhost, port 8000.

```bash
$ pyresttest http://localhost:8000 tests/interoperability/basic.yaml
Test Group Openmtc Test 8.1.1 SUCCEEDED: : 1/1 Tests Passed!
Test Group Openmtc Test 8.1.2 SUCCEEDED: : 4/4 Tests Passed!
Test Group Openmtc Test 8.1.3 SUCCEEDED: : 4/4 Tests Passed!
Test Group Openmtc Test 8.1.4 SUCCEEDED: : 8/8 Tests Passed!
Test Group Openmtc Test 8.1.5 SUCCEEDED: : 13/13 Tests Passed!
Test Group Openmtc Test 8.1.6 SUCCEEDED: : 4/4 Tests Passed!
```
