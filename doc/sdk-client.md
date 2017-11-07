# SDK - The low-level CSE Client


## Introduction

The OpenMTC SDK offers a client module for low-level access to the
oneM2M resource tree exposed by a CSE's reference point. Currently,
only the http and https protocols are supported.

Basically, there are different types of Common Service Entities (CSE):

* MN-CSE: Middle Node CSE (OpenMTC Gateway)
* IN-CSE: Infrastructure Node CSE (OpenMTC Backend)

The client module comprises classes for representing requests,
responses as well as classes that provide an abstraction for a
connection to a CSE's reference point (the actual client itself).


## Requests

Requests to a CSE are called a OneM2MRequest. The OpenMTC SDK provides
this class for representing the different types of requests that can
be issued towards a CSE. This class resides under the
`openmtc_onem2m.transport` package. The following requests
(OneM2MOperation) are available:

* `retrieve`
* `delete`
* `create`
* `notify`
* `update`


### OneM2MRequest - Retrieve

The most trivial case of a `OneM2MRequest` is the `retrieve`. It takes
the path of the resource to be retrieved as parameter upon
construction.

This file can be found [here](./training/onem2m-examples/onem2m-example-3.py).
``` py
# Example 3: Retrieve OneM2MRequest

from openmtc_onem2m.transport import OneM2MRequest

request = OneM2MRequest("retrieve", to="onem2m")

print request.to
#>>> onem2m
```


### OneM2MRequest - Delete

Like the `retrieve` `OneM2MRequest`, a `delete` `OneM2MRequest` merely
takes the path of the resource to be deleted as parameter upon
construction.

This file can be found [here](./training/onem2m-examples/onem2m-example-4.py).
``` py
# Example 4: Delete OneM2MRequest

from openmtc_onem2m.transport import OneM2MRequest

request = OneM2MRequest("delete", to="onem2m")

print request.to
#>>> onem2m
```


### OneM2MRequest - Create

When creating a `create` `OneM2MRequest` object we need to specify the
object to be created together with the path where it is to be
created. In most cases this is done by creating an appropriate
resource object and passing it.

This file can be found [here](./training/onem2m-examples/onem2m-example-5a.py).
``` py
# Example 5a: Create OneM2MRequest

from openmtc_onem2m.transport import OneM2MRequest
from openmtc_onem2m.model import AE

my_app = AE(App_ID="myApp")

request = OneM2MRequest("create", to="onem2m", pc="my_app")

print request.to
#>>> onem2m
print request.pc
#>>> myApp
```

When creating contentInstances, we can also pass in a string of raw
data. In this case, we also need to specify the mime-type of the data
via the `resource_type` parameter (ty).

This file can be found [here](./training/onem2m-examples/onem2m-example-5b.py).
``` py
# Example 5b: Create OneM2MRequest with data

from openmtc_onem2m.transport import OneM2MRequest
import json

sensor_data = {"type": "temperature",
               "value": 15 }

data_string = json.dumps(sensor_data)

request = OneM2MRequest("create", 
                        to="onem2m",
                        pc=data_string,
                        ty="application/json")

print request.to
#>>> onem2m
print request.pc
#>>> {"type": "temperature", "value": 15}
```


### OneM2MRequest - Notify

For `notify` `OneM2MRequest` objects the same semantics as for
`create` `OneM2MRequest` apply.

This file can be found [here](./training/onem2m-examples/onem2m-example-6a.py).
``` py
# Example 6a: Notify OneM2MRequest

from openmtc_onem2m.transport import OneM2MRequest
from openmtc_onem2m.model import AE

my_app = AE(App_ID="myApp")

request = OneM2MRequest("notify", to="onem2m", pc=my_app)

print request.to
#>>> onem2m
print request.pc.App_ID
#>>> myApp
```

This file can be found [here](./training/onem2m-examples/onem2m-example-6b.py).
``` py
# Example 6b: Notify OneM2MRequest with data

from openmtc_onem2m.transport import OneM2MRequest
import json

sensor_data = {"type": "temperature",
               "value": 15 }

data_string = json.dumps(sensor_data)

request = OneM2MRequest("create", 
                        to="onem2m",
                        pc=data_string,
                        ty="application/json")

print request.to
#>>> onem2m
print request.pc
#>>> {"type": "temperature", "value": 15}
```


