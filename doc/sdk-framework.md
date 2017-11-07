# SDK - Using the Application Framework


## Introduction

To simplify application development, the OpenMTC SDK provides an application framework for writing oneM2M compliant applications with minimal effort.

This framework allows specifying application parameters in a declarative way and is furthermore fully event driven.

The OpenMTC application framework resides in the `openmtc_app.onem2m` module.


## Application Basics

To write an application a conventional Python class has to be implemented. There are only two restrictions on this class:

- It must derive from the provided base class `openmtc_app.onem2m.XAE`
- It must override the \_on\_register method.

The overall flow of operations is simple. Upon startup, the framework will register the application with the CSE and once that has successfully happened, call the `_on_register` method of the application. This is the entry point where the application can start actually doing things. This includes:

- Creating some containers
- Creating more applications
- Subscribe for data from the CSE
- Setup any device specific communication

Upon shutdown, the application itself and any resources it has created will automatically be deleted by the framework.

**Note:** The framework also automatically handles expiration time updates for all resources that have been created.


### Properties

The following properties are available on objects of type `openmtc_app.onem2m.XAE`:

- `application` - the `Application` object that represents this application in the CSE's resource tree.
- `client` - an instance of `openmtc_onem2m.client.http.OneM2MHTTPClient` connected to the CSE
- `logger` - a `logging.Logger` object. Please refer to the Python [logging documentation](https://docs.python.org/2/library/logging.html) for details.


### Methods

The following methods are available on an `openmtc_app.onem2m.XAE` object:

- `get_application(application, path)`  
  - used to retrieve an Application resource.
  - `application` old app instance or appId
  - `path` (optional) path in the resource tree
  - Returns the `Application` object that was retrieved

- `create_application(application, path)`  
  - used to create a new Application resource in the CSE's resource tree, besides the one that has been registered at startup.
  - `application` Application instance or appId as str
  - `path` (optional) path in the resource tree at which the new application should be created.
  - Returns the `Application` object that represents the application that has been created at the CSE.

- `discover(path, filter_criteria, unstructured)`  
  - used to discover resources.
  - `path` the target resource/path parenting the Container. e.g. the remote CSE
  - `filter_criteria` (optional) FilterCriteria for the for the discovery
  - `unstructured` (optional) set `discovery_result_type`
  - Returns the content of the discovery

- `create_container(target, container, labels, max_nr_of_instances)`  
  - used to create a Container resource as children of an application.
  - `target` the target resource/path parenting the Container
  - `container` the Container resource or a valid container ID
  - `labels` (optional) the container's searchStrings
  - `max_nr_of_instances` the container's maximum number of instances (0=unlimited)
  - Returns the container that was created

- `get_resource(path, app_local)`  
  - used to retrieve a resource
  - `path` is the path to the resource
  - `app_local` if set to `True` path will be appended to the path of the Application

- `push_content(container, content, fmt, text)`  
  - used to push actual data into a container. Therefore creates a ContentInstance resource in the given container, wrapping the content. Defaults to serialising the content as JSON and base64 encodes it. Will attempt to create the container, if not found.
  - `container` container at which the content should be created
  - `content` the actual data. Currently, only Python `string`, `list` and `dict` objects are supported.
  - `fmt` (optional)
  - `text` (optional)
  - Returns the created ContentInstance resource

- `get_content(container)`  
  - used to retrieve the latest ContentInstance of a Container.
  - `container` container to retrieve content from
  - Returns the latest ContentInstance of the specified Container

- `add_container_subscription(container, handler, data_handler, filter_criteria)`  
  - used to create a Subscription to the ContentInstances of the given Container.
  - `container` the Container or it's path
  - `handler` reference of the notification handling function
  - `data_handler` (optional) reference of the function parsing/decoding the data
  - `filter_criteria` (optional) FilterCriteria for the subscription

- `emit(message, event)`  
  - publish data via `socket.io` to all connected clients.
  - `message` is the data to be pushed.
  - `event` specifies the `socket.io` event channel name.


### Application Shutdown

Upon shutdown, the `shutdown` method will be called with no arguments. Implementations may override it to implement their own clean-up facilities.

After the `shutdown` method has finished, all resources created by the application framework, including the application itself, will be removed.


## Writing Applications

This example shows how a simple device application might be written. The goal of this application is to first register itself with the CSE and then continuously read sensor data from some hardware device and push it to the CSE.

Note that the actual sensor reading parts of the application is left out - it is represented simply by an imagined `read_sensor_data` method. This example will solely focus on the OpenMTC SDK aspects of the application.


### A minimal Application

A minimal application is simply a class that extends the application base class `openmtc_app.onem2m.XAE` and overrides the `_on_register` method. Such an application could look like this.

This file can be found [here](./training/onem2m-examples/onem2m-example-13.py).
``` py
# Example 13: Minimal application

from openmtc_app.onem2m import XAE

class MyAE(XAE):
    # when this is called the application is registered 
    # and can start doing something
    def _on_register(self):
        pass
```

Upon running, this application would be registered under the name MyAE.


### Running the Application

Applications are run by encapsulating them in a so-called runner. These runners provide external functions such as maintaining a server component for receiving notifications.

Currently, two runner implementations are provided, both built upon the popular [Flask](http://flask.pocoo.org/) framework. These are:

- `openmtc_app.flask_runner.SimpleFlaskRunner`
- `openmtc_app.flask_runner.FlaskRunner`

The difference between these two is that `FlaskRunner` provides some additional functionality, which is not included in `SimpleFlaskRunner`. This is mainly related to web-browser support/integration:

- `FlaskRunner` supports websocksets through the [socket.io](http://socket.io/) abstraction layer.
- `FlaskRunner` is more scalable.

However, in certain cases the simpler implementation of `SimpleFlaskRunner` can have advantages as well:

- `FlaskRunner` is built upon the [gevent](http://www.gevent.org/) asynchronous I/O framework. While this provides for a very scalable solution, it might produce undesirable results and strange behaviour when applications implement their own I/O mechanisms, e.g. for communicating with a device. In contrast `SimpleFlaskRunner` will not exhibit these pitfalls.
- While `FlaskRunner` provides a more scalable solution when a lot of I/O happens, the resource consumption of `SimpleFlaskRunner` will be less in cases where only few requests are performed - especially when requests are performed strictly sequential.

**Hint:** Both implementations will automatically serve static www content from a `static` directory in the application's root directory.

To invoke a runner, we have to:

1. instantiate our application class
2. instantiate the runner class, passing in the application object in the runner's constructor
3. invoke the runner's `run` method, passing the URI of the CSE we want to communicate with

The following example shows how this is done:

This file can be found [here](./training/onem2m-examples/onem2m-example-14a.py).
``` py
# Example 14a: Invoking a FlaskRunner

from openmtc_app.onem2m import XAE
from openmtc_app.flask_runner import FlaskRunner

class MyAE(XAE):
    def _on_register(self):
        pass

app_instance = MyAE()
runner = FlaskRunner(app_instance)
runner.run("http://localhost:8000")
```

**Note:** This example (and most of the following ones) will only work as shown, if a `gateway` instance is running in the background of the localhost. This can be launched by running the `openmtc-open-source/openmtc-gevent/run_gateway` script.

At this point the runner will start the app which results in the app being registered at the CSE. Once that has happened, the `_on_register` method will be called upon which our application can actually start its operation.

The above example will register the application under its default application ID, which in this case, is derived from the name of the application's class: `MyAE`. In some cases - for example when multiple instances of the same application class are run against the same CSE - it may be desirable to override the default application ID. This can be achieved simply by setting the `name` parameter when instantiating the application class.

This file can be found [here](./training/onem2m-examples/onem2m-example-14b.py).
``` py
# Example 14b: Invoking a FlaskRunner with custom name

from openmtc_app.onem2m import XAE
from openmtc_app.flask_runner import FlaskRunner

class MyAE(XAE):
    def _on_register(self):
        pass

app_instance = MyAE(name="someAppName")
runner = FlaskRunner(app_instance)
runner.run("http://localhost:8000")
```

The invocation in this example tells the framework to register the application under the ID `someAppName`.


### Providing additional Information

We can provide/override some static configuration information about our application in a declarative manner. This information includes:

- `app_id` - The default application ID.
- `name` - The default application name. (default = None)
- `labels` - The default application labels.
- `default_lifetime` - The default application lifetime. (default = 3600)
- `max_nr_of_instances` - The default application maximum number of instances. (default = 3)
- `cse_base` - The default application CSE-base. (default = "onem2m")

This file can be found [here](./training/onem2m-examples/onem2m-example-15.py).
``` py
# Example 15: Running App with Static Information

from openmtc_app.onem2m import XAE

class MyAE(XAE):
    app_id = "AnotherAppID"
    labels =["keyword1", "keyword2"]
```

In the above example, the application would by default be registered under the ID `anotherAppID`. Moreover, its `labels` attribute would be set to `["keyword1", "keyword2"]`.


### Creating a Container

At this point, the next step for most if not all device applications will be to create a container to store any sensor data it reads. This is achieved by calling the `create_container` method.

This file can be found [here](./training/onem2m-examples/onem2m-example-16.py).
``` py
# Example 16: Creating a simple Container

from openmtc_app.onem2m import XAE
from openmtc_app.flask_runner import FlaskRunner

class MyAE(XAE):
    def _on_register(self):
        container = self.create_container(None, "myContainer")

app_instance = MyAE()
runner = FlaskRunner(app_instance)
runner.run("http://localhost:8000")
```

Note how we pass `None` as the first parameter to `create_container`. This implies to the framework that the container should be created as a child of the registered application (this invocation is thus equivalent to `self.create_container(self.application, "myContainer"`). We could pass different application objects in the first parameter which we would have obtained by calling `self.create_application`.

Also note how we pass a simple string object as the second parameter. This will serve as the `id` attribute of the container. The framework will internally create a `Container` object with the specified ID which will otherwise be configured with some default parameters. If we wanted to provide more details upon container creation, we would have to pass in a full container object.

This file can be found [here](./training/onem2m-examples/onem2m-example-17.py).
``` py
# Example 17: Creating a custom Container

from openmtc_app.onem2m import XAE
from openmtc_app.flask_runner import FlaskRunner
from openmtc_onem2m.model import Container

class MyAE(XAE):
    def _on_register(self):
		# create a container
        container = Container(
            resourceName = "myContainer",
            maxNrOfInstances=100,
            maxByteSize=1024 ** 3 )
        container = self.create_container(None, container)

app_instance = MyAE()
runner = FlaskRunner(app_instance)
runner.run("http://localhost:8000")
```

Here we create an explicit `Container` object which limits the size of the container to a maximum of 100 content instances and a maximum size of 3 MByte.


### Pushing Data

The final step for our application is to read data from the actual sensor hardware and forward it to the CSE as a content instance. As mentioned before, reading the data is represented by a fictional function `read_sensor_data`, the implementation of which is out of scope for the purpose of this document. In our imagination it will return a single value.

The modus operandi of this particular application is to simply read sensor data using the aforementioned function, forward it to the CSE and then wait 60 seconds before starting the whole procedure again. This will be done over and over again, thus we will encapsulate this scheme in an endless loop.

This file can be found [here](./training/onem2m-examples/onem2m-example-18.py).
``` py
# Example 18: Pushing Data

from openmtc_app.onem2m import XAE
from openmtc_app.flask_runner import FlaskRunner
from time import sleep
from somewhere import read_sensor_data

class MyAE(XAE):
    def _on_register(self):
        container = self.create_container(None, "myContainer")

	while True:
	    value = read_sensor_data() # read measurements
	    data = {"value": value}
	    self.push_content(container, data)
	    sleep(60)

app_instance = MyAE()
runner = FlaskRunner(app_instance)
runner.run("http://localhost:8000")
```

Note how the actual forwarding of the data is performed by using the `push_content` method. `push_content` takes as first argument a `Container` object that specifies the destination container of the data. The second argument is simply the data that is to be pushed in the form of a Python `dict` or `list` object. Internally, the framework will wrap this in a `ContentInstance` object and forward it to the CSE.

