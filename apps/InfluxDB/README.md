# InfluxDB

This App will subscribe to OpenMTC data and tranfer it to an instance of the InfluxDB.

## Run the app

You need a running instance of InfluxDB and configure the following parameters according to your setup.

```
apps/influx-db \
    --ep "http://127.0.0.1:8000" \
    --influx_host "127.0.0.1" \
    --influx-port "8086" \
    --influx-user "root" \
    --influx-password "secret" \
    --db-name "example" \
    --db-user "root" \
    --db-pw "secret"
```

## Data Model

Entries in the InfluxDB are organized by measurement, time, fields and tags. Data is transfered from OpenMTC like shown below:

* measurement: data_senml["n"] (example: vehiclecount)
* time: data_senml["t"]
* tags:
  * application name (example: loadgen)
  * device name (example: parking_space)
  * sensor name (example: totalspaces)
  * sensor labels (example: "openmtc:sensor")
  * device labels (example: "openmtc:device")
* fields:
  * value: data_senml["v"]
  * bn: data_senml["bn"]
  * unit: data_senml["u"]
