#! /bin/sh

set -e

cd `dirname "$0"`

dfu-programmer atmega32u4 erase --force
dfu-programmer atmega32u4 flash CUL_V3.hex
dfu-programmer atmega32u4 reset
