#!/bin/bash

function stop_ccpy()
{
    if [ -f /var/run/ccpyd.pid ] ; then
        local pid=$(cat /var/run/ccpyd.pid)
        if kill -0 ${pid} ; then
            kill ${pid}
            sleep 0.5
            if kill -0 ${pid} > /dev/null 2>&1; then
                kill -9 ${pid}
            fi
        fi
    fi
}

function start_ccpy()
{
    cd $( dirname "${BASH_SOURCE[0]}" )
    ./ccpyd.py $1
}

stop_ccpy
start_ccpy $1
