#!/bin/bash

[ -f /var/run/ccpyd.pid ] && kill `cat /var/run/ccpyd.pid`
python ccpyd.py $1
