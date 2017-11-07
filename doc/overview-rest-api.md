# Overview REST API
 
## Introduction

This document gives a quick overview on how the external interfaces of
an *OpenMTC Gateway* can be used to create new resources within
an OpenMTC M2M system.  Based on the same external interface, it is
also shown how data can be retrieved from it. In general, all
functionality of a Gateway is exposed via the resource tree. This resource tree is accessible in a *RESTful* manner through
a HTTP interface. Thus, all examples in this document
can be performed with standard off-the-shelve HTTP client software
(curl, postman).

### HTTP Requests and Responses as Given in this Text

Within the step-by-step guide further below in this text, each HTTP
request and response are shown as their actual textual representation
-- unimportant details are omitted.

A short (theoretical) example will help you to understand this.  

**Request**
```
GET /some-example  HTTP/1.1
Host: localhost:8000
```

This example, describes a `GET` request, based on HTTP/1.1, which is
send to the host `localhost` at port `8000` and requests the resource
`/some-example`.

Another example, outlines how a `POST` request will look like.  Here,
an HTTP/1.1-based `POST` request will send the below specified JSON to
host `localhost` at port `8000` and requests to send it to resource
`/some-example`.  

**Request**

```
POST /some-example  HTTP/1.1
Host: localhost:8000
Content-Type: application/vnd.onem2m-res+json

{
  "some-data": "some-string-value"
}
```

### Example usage of HTTP clients

