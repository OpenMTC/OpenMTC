# Introduction

OrionContextBroker is an OpenMTC AE to forward OpenMTC sensor data (via Subscription) to an instance of the Orion Context Broker. Additionally OpenMTC actuators are handled by forwarding changes on the OCB side via OpenMTC to the actuator.
All Content Instances are expected to use the SenML format. It is possible to connect the AE either to an OpenMTC Gateway or an OpenMTC Backend.

# Getting started

Within the OpenMTC root directory the app can be started via

```
./apps/orion-context-broker -v
```

## Configuration

It is possible to configure the AE either via config.json or CLI parameters. All possible parameters can be shown via:

```
./apps/orion-context-broker  -h
```

The most important parameters are:

* ep (the OpenMTC host)
* labels (the labels that should be forwarded to the OrionCB, one label has to match (OR), empty ([""]) means every label)
* interval (for periodic discovery)
* orion_host (hostname:port of the Orion CB)
* accumulate_address (Subscription Sink (RESTful HTTP) used for subscriptions to the OCB (actuator functionality))

# How the data is stored at the Orion CB

The Orion CB uses the model of *entities* having *attributes*. The AE matches all Container having the label "openmtc:device" to entities. Attributes are matched to the SenML Key "n" of Content Instances. The types of values are determined by the AE to match typical Orion CB types (e.g. Int, String, Float...).

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

# Actuator Functionality

![](actuator_arch.png)

If an actuator is created in OpenMTC an event is triggered at the orion context broker app. The app will create an entity of the actuator on the OCB with an attribute "cmd". After that a subscription to the attribute "cmd" is created and therefore all change on this attribute will be forwarded to the corresponding OpenMTC backend or gateway.
