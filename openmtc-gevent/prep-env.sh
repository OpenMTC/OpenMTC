#!/usr/bin/env bash

. ../common/prep-env.sh

for d in src ../server/*/src ; do
    _SRC_PATH="${d}"
    _READLINK_PATH="$(readlink ${_SRC_PATH})"
    PYTHONPATH=${PYTHONPATH}:$(pwd)/${_READLINK_PATH:-${_SRC_PATH}}
done

echo PYTHONPATH: ${PYTHONPATH}

export PYTHONPATH
