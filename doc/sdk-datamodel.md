# SDK - The Data Model


## Introduction

The OpenMTC data model represents the resources of the M2M resource tree(s) through classes and objects. All model classes derive from the base class `openmtc.model.Entity`. An Entity represents a data type defined in the respective Instances of these classes and have all the attributes of the respective type. Also, the constructors of these classes accept all relevant attributes. Attributes that are missing on construction will be initialized with default values (mostly `None` or empty lists).


### Entities vs. Resources

As mentioned above, entity classes are the base class for all model entities. A special case of an entity is a resource. Resources are "first class" objects that are represented directly in the resource tree, e.g. the OneM2M `AE` (Application Entity) resource.


### Different Data Models

At present, OpenMTC uses two different data models:

-   The OneM2M data model
-   OpenMTC's internal data model (The "unified" data model)

OpenMTC uses the unified data model for storing data in a database. Objects are mapped to / from this model to an externally visible model as needed. The reason for this is that certain resources should be visible through multiple representations. E.g. an OneM2M `AE` resource will be mapped internally as a `UnifiedApplication` resource.

**Note:** This mapping of models happens mostly transparent at database adapter level. The actual mapping is performed by the `openmtc_unified` module. Code that is specific to a certain M2M standard does not need to have knowledge about the unified data model. This means that for example the OneM2M controller classes will always only have to work with OneM2M resource types, even though those are mapped to unified types when stored in the database.


## Member Variables

Member variables on OpenMTC model objects are of three different varieties:

-   attributes - Any attributes that are directly contained within an object. Examples include `App_Id` and `appName`. Upon initializing/assigning attributes, type checking and possibly conversion is performed. Illegal values will be rejected by raising an appropriate `Exception`. Attributes can be of the following types:
    -   strings (Python type `str`). By default initialized with `None`.
    -   integers (Python type `int`). By default initialized with `None`.
    -   floating point (Python type `float`). By default initialized with `None`.
    -   dates (Python type `datetime.datetime`). By default initialized with `None`.
    -   sequences (Python type `list`). By default initialized with an empty `list` (`[]`).
    -   complex objects (Python type `dict`). By default intialized with an empty `dict` (`{}`). These are used to represent objects that are not themsekves adressable within the resource tree, e.g. permission objects.
    -   resources - The `latest` and `oldest` members of `ContentInstances` objects are represented as attributes. By default initialized with `None`.
-   collections - Any variable length collection of child resources held by an object. By default initialized with an empty collection.
-   subresources - All other children of a resource instance. By default initialized with a default-initialized object.


### Common Properties

The following properties exist on instances of model classes:

-   `path` - The path of the object. e.g. `"/onem2m/TestGIP/devices/temp02"`
-   `parent_path` (read-only) - The path of this resource's parent resource. This is derived from the resource's path. e.g. for a resource with `path="/onem2m/TestGIP/devices/temp02"` the `parent_path` would be `"/onem2m/TestGIP/devices"`
-   `name` (read-only) - the last element of the resource's path. e.g. for a resource with `path="/onem2m/TestGIP/devices/temp02"` the `name` would be `"temp02"`


### Introspection

The members of each OneM2M resource class can be inspected at run-time. For this matter, each resource class has the `attributes` property, which returns a list of all attribute members.


## Creating Objects

To create an object representing a resource from the OneM2M resource tree, one simply invokes its constructor. All classes can be instantiated without arguments. The following example creates an `AE` object that represents an OneM2M Application Entity resource.

This file can be found [here](./training/onem2m-examples/onem2m-example-1.py).
``` py
# Example 1: Creating Objects

from openmtc_onem2m.model import AE

my_app = AE()

print my_app.path
#>>> None
print my_app.App_ID
#>>> None
print my_app.parent_path
#>>> None
print my_app.labels
#>>> None
print my_app.attributes
#>>> [UnicodeAttribute(name="AE-ID", type=unicode), UnicodeAttribute(name="App-ID", type=unicode), ListAttribute(name="accessControlPolicyIDs", type=list), ListAttribute(name="announceTo", type=list), UnicodeAttribute(name="announcedAttribute", type=unicode), ListAttribute(name="childResources", type=list), DatetimeAttribute(name="creationTime", type=datetime), DatetimeAttribute(name="expirationTime", type=datetime), UnicodeAttribute(name="labels", type=unicode), DatetimeAttribute(name="lastModifiedTime", type=datetime), UnicodeAttribute(name="name", type=unicode), UnicodeAttribute(name="nodeLink", type=unicode), UnicodeAttribute(name="ontologyRef", type=unicode), ListAttribute(name="pointOfAccess", type=list)]
```

As it can be seen, all attributes of the instance have been initialized with default values. For instance, both `path` and `App_ID` were initialized with `None`, while `labels` is an empty `list`. Since `path` is `None`, `parent_path` is also `None`.

**Note:** It is important to understand that this only created the `AE` object internally in our program but not actually in the OneM2M resource tree of a CSE! No interaction with a CSE has taken place yet.


### Passing Values

We can pass values for all the attributes that are applicable to a particular resource.

This file can be found [here](./training/onem2m-examples/onem2m-example-2.py).
``` py
# Example 2: Passing Values

from openmtc_onem2m.model import AE

my_app = AE(App_ID="myApp", labels=["keyword1", "keyword2"])

print my_app.path
#>>> None
print my_app.App_ID
#>>> myApp
print my_app.parent_path
#>>> None
print my_app.labels
#>>> [u'keyword1', u'keyword2']
print my_app.attributes
#>>> [UnicodeAttribute(name="AE-ID", type=unicode), UnicodeAttribute(name="App-ID", type=unicode), ListAttribute(name="accessControlPolicyIDs", type=list), ListAttribute(name="announceTo", type=list), UnicodeAttribute(name="announcedAttribute", type=unicode), ListAttribute(name="childResources", type=list), DatetimeAttribute(name="creationTime", type=datetime), DatetimeAttribute(name="expirationTime", type=datetime), UnicodeAttribute(name="labels", type=unicode), DatetimeAttribute(name="lastModifiedTime", type=datetime), UnicodeAttribute(name="name", type=unicode), UnicodeAttribute(name="nodeLink", type=unicode), UnicodeAttribute(name="ontologyRef", type=unicode), ListAttribute(name="pointOfAccess", type=list)]
```