### OneM2MRequest - Update

The `update` `OneM2MRequest` can be used to update specific attributes
of an object (AE). If the request is legal, four different cases are
distinguished:

* If an attribute value **is provided** in the `OneM2MRequest` that
  **exists** in the target resource, the CSE will simply update that
  attribute in the resource representation.
* If an attribute **is not provided** in the `OneM2MRequest`, but the
  attribute **exists** in the target resource, the hosting CSE will
  simply leave the value of that attribute unchanged.
* If an attribute **is provided** in the `OneM2MRequest` and does
  **not exist** in the target resource, the hosting CSE will create
  such attribute with the provided value.
* If an attribute is **set to NULL** in the `OneM2MRequest` and
  **exists** in the target resource, the hosting CSE will delete such
  attribute if the deletion of the attribute is allowed by the local
  policy.

The following example shows the creation of a `update`
`OneM2MRequest`. The CSE would either update the attribute (labels) in
the resource representation if it exists already exists there, or
create the attribute labels with the provided value if it does not
exist in the CSE resource representation yet.

This file can be found [here](./training/onem2m-examples/onem2m-example-7.py).
``` py
# Example 7: Update OneM2MRequest

from openmtc_onem2m.transport import OneM2MRequest
from openmtc_onem2m.model import AE

my_app = AE(App_ID="myApp", labels=["keyword1", "keyword2"])

request = OneM2MRequest("update", to="onem2m", pc=my_app.labels)

print request.to
#>>> onem2m
print request.pc
#>>> [u'keyword1', u'keyword2']
```


## Responses

Upon servicing a request, a CSE will return a `OneM2MResponse`, which
is a class of the client module. This class is defined in the
`openmtc_onem2m.transport` module and derives from the `object` base
class. The following response types are possible:

* `Create`
* `Retrieve`
* `Update`
* `Delete`
* `Notify`
* `Execute`
* `Observe`

An `OneM2MResponse` has the following properties:

* `status_code` - Denotes the result status of the operation (see
  below).
* `request` - The type of the operation. One of (`create`, `retrieve`,
  `update`, `delete`, `notify`, `execute`, `observe`).
* `rqi` - Denotes the request identifier (`requestIdentifier`).
* `pc` - Denotes the resource content (`primitiveContent`).
* `to` - Denotes to destination of the response.


### Error Responses

If an error occurs on the CSE servicing the request, the CSE will
return a `OneM2MErrorResponse`. Note that the `OneM2MErrorResponse`
class is an `Exception`. In case that any error is reported by the CSE
during processing a request, the client will *raise* an instance of
`OneM2MErrorResponse`. The `OneM2MErrorResponse` heritates from the
classes `OneM2MResponse` and `OneM2MError` (`OpenMTCError`) and is not
yet implemented (pass).


### Status Codes

The `status_code` of `OneM2MResponse` objects are defined as constants
in the `openmtc_onem2m.exc` module. The following constants are
defined:

