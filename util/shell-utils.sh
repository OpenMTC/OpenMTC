#!/usr/bin/env bash

#set -x


# A (partial) 'realpath' replacement based on Bash functionality,
# using 'readlink' in a bare form (should be compatible with non-GNU
# 'readlink).
#
# For the original idea, see:
# http://stackoverflow.com/questions/3572030/bash-script-absolute-path-with-osx#30267480
#
get_realpath()
{
    local _READLINK="$(readlink "$1")"
    if [ -z ${_READLINK} ]; then
        echo "$1"
        return
    else
        # Note, a symbolic link could be either a link to a file or a
        # link to a path!

        # If is symbolic link to directory
        if [ -d ${_READLINK} ]; then
            pushd ${_READLINK}
            echo "${PWD}"
            popd
            return

        # If is symbolic link to a file
        else
            # Save depth of 'dirs' to be able to jump back were you
            # came from
            local _DIRSDEPTH=$(dirs | wc -l)

            local _LASTBASENAME=$(basename ${_READLINK})
            pushd $(dirname $1) >/dev/null
            _READLINK=$(readlink $(basename "$1"))
            while [ -n "${_READLINK}" ]; do
                pushd $(dirname "${_READLINK}" ) >/dev/null
                _READLINK=$(readlink $(basename "${_READLINK}"))
            done
            _REALPATH=${PWD}/$(basename "${_LASTBASENAME}")
        fi
    fi

    # Get back to where you originally came from
    while [ "${_DIRSDEPTH}" != "$(dirs | wc -l)" ]; do
        popd
    done

    echo "${_REALPATH}"
}

# echo ""
# echo "checking: $1"
# echo "get_realpath(): $(get_realpath $1)"
# echo "realpath: $(realpath $1)"

