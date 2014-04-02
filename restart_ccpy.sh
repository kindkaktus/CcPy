#!/bin/bash

[ -f /var/run/ccpyd.pid ] && kill `cat /var/run/ccpyd.pid`
./ccpyd.py $1
