# Subscriptions and Notifications

## General Description of Subscription and Notification

The subscription and notification mechanism can be used to track changes on a resource. Therefore, a subscription is created by the resource subscriber containing subscription information. An AE or CSE can be the resource subscriber. When the resource is modified, the hosting CSE of the resource is sending a notification for the subscriber to the address(es) specified in the subscription information.

## The Subscription Resource

A subscription is represented by a `<subscription>` resource as child resource of the subscribed-to resource. The subscription contains subscription information, most importantly:

- the list `notificationURI`
- and the attribute `subscriberURI`.

The `notificationURI` list can contain one or more addresses where the resource subscriber wants to receive notifications. The attribute `subscriberURI` contains the address of the subscriber that is used by the CSE to send a notification when the `<subscription>` resource itself is deleted.

The `<subscription>` resource is supported by resource types like:

- CSEBase
- remoteCSE
- AE
- container
- contentInstance
- accessControlPolicy
- mgmtObj

**Note:** The `<contentInstance>` resource does not include the `<subscription>` resource as a child resource. To keep track of changes of `<contentInstance>` resources a subscription in the corresponding parent `container` resource needs to be created.


## Subscription and Notification using the Application Framework

The OpenMTC Application Framework provides the following methods to create subscriptions and handle notifications.

### The `add_container_subscription` method

The Application Framework provides the `add_container_subscription` method to create a subscription to the contentInstances of a given container and specify a handler function that is called when a notification is send. Optionally, a delete handler and filter criteria can be specified.

The method with its parameters is listed below:

`add_container_subscription(self, container, handler, delete_handler=None, filter_criteria=None)`

- `container`: container object or container path string
- `handler`: reference of the notification handling function
- `delete_handler`: (optional) reference to delete handling function
- `filter_criteria`: (optional) filterCriteria for the subscription

The parameters given to the `handler` function are:

- the path of the subscribed-to container
- the content data of the contentInstance which was created

The parameter given to the `delete_handler` function is:

- the path of the subscription


### Example: Using the `add_container_subscription` method

This example shows how the `add_container-subscription` method is used. The following code is part of the **training app** `onem2m-ipe-sensors-actuators-final` that can be found [here](./training/apps/onem2m/ipe/sensors-actuators/onem2m-ipe-sensors-actuators-final.py).
```python
# add commands_container of current actuator to self._command_containers
self._command_containers[actuator] = commands_container
# subscribe to command container of each actuator to the handler command
self.add_container_subscription(
    commands_container.path,    # the Container or it's path to be subscribed
    self.handle_command         # reference of the notification handling function
)
```

This code creates a subscription to the path of the `commands` container and registers the `handle_command` function as the notification handling function.


The `handle_command` function of the example application looks like this.
```python
def handle_command(self, container, value):
    print('handle_command...')
    print('container: %s' % container)
    print('value: %s' % value)
    print('')
```

In this example the handling function simply prints the path of the container and the JSON data to the terminal.

### Curl request for testing the `handle_command` notification handling function

In the following the REST API is used to demonstrate the `handle_command` handling function of the example from above. Therefore, an HTTP POST request is send to the `commands` subcontainer of the `Switch-AirCon` container.  The request contains some JSON data that is pushed as a contentInstance to the container. The creation of the contentInstance triggers the notification to be send to the IPE, because of the subscription that was created with the `add_container_subscription` method. The `handle_command` function handles the notification.

For this example, the following example data is send:
```json
{
	"switch_state": "on"
}
```

The data is encoded to its base64 string:
```
eyAic3dpdGNoX3N0YXRlIjogIm9uIiB9
```

To start the  `onem2m-ipe-sensors-actuators-final` training application, go to the training folder  `doc/training`:
```bash
$ cd doc/training
```

Run the **start-app** script to start one of the training applications:
```bash
$ `./start-app.sh`
```

Choose number `2` to start the `onem2m-ipe-sensors-actuators-final.py`


Send the following curl request to create the contentInstance and trigger the notification to be send:
```shell
curl -X POST localhost:8000/onem2m/TestIPE/devices/Switch-AirCon/commands -H 'Content-Type: application/vnd.onem2m-res+json' -d '{"m2m:cin": {"con": "eyAic3dpdGNoX3N0YXRlIjogIm9uIiB9", "cnf":"application/json:1"}}'
```

When sending the request, the notification is triggered and handled by the `handle_command` handling function that prints the following output to the terminal:
```
handle_command_cnt...
container: onem2m/TestIPE/devices/Switch-AirCon/commands
value: {u'switch_state': u'on'}
```

### The `add_subscription` method

This method creates a subscription resource at the given path and registers an handler to receive notification data. In comparison to the `add_container_subscription` method, the notification does not include the content data of a contentInstance, but information about the resource and subscription that triggered the notification.

The method with its parameters is listed below:

`add_subscription(self, path, handler, delete_handler=None)`

- `path`: path to subscribe to
- `handler`: notification handler
- `delete_handler`: reference to delete handling function


The notification that is send to the handling function includes the following three parameters:

- the path of the subscription
- the notification event type
- the resource representation

### Example: Using the `add_subscription` method

This example again uses the **training app** `onem2m-ipe-sensors-actuators-final`, but with some modified code using the `add_subscription` method that creates a subscription to the `Switch-AirCon`container.
```python
self.add_subscription(
    "onem2m/TestIPE/devices/Switch-AirCon",
    self.handle_command
)
```

The handle method is modified like this:

```python
def handle_command(self, sub, net, rep):
    print('handle_command_general...')
    print('subscription path: %s' % sub)
    print('notification event type: %s' % net)
    print('representation: %s' % rep)
    print('')
```

The terminal output of the handle method is:
```
handle_command...
subscription path: onem2m/TestIPE/devices/Switch-AirCon/subscription-J3VOG9vvCfg2ifiR
notification event type: None
representation: Container(path='None', id='cnt1')
```
As a result, the information of the resource representation from the notification can be used to perform further requests on the container resource.


## Curl request to create a Subscription using the REST API

A subscription can also be created using the REST API. Therefore, a POST request is send to the path where the subscription should be created.

In the following this example shows a curl request that creates a subscription in the `Switch-AirCon`container of the `onem2m-ipe-sensors-actuators-final` training app from above.

```shell
curl -X POST localhost:8000/onem2m/TestIPE/devices/Switch-AirCon/commands -H 'Content-Type: application/vnd.onem2m-res+json;ty=23' -d '{  "m2m:sub": {  "nu": "TestIPE",  "rn":"sub101"  }}'
```

This POST request creates a subscription in the `commands` container at the URI `localhost:8000/onem2m/TestIPE/devices/Switch-AirCon/commands`. The `resource type (ty)` number `23` included in the Content-Type header field represents the resource type of a subscription resource.
The subscription created by this curl request includes the `resource name (rn)` of the subscription which is `sub101` and the `notification URI (nu)` which is `TestIPE`, the AE-ID of the IPE. When the AE-ID is used, the CSE automatically replaces it with the appropriate absolute path of the application resource, which in this example is `["//openmtc.org/mn-cse-1/CTestIPE"]`.

Likewise, the curl request can include a list of notification URIs:
```shell
curl -X POST localhost:8000/onem2m/TestIPE/devices/Switch-AirCon/commands -H 'Content-Type: application/vnd.onem2m-res+json;ty=23' -d '{  "m2m:sub": {  "nu":["//openmtc.org/mn-cse-1/CTestIPE"],  "rn":"sub101"  }}'
```
