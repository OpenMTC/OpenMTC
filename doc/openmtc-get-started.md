# Quick Start

In this short tutorial you will:

1. Setup an OpenMTC Gateway
2. Create an *application resource* and corresponding  *content instance* via the REST API
3. Using the REST API to get this *content instance*

First, clone the OpenMTC GitHub repository:

```sh
git clone https://github.com/OpenMTC/OpenMTC OpenMTC
```

All following commands should be executed from within the repo folder:

```sh
cd OpenMTC
```

The next steps need Docker to be installed on your system. If you need help for
the installation, follow [this guide](various.md).  
  
Build the gateway image:

```sh
./create-binary-docker gateway
```

To check if this step was successful run:

```sh
docker image ls
```

If there is an "openmtc/gateway-amd64" or "openmtc/gateway-arm" entry, the image was created successfully.

Run the gateway Docker image

```sh
docker run -d --name gateway  -p 0.0.0.0:8000:8000  \
    -e "LOGGING_LEVEL=DEBUG"    openmtc/gateway-amd64 -vv
```

or

```sh
docker run -d --name gateway  -p 0.0.0.0:8000:8000  \
    -e "LOGGING_LEVEL=DEBUG"    openmtc/gateway-arm -vv
```

Create an application resource on your gateway:

```sh
curl -X POST localhost:8000/onem2m/ -H "Content-Type: application/vnd.onem2m-res+json" \
     -d '{"m2m:ae": {"rn": "EXAMPLE_APP_NAME", "api": "placeholder", "rr": "TRUE"}}'
```

Create a container resource on your gateway:

```sh
curl -X POST localhost:8000/onem2m/EXAMPLE_APP_NAME/ -H "Content-Type: application/vnd.onem2m-res+json" \
     -d '{"m2m:cnt": {"rn": "EXAMPLE_CONTAINER_NAME"}}'
```

Create plain text content:

```sh
curl -X POST localhost:8000/onem2m/EXAMPLE_APP_NAME/EXAMPLE_CONTAINER_NAME/ \
     -H "Content-Type: application/vnd.onem2m-res+json" \
     -d '{"m2m:cin": {"con": "EXAMPLE_VALUE", "cnf": "text/plain:0"}}'
```

Get the content:

```sh
curl -X GET localhost:8000/onem2m/EXAMPLE_APP_NAME/EXAMPLE_CONTAINER_NAME/la
```

