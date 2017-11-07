#!/bin/sh

for d in ../futile/src ../common/openmtc/lib ../common/*/src ../serializers/*/src ../openmtc-app/src ; do
    _SRC_PATH="${d}"
    _READLINK_PATH="$(readlink ${_SRC_PATH})"
    PYTHONPATH=${PYTHONPATH}:$(pwd)/${_READLINK_PATH:-${_SRC_PATH}}
done

echo PYTHONPATH: ${PYTHONPATH}

export PYTHONPATH