| ``STATUS`` | numeric_code | http_status_code |
|:-----------|:------------:|:----------------:|
| ``STATUS_ACCEPTED`` | 1000 | 202 |
| ``STATUS_OK`` | 2000 | 200 |
| ``STATUS_CREATED`` | 2001 | 201 |
| ``STATUS_BAD_REQUEST`` | 4000 | 400 |
| ``STATUS_NOT_FOUND`` | 4004 | 404 |
| ``STATUS_OPERATION_NOT_ALLOWED`` | 4005 | 405 |
| ``STATUS_REQUEST_TIMEOUT`` | 4008 | 408 |
| ``STATUS_SUBSCRIPTION_CREATOR_HAS_NO_PRIVILEGE`` | 4101 | 403 |
| ``STATUS_CONTENTS_UNACCEPTABLE`` | 4102 | 400 |
| ``STATUS_ACCESS_DENIED`` | 4103 | 403 |
| ``STATUS_GROUP_REQUEST_IDENTIFIER_EXISTS`` | 4104 | 409 |
| ``STATUS_CONFLICT`` | 4015 | 409 |
| ``STATUS_INTERNAL_SERVER_ERROR`` | 5000 | 500 |
| ``STATUS_NOT_IMPLEMENTED`` | 5001 | 501 |
| ``STATUS_TARGET_NOT_REACHABLE`` | 5103 | 404 |
| ``STATUS_NO_PRIVILEGE`` | 5105 | 403 |
| ``STATUS_ALREADY_EXISTS`` | 5106 | 403 |
| ``STATUS_TARGET_NOT_SUBSCRIBABLE`` | 5203 | 403 |
| ``STATUS_SUBSCRIPTION_VERIFICATION_INITIATION_FAILED`` | 5204 | 500 |
| ``STATUS_SUBSCRIPTION_HOST_HAS_NO_PRIVILEGE`` | 5205 | 403 |
| ``STATUS_NON_BLOCKING_REQUEST_NOT_SUPPORTED`` | 5206 | 501 |
| ``STATUS_EXTERNAL_OBJECT_NOT_REACHABLE`` | 6003 | 404 |
| ``STATUS_EXTERNAL_OBJECT_NOT_FOUND`` | 6005 | 404 |
| ``STATUS_MAX_NUMBER_OF_MEMBER_EXCEEDED`` | 6010 | 400 |
| ``STATUS_MEMBER_TYPE_INCONSISTENT`` | 6011 | 400 |
| ``STATUS_MANAGEMENT_SESSION_CANNOT_BE_ESTABLISHED`` | 6020 | 500 |
| ``STATUS_MANAGEMENT_SESSION_ESTABLISHMENT_TIMEOUT`` | 6021 | 500 |
| ``STATUS_INVALID_CMDTYPE`` | 6022 | 400 |
| ``STATUS_INVALID_ARGUMENTS`` | 6023 | 400 |
| ``STATUS_INSUFFICIENT_ARGUMENT`` | 6024 | 400 |
| ``STATUS_MGMT_CONVERSION_ERROR`` | 6025 | 500 |
| ``STATUS_CANCELLATION_FAILED`` | 6026 | 500 |
| ``STATUS_ALREADY_COMPLETE`` | 6028 | 400 |
| ``STATUS_COMMAND_NOT_CANCELLABLE`` | 6029 | 400 |


## Exceptions

In addition to raising an instance of `OneM2MErrorResponse`, the CSE
client might also inidcate error conditions that do not occur while
the CSE was processing the request. This will mainly happen when the
client was unable to contact the CSE for whatever reason.

Exeptions that are raised will be subclasses of the `OpenMTCError`
class defined in the `openmtc.exc` module.


## Using the Client

The client implementation for interfacing with the HTTP interface of
an CSE resides in the `openmtc_onem2m.client.http` module. The
implementing class is called `OneM2MHTTPClient`. In the current
version of the SDK, we simply import the class directly. This is
planned to be replaced with a more sophisticated factory pattern that
creates appropriate clients based on the transport scheme (e.g. `http`
or `mqtt`) that is used.

Client objects expose a method called `send_onem2m_request` for
sending `OneM2MRequest` objects to a CSE.


### Creating a Client

To create a client object, we simply import the `OneM2MHTTPClient`
class from the `openmtc_onem2m.client.http` module and create an
instance of it with the URI of a reference point of an oneM2M CSE.

This file can be found [here](./training/onem2m-examples/onem2m-example-8a.py).
``` py
# Example 8a: Creating a Client

from openmtc_onem2m.client.http import OneM2MHTTPClient

# create a OneM2MHTTPClient object
client = OneM2MHTTPClient("http://localhost:8000", False)
```


### Making Requests

To retrieve a resource from the CSE's resource tree, we can use the
`send_onem2m_request` method and pass an appropriate `OneM2MRequest`
object. In this case we retrieve the `CSEBase` resource of the CSE's
resource tree. If successful, the operation returns a promise, which
contains an `OneM2MResponse` object. The `OneM2MResponse` can be
obtained from the promise by using `.get()`. The `content` property of
the `OneM2MResponse` holds the appropriate `CSEBase` object.

