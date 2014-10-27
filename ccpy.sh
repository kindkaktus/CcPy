#!/bin/bash

# Startup script for ccpy
# Usage:
# ./ccpy.sh [--skip-update] - will subsequently perform the following actions:
#                           1. stop ccpy if it is already running recursively killing all children spawned by ccpy
#                           2. unless --skip-update option is given, will update ccpy working copy if either .git or .svn directory is detected
#                           3. starts ccpy
# ./ccpy.sh stop - stop ccpy recursively killing all children spawned by ccpy

function usage()
{
    echo "Usage: "
    echo "./$0 [--skip-update]"
    echo "./$0 stop"
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

function update_ccpy_wc()
{
    pushd $( dirname "${BASH_SOURCE[0]}" ) > /dev/null 
    if [ -d ".svn" ]; then
        svn up
    elif [ -d ".git" ]; then
        git pull
    fi
    popd > /dev/null
}

function start_ccpy()
{
    pushd $( dirname "${BASH_SOURCE[0]}" ) > /dev/null
    ./ccpyd.py
    popd > /dev/null
}

if [ $# -eq 0 ]; then
    stop_ccpy
    update_ccpy_wc
    start_ccpy
elif [ $# -eq 1 ]; then
    if [ x"$1" == x"stop" ]; then
        stop_ccpy
    elif [ x"$1" == x"--skip-update" ]; then
        stop_ccpy
        start_ccpy
    else
        usage
        exit 1
    fi
else
    usage
    exit 1
fi
