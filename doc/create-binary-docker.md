# Create binary docker images Script

This documentation explains the `create-binary-docker` script in the main folder
and shows the usage.

## Description

`create-binary-docker` is used to build Docker container images for
all available OpenMTC components.  It can be used for cross-builds
too.

## Usage

The script shall be called from the command line:

```bash
Usage: create-binary-docker [OPTS] <module_name>
  OPTS:
    -a|--arch <ARCH>           Choose architecture: amd64|arm
    -p|--prefix <Name Prefix>  Choose Docker image name prefix
    -e|--export                Export the Docker image to a file, after build

    -h|--help                  Show this help
    -v|--version               Show version information

  module_name:
    gateway | backend
```

## Examples

Assuming an AMD64-based host machine, building the OpenMTC Gateway
Container image can be achieved by following:

```bash
./create-binary-docker gateway
```

Cross building the same component for ARM (e.g. the Raspberry Pi),
use:

```bash
./create-binary-docker -a arm gateway
```

Any successfully built Docker image will be available in the machine's
local Docker repository.

To be able to adjust the Docker image name for the OpenMTC Gateway,
the common prefix can be configured, like this:

```bash
./create-binary-docker -p openmtc-testv1 gateway
```

After the built succeeded, a Docker image of the following name will
be available in the host's Docker repository:
`openmtc-testv1/gateway`.

It is also possible to automatically save the created Docker to the
file system, using the `--export` flag.  This will save the Docker
image into `dist/docker` within the OpenMTC git repository.