This file can be found [here](./training/onem2m-examples/onem2m-example-8b.py).
``` py
# Example 8b: Making Requests

from openmtc_onem2m.client.http import OneM2MHTTPClient
from openmtc_onem2m.transport import OneM2MRequest

# create a OneM2MHTTPClient object
client = OneM2MHTTPClient("http://localhost:8000", False)

# create a OneM2MRequest object
onem2m_request = OneM2MRequest("retrieve", to="onem2m")
# send the OneM2MRequest to the CSE
promise = client.send_onem2m_request(onem2m_request)
# reteive the OneM2MResponse from the returned promise
onem2m_response = promise.get()

print onem2m_response.to
#>>> onem2m
print onem2m_response.response_status_code
#>>> STATUS(numeric_code=2000, description='OK', http_status_code=200)
print onem2m_response.content
#>>> CSEBase(path='None', id='cb0')
```

**Note:** This example (and most of the following ones) will only work
as shown, if a `gateway` instance is running in the background of the
localhost. This can be launched by running the
`openmtc-open-source/openmtc-gevent/run_gateway` script.

To create a resource on the CSE, we first create the desired resource
object and then send a create `OneM2MRequest`.

In the following example, we will add the optional pararmeter
`resourceName="MYAPP"` to the creation of the AE in order to
facilitate the retrieval of this AE in the browser. After execution of
the example (and the condition to have running CSE on the localhost)
the created AE on the CSE should be retrievable at URL
`http://localhost:8000/onem2m/MYAPP` in a browser on the
localhost. Further, we add the mandatory parameter
`requestReachability=False` which states, that the created AE should
have no server capability and therefore no reachability for other
instances.

For a `create` `OneM2MRequest`, there are two additional parameters:
`ty=AE` indicates that the resource that should be created on the CSE
is of type AE (ApplicationEntity). The statement `pc=my_app` specifies
what resource should be created on the CSE. In this case, it is the AE
created previously.

This file can be found [here](./training/onem2m-examples/onem2m-example-10.py).
``` py
# Example 10: Create a resource

from openmtc_onem2m.model import AE
from openmtc_onem2m.client.http import OneM2MHTTPClient
from openmtc_onem2m.transport import OneM2MRequest

# create a OneM2MHTTPClient object
client = OneM2MHTTPClient("http://localhost:8000", False)

# create a resource to be created on the CSE
# resourceName: (optional) for easy check in browser
# requestReachability: (mandatory) for servercapability of the AE
my_app = AE(App_ID="myApp", 
            labels=["keyword1", "keyword2"], 
            resourceName="MYAPP", 
            requestReachability=False)

# create a OneM2MRequest object of type 'create'
# ty: resource_type of the created resource
# pc: Resource content to be transferred
onem2m_request = OneM2MRequest("create", to="onem2m", ty=AE, pc=my_app)

# send the 'create' OneM2MRequest to the CSE
promise = client.send_onem2m_request(onem2m_request)

# reteive the OneM2MResponse from the returned promise
onem2m_response = promise.get()

print onem2m_response.to
#>>> onem2m
print onem2m_response.response_status_code
#>>> STATUS(numeric_code=2001, description='CREATED', http_status_code=201)
print onem2m_response.content
#>>> AE(path='None', id='ae0')
print onem2m_response.content.App_ID
#>>> myApp
print onem2m_response.content.labels
#>>> [u'keyword1', u'keyword2']
```

**Note:** If this example throws a `OneM2MErrorResponse` with
`response_status_code: STATUS(numeric_code=4015,
description='CONFLICT', http_status_code=409)`, then the
`resourceName` might already be registered at the CSE. Try to alter
the `resourceName`. ResourceNames need to be unique on the
CSE. Alternatively, the running CSE process can be terminated and
restarted. This avoids the need to change the `resourceName`.

**Note:** At this point the application object has been created in the
CSE's resource tree. However, the original object we created in our
program (`my_application`) has not been altered in any
way. Specifically, it does not contain any attributes that may have
been set or altered by the CSE, nor has its `path` property been set.

If we want to continue working with the application object it is good
practice to retrieve the object again through the resourceName.

