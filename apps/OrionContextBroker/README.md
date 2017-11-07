# Introduction

OrionContextBroker is an OpenMTC AE to forward OpenMTC data (via Subscription) to an instance of the Orion Context Broker. 
All ContentInstances are expected to use the SenML format. It is possible to connect the AE either to an OpenMTC Gateway or an OpenMTC Backend.

# Getting started

Within the openmtc root directory the app can be started via

```
./apps/orion-context-broker -v
```

## Configuration

It is possible to configure the AE either via config.json or CLI paramters. All possible paramters can be shown via:

```
./apps/orion-context-broker  -h
```

The most important parameters are:

* ep (the OpenMTC host)
* labels (the labels that should be forwarded to the OrionCB, one label has to match (OR), empty ([""]) means every label)
* interval (for periodic discovery)
* orion_host (hostname:port of the Orion CB)

# How the data is stored at the Orion CB

The Orion CB uses the model of *entities* having *attributes*. The AE matches all Container having the label "openmtc:device" to entities. Attributes are matched to the SenML Key "n" of ContentInstances. The types of values are determined by the AE to match typical Orion CB types (e.g. Int, String, Float...).

## Example

### Create Data in OpenMTC

Create an App with OpenMTC:

```
curl -X POST localhost:18000/onem2m/ -H "Content-Type: application/vnd.onem2m-res+json" -d '{"m2m:ae": {"rn": "EXAMPLE_APP_NAME", "api": "placeholder", "rr": "TRUE"}}'
```

Create an Device with OpenMTC:

```
curl -X POST localhost:18000/onem2m/EXAMPLE_APP_NAME/ -H "Content-Type: application/vnd.onem2m-res+json" -d '{"m2m:cnt": {"rn": "EXAMPLE_DEVICE_NAME", "lbl":["openmtc:device"]}}'
```

Create an Measurment (Sensor data container) with OpenMTC:

```
curl -X POST localhost:18000/onem2m/EXAMPLE_APP_NAME/EXAMPLE_DEVICE_NAME/ -H "Content-Type: application/vnd.onem2m-res+json" -d '{"m2m:cnt": {"rn": "EXAMPLE_MEASUREMENT_NAME", "lbl":["openmtc:sensor_data"]}}'
```

Upload SenML Data to OpenMTC:

```json
{
  "n": "temperature",
  "bn": "openmtc:zigbee:temp",
  "v": 24,
  "u": "Cel",
  "t": "2017-04-13 12:45:12.787239"
}
```
base64: eyJuIjogInRlbXBlcmF0dXJlIiwgImJuIjogIm9wZW5tdGM6emlnYmVlOnRlbXAiLCAidiI6IDI0LCAidSI6ICJDZWwiLCAidCI6ICIyMDE3LTA0LTEzIDEyOjQ1OjEyLjc4NzIzOSJ9Cg==

```
curl -X POST localhost:18000/onem2m/EXAMPLE_APP_NAME/EXAMPLE_DEVICE_NAME/EXAMPLE_MEASUREMENT_NAME/ -H "Content-Type: application/vnd.onem2m-res+json" -d '{"m2m:cin": {"con": "eyJuIjogInRlbXBlcmF0dXJlIiwgImJuIjogIm9wZW5tdGM6emlnYmVlOnRlbXAiLCAidiI6IDI0LCAidSI6ICJDZWwiLCAidCI6ICIyMDE3LTA0LTEzIDEyOjQ1OjEyLjc4NzIzOSJ9Cg==", "cnf": "application/json:1"}}'
```

### Query Data Orion CB

```
curl localhost:1026/v2/entities/ | jq '.'
```

```json
[
  {
    "id": "EXAMPLE_DEVICE_NAME",
    "type": "openmtc",
    "temperature": {
      "type": "Int",
      "value": 24,
      "metadata": {
        "bn": {
          "type": "String",
          "value": "openmtc:zigbee:temp"
        },
        "timestamp": {
          "type": "String",
          "value": "2017-04-13 12:45:12.787239"
        },
        "unit": {
          "type": "String",
          "value": "Cel"
        }
      }
    }
  }
]
```
