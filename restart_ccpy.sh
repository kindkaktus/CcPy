#!/bin/bash

# usage _killtree <pid>
function _killtree() 
{
    local _pid=$1
    
    kill -stop ${_pid} # to prevent the process from producing more children while killing its current children
    for _child in $(ps -o pid --no-headers --ppid ${_pid}); do
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
    ./ccpyd.py $1
}

stop_ccpy
start_ccpy $1