This file can be found [here](./training/onem2m-examples/onem2m-example-11a.py).
``` py
# Example 11a: Create a resource (continued)

from openmtc_onem2m.model import AE
from openmtc_onem2m.client.http import OneM2MHTTPClient
from openmtc_onem2m.transport import OneM2MRequest

client = OneM2MHTTPClient("http://localhost:8000", False)

my_app = AE(App_ID="myApp", 
            labels=["keyword1", "keyword2"], 
            resourceName="MYAPP1", 
            requestReachability=False)

onem2m_request = OneM2MRequest("create", to="onem2m", ty=AE, pc=my_app)

promise = client.send_onem2m_request(onem2m_request)

onem2m_response = promise.get()

print onem2m_response.response_status_code
#>>> STATUS(numeric_code=2001, description='CREATED', http_status_code=201)

# Build path to retieve from
path = "onem2m/" + onem2m_response.content.resourceName
print path
#>>> onem2m/MYAPP

# Retrieve the AE from the CSE
onem2m_request = OneM2MRequest("retrieve", to=path)
promise = client.send_onem2m_request(onem2m_request)
onem2m_response = promise.get()

print onem2m_response.response_status_code
#>>> STATUS(numeric_code=2000, description='OK', http_status_code=200)
print onem2m_response.content
#>>> AE(path='None', id='ae0')

# Set the local AE to the retrieved content
my_app = None
my_app = onem2m_response.content

print my_app.App_ID
#>>> myApp
print my_app.resourceName
#>>> MYAPP
print my_app.labels
#>>> [u'keyword1', u'keyword2']
```

**Note:** Again, if this example throws a `OneM2MErrorResponse` with
`response_status_code: STATUS(numeric_code=4015,
description='CONFLICT', http_status_code=409)`, then the
`resourceName` might already be registered at the CSE. Try to alter
the `resourceName`. Alternatively, the running CSE process can be
terminated and restarted. This avoids the need to change the
`resourceName`.

The following example showcases how to update some fields using
`OneM2MRequest` `update`.

This file can be found [here](./training/onem2m-examples/onem2m-example-11b.py).
``` py
# Example 11b: Updating a resource using OneM2MRequest Update

from openmtc_onem2m.model import AE
from openmtc_onem2m.client.http import OneM2MHTTPClient
from openmtc_onem2m.transport import OneM2MRequest

client = OneM2MHTTPClient("http://localhost:8000", False)

my_app = AE(App_ID="myApp", 
            labels=["keyword1", "keyword2"], 
            resourceName="MYAPP2", 
            requestReachability=False)

# Create the AE 'my_app' at the CSE
onem2m_request = OneM2MRequest("create", to="onem2m", ty=AE, pc=my_app)
promise = client.send_onem2m_request(onem2m_request)
onem2m_response = promise.get()
print onem2m_response.content.labels
#>>> [u'keyword1', u'keyword2']

# Retrieve the AE from the CSE and check the labels
path = "onem2m/" + onem2m_response.content.resourceName
onem2m_request = OneM2MRequest("retrieve", to=path)
promise = client.send_onem2m_request(onem2m_request)
onem2m_response = promise.get()
print onem2m_response.content.labels
#>>> [u'keyword1', u'keyword2']

# Update the changes labels in the remote resource
# Therefore a temporay AE object is needed
# This temporary AE object should ONLY contian the fields that need to be updated 
tmp_app = AE(labels=["foo", "bar", "coffee"])
onem2m_request = OneM2MRequest("update", to=path, pc=tmp_app)
promise = client.send_onem2m_request(onem2m_request)
onem2m_response = promise.get()
print onem2m_response.content.labels
#>>> [u'foo', u'bar', u'coffee']

# Set the local AE to the retrieved content
my_app = None
my_app = onem2m_response.content
print my_app.labels
#>>> [u'foo', u'bar', u'coffee']
```


### Error Handling

The examples above have so far omitted error handling for the sake of
clarity and brevity. Obviously however, many things can go wrong at
various stages of processing and these cases need to be dealt with.

Any errors that are returned from the CSE will be represented in the
form of an `OneM2MErrorResponse` instance. As stated before, the
`OneM2MErrorResponse` class derives from `Exception`. Consequently,
`OneM2MErrorResponse` objects are not returned from the method,
instead they are raised as exceptions.

