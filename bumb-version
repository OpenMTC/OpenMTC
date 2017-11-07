#!/bin/bash

VERSION=${1}

if ! [[ "${VERSION}" =~ ^[0-9]+\.[0-9]+(\.[0-9]+)?$ ]]; then
    echo "Wrong version number! Only x.y or x.y.z is allowed."
    exit 1
fi

SETUPS=( gevent-all sdk gevent-all-with-abs-gip arduinogip cul868gip roomui
    testgip zigbeegip )

for setup in "${SETUPS[@]}"; do
    sed -i -re 's/(^\W*SETUP_VERSION\W*=\W*")[0-9]+\.[0-9]+(\.[0-9]+)?"/\1'${VERSION}'"/' setup-${setup}.py
done

