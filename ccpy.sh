#!/bin/bash

# Startup script for ccpy
# Usage:
# ./ccpy.sh - (re)start ccpy, stopping ccpy if it is already running and recursively killing all children spawned by ccpy
# ./ccpy.sh stop - stop ccpy recursively killing all children spawned by ccpy

function usage()
{
    echo "./$0 [stop]"
}

# usage _killtree <pid>
function _killtree() 
{
    local _pid=$1
    
    kill -stop ${_pid} # to prevent the process from producing more children while killing its current children
    for _child in $(pgrep -P ${_pid}); do
        _killtree ${_child}
    done
    
    kill ${_pid}
    sleep 0.1
    if kill -0 ${_pid} > /dev/null 2>&1; then
        kill -9 ${_pid}
    fi
}

function stop_ccpy()
{
    if [ -f /var/run/ccpyd.pid ] ; then
        local _pid=$(cat /var/run/ccpyd.pid)
        _killtree ${_pid}
    fi
}

function start_ccpy()
{
    cd $( dirname "${BASH_SOURCE[0]}" )
    ./ccpyd.py
}

if [ $# -eq 0 ]; then
    stop_ccpy
    start_ccpy
elif [ $# -eq 1 ]; then
    if [ x"$1" != x"stop" ]; then
        usage
        exit 1
    fi
    stop_ccpy
else
    usage
    exit 1
fi
