#!/bin/bash

cd $( dirname "${BASH_SOURCE[0]}" )
[ -f /var/run/ccpyd.pid ] && kill `cat /var/run/ccpyd.pid`
./ccpyd.py $1
