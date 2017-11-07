#!/usr/bin/env sh

cd ../common
. ../common/prep-env.sh
cd ../apps

_SRC_PATH="../openmtc-app/src"
_READLINK_PATH="$(readlink ${_SRC_PATH})"
PYTHONPATH=${PYTHONPATH}:$(pwd)/${_READLINK_PATH:-${_SRC_PATH}}

echo PYTHONPATH: ${PYTHONPATH}

export PYTHONPATH