To be able to send the (theoretical) requests, given in the last
subsection, [cURL](https://curl.haxx.se/) may be used, which is a
command line program usable as HTTP client.

#### Retrieve a resource

```sh
curl -X GET localhost:8000/some-example
```

Here, the request command `GET` is send to localhost at port 8000,
requesting the resource "/some-example".  If data was successfully
retrieved, by this, it will be printed to STDOUT.

#### Push plain text data to a resource

```sh
curl -X POST localhost:8000/some-example \
 -H "Content-Type: application/vnd.onem2m-res+json" \
 -d '{ "some-data": "some-string-value" }'
```

Here, plain text (JSON) data (`-d`) is pushed to the resource
"/some-example", by using the HTTP request command `POST`.  Note that
the content type of the given data is specified via an additional HTTP
header (`-H`).  If the provided JSON was successfully uploaded, a new
content instance for this resource is provided.

#### Push base64 encoded data to a resource

Sometimes, it is needed to encode given data -- for example a JSON --
as a base64 string.  This can be done, at the command line, in the
following way:

```sh
echo '{ "some-data": "some-string-value" }' | base64
```

Which will return following base64 encoded string:

`eyAic29tZS1kYXRhIjogInNvbWUtc3RyaW5nLXZhbHVlIiB9Cg==`

Pushing the same data as from the last subsection as a base64 encoded
string will work like this:

```sh
curl -X POST localhost:8000/some-example \
 -H "Content-Type: application/vnd.onem2m-res+json" \
 -d 'eyAic29tZS1kYXRhIjogInNvbWUtc3RyaW5nLXZhbHVlIiB9Cg=='
```

If you need to do this as a single line command, just combine the two
last commands in the following way:

```sh
curl -X POST localhost:8000/some-example \
 -H "Content-Type: application/vnd.onem2m-res+json" \
 -d $(echo '{ "some-data": "some-string-value" }' | base64)
```

### A step-by-step Guide for OpenMTC's Rest API

**Step 1:** Create a new application entity within a given OpenMTC
Gateway: [AE creation](#create-an-application-resource).  
  
**Step 2:** Check the stored information about your newly created
application entity:
[Application Resource Retrieval](#retrieve-information-of-a-specific-application-resource).  
  
**Step 3:** To be able to structure information provided by your newly
created application entity, you should create a new oneM2M container
within the hierarchy of your application: [Create an Application Resource](#create-an-application-resource).  
  
**Step 4:** Check whether your newly created oneM2M container was
created correctly: [Retrieve Information of a Specific Container Resource](#retrieve-information-of-a-specific-container-resource).  
  
**Step 5:** Push new data (content instance) to your newly created
application container.  If your new content instance is supposed to
store plain text value:
[Create plain text value Content Instance](#create-a-plain-text-content-instance). If your new content instance is supposed to store
base64-encoded values:
[Create base64-encoded Content Instance](#create-a-base64-encoded-content-instance).  
  
**Step 6:** Finally, check whether your data (content instance) was
pushed correctly:
[Retrieve Latest Content Instances](#retrieve-latest-content-instances).  

## Create an Application Resource

**Request**

```
POST /onem2m
Host: localhost:8000
Content-Type: application/vnd.onem2m-res+json

{
  "m2m:ae": {
    "rn": "EXAMPLE_APP_NAME",
	"api": "placeholder",
	"rr": "TRUE"
  }
}
```

**Response**

```json
{
  "m2m:ae": {
    "ri":"ae1",
    "nl":"dummy",
    "rr":true,
    "ty":2,
    "et":"2017-03-02T16:46:13.350093+00:00",
    "lt":"2017-03-02T16:12:53.350093+00:00",
    "api":"placeholder",
    "aei":"C1",
    "pi":"cb0",
    "rn":"EXAMPLE_APP_NAME",
    "ct":"2017-03-02T16:12:53.350093+00:00"
  }
}
```

## Retrieve Information of a Specific Application Resource

**Request**

```
GET /onem2m/EXAMPLE_APP_NAME  HTTP/1.1
Host: localhost:8000
```

**Response**

```json
{
  "m2m:ae": {
    "ri":"ae0",
    "nl":"dummy",
    "rr":true,
    "ty":2,
    "et":"2017-03-02T16:54:10.097197+00:00",
    "ch": [{
        "typ":3,"nm":"EXAMPLE_CONTAINER_NAME",
        "val":"cnt0"
    }],
    "lt":"2017-03-02T16:20:50.097197+00:00",
    "api":"placeholder",
    "aei":"C0",
    "pi":"cb0",
    "rn":"EXAMPLE_APP_NAME",
    "ct":"2017-03-02T16:20:50.097197+00:00"
  }
}
```

## Create a Container Resource

**Request**

```
POST /  HTTP/1.1
Host: localhost:8000
Content-Type: application/vnd.onem2m-res+json

{ "m2m:cnt": {
  "rn": "EXAMPLE_CONTAINER_NAME"
  }
}
```

**Response**

```json
{
  "m2m:cnt": {
    "cr":"nobody",
    "et":"2017-03-02T16:54:19.216702+00:00",
    "ty":3,
    "lt":"2017-03-02T16:20:59.216702+00:00",
    "rn":"EXAMPLE_CONTAINER_NAME",
    "ct":"2017-03-02T16:20:59.216702+00:00",
    "ri":"cnt0",
    "cni":0,
    "cbs":0,
    "pi":"ae0",
    "st":"0"
  }
}
```

## Retrieve Information of a Specific Container Resource

**Request**

```
GET /onem2m/EXAMPLE_APP_NAME/EXAMPLE_CONTAINER_NAME  HTTP/1.1
Host: localhost:8000
```

**Response**

```json
{
  "m2m:cnt": {
    "cr":"nobody",
    "et":"2017-03-02T16:54:19.216702+00:00",
    "ty":3,
    "lt":"2017-03-02T16:20:59.216702+00:00",
    "rn":"EXAMPLE_CONTAINER_NAME",
    "ct":"2017-03-02T16:20:59.216702+00:00",
    "ri":"cnt0",
    "cni":0,
    "cbs":0,
    "pi":"ae0",
    "st":"0"
  }
}
```



## Create a Plain-Text Content Instance

**Request**

```
POST /onem2m/EXAMPLE_APP_NAME/EXAMPLE_CONTAINER_NAME/  HTTP/1.1
Host: localhost:8000
Content-Type: application/vnd.onem2m-res+json

{
  "m2m:cin": {
    "con": "EXAMPLE_VALUE",
	"cnf": "text/plain:0"
  }
}
```

**Response**

```json
{
  "m2m:cin": {
    "ri":"cin1",
    "ty":4,
    "st":"0",
    "cnf":"text/plain:0",
    "lt":"2017-03-02T16:37:23.963247+00:00",
    "et":"2017-03-02T17:10:43.963247+00:00",
    "cs":13,
    "pi":"cnt0",
    "rn":"contentInstance-v2HDJeljran3jxPX",
    "con":"EXAMPLE_VALUE",
    "ct":"2017-03-02T16:37:23.963247+00:00"
  }
}
```

## Create a Base64-Encode Content Instance

 For this subsection it is assumed that data represented as JSON will
 used to create a new content instance.  Therefore, following
 example data:
 ```
 {
   "foo": 42, "bar": 42
 }
 ```
 needs to be trans-coded to its base64 string:
 ```
 eyJmb28iOiA0MiwgImJhciI6IDQyfQo=
 ```
 
 To be able to execute the trans-coding, be reminded of
 subsection
 [Push base64 encoded data to a resource](#push-base64-encoded-data-to-a-resource).   
 
**Request**

```
POST /onem2m/EXAMPLE_APP_NAME/EXAMPLE_CONTAINER_NAME/  HTTP/1.1
Host: localhost:8000
Content-Type: application/vnd.onem2m-res+json

{
  "m2m:cin": {
  "con": "eyJmb28iOiA0MiwgImJhciI6IDQyfQo=",
  "cnf": "application/json:1"
  }
}
```

**Response**

```json
{
  "m2m:cin": {
    "ri":"cin2",
    "ty":4,
    "st":"0",
    "cnf":"application/json:1",
    "lt":"2017-03-02T16:41:02.060806+00:00",
    "et":"2017-03-02T17:14:22.060806+00:00",
    "cs":32,
    "pi":"cnt0",
    "rn":"contentInstance-ccUmIDHZ2jvtUWyQ",
    "con":"eyJmb28iOiA0MiwgImJhciI6IDQyfQo=",
    "ct":"2017-03-02T16:41:02.060806+00:00"
  }
}
```

## Retrieve Latest Content Instances

**Request**

```
GET /onem2m/EXAMPLE_APP_NAME/EXAMPLE_CONTAINER_NAME/latest  HTTP/1.1
Host: localhost:8000
```

**Response**

```json
{
  "m2m:cin": {
    "ri":"cin2",
    "ty":4,
    "st":"0",
    "cnf":"application/json:1",
    "lt":"2017-03-02T16:41:02.060806+00:00",
    "et":"2017-03-02T17:14:22.060806+00:00",
    "cs":32,
    "pi":"cnt0",
    "rn":"contentInstance-ccUmIDHZ2jvtUWyQ",
    "con":"eyJmb28iOiA0MiwgImJhciI6IDQyfQo=",
    "ct":"2017-03-02T16:41:02.060806+00:00"
  }
}
```

## Reference: Short Resource names and Resource types

 [Resource names and types](reference-doc/resource-names-and-types.md) provides a
 reference of how names of resources are mapped to their short names
 but also provides a table that reveals the numerical representation
 of resource types.