In addition, it is possible that the CSE could not be contacted at all
in the first place. In this case, an instance of
`openmtc.exc.ConnectionFailed` will be raised, which also derives from
`Exception`.

**Note:** This implies that whenever one of the client methods returns
normally, we can be sure that the operation has succeeded and continue
working with the result as planned without further inspecting the
result's status. This allows a very convenient and pythonic separation
of error and result handling.

With this in mind we can extend *Example 8b* by simply enclosing the
invocation of the client method in a `try`/`except`/`else` block.

This file can be found [here](./training/onem2m-examples/onem2m-example-12a.py).
``` py
# Example 12a: Making Requests with error handling

from openmtc_onem2m.client.http import OneM2MHTTPClient
from openmtc_onem2m.transport import OneM2MRequest, OneM2MErrorResponse
from openmtc.exc import OpenMTCError

client = OneM2MHTTPClient("http://localhost:8000", False)

try:
    onem2m_request = OneM2MRequest("retrieve", to="onem2m")
    promise = client.send_onem2m_request(onem2m_request)
    onem2m_response = promise.get()
except OneM2MErrorResponse as e:
    print "CSE reported an error:", e
    raise
except OpenMTCError as e:
    print "Failed to reach the CSE:", e
    raise
else:
    pass

# no exception was raised, the method returned normally.
print onem2m_response.to
#>>> onem2m
print onem2m_response.response_status_code
#>>> STATUS(numeric_code=2000, description='OK', http_status_code=200)
print onem2m_response.content
#>>> CSEBase(path='None', id='cb0')
```


### Forwarding

OpenMTC will automatically handle forwarding of a OneM2MRequest if it
is referring to a different CSE than the one the client is connected
to. Forwarding in OneM2M is based on CSE-IDs whereas the ETSI M2M
equivalent Retargeting is based on IPs.

Lets suppose that a gateway is availabe at `localhost:8000` and has
the CSE-ID `mn-cse-1`. Then, its backend is available at
`localhost:18000` and has the CSE-ID `in-cse-1`.

Due to forwarding, the following requests will have the same results:

* `localhost:8000/onem2m` and `localhost:18000/~/mn-cse-1/onem2m`
* `localhost:8000/onem2m` and `localhost:8000/~/mn-cse-1/onem2m"`
* `localhost:8000/~/in-cse-1/onem2m` and `localhost:18000/onem2m`

The following exaple illustrates this:

This file can be found [here](./training/onem2m-examples/onem2m-example-12b.py).
``` py
# Example 12b: Forwarding

from openmtc_onem2m.client.http import OneM2MHTTPClient
from openmtc_onem2m.transport import OneM2MRequest

client = OneM2MHTTPClient("http://localhost:8000", False)

onem2m_request = OneM2MRequest("retrieve", to="onem2m")
onem2m_response = client.send_onem2m_request(onem2m_request).get()
print "---> Request to: http://localhost:8000" + "/" + onem2m_request.to
print onem2m_response.to
#>>> onem2m
print onem2m_response.response_status_code
#>>> STATUS(numeric_code=2000, description='OK', http_status_code=200)
print onem2m_response.content
#>>> CSEBase(path='None', id='cb0')

onem2m_request = OneM2MRequest("retrieve", to="~/mn-cse-1/onem2m")
onem2m_response = client.send_onem2m_request(onem2m_request).get()
print "---> Request to: http://localhost:8000" + "/" + onem2m_request.to
print onem2m_response.to
#>>> ~/mn-cse-1/onem2m
print onem2m_response.response_status_code
#>>> STATUS(numeric_code=2000, description='OK', http_status_code=200)
print onem2m_response.content
#>>> CSEBase(path='None', id='cb0')

client.port = 18000
onem2m_request = OneM2MRequest("retrieve", to="~/mn-cse-1/onem2m")
onem2m_response = client.send_onem2m_request(onem2m_request).get()
print "---> Request to: http://localhost:18000" + "/" + onem2m_request.to
print onem2m_response.to
#>>> ~/mn-cse-1/onem2m
print onem2m_response.response_status_code
#>>> STATUS(numeric_code=2000, description='OK', http_status_code=200)
print onem2m_response.content
#>>> CSEBase(path='None', id='cb0')
```

