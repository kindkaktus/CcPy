#!/bin/bash

# Startup script for ccpy
# Usage:
# ./ccpy.sh [--skip-update] [--fg] - will subsequently do the following:
#  1. unless --skip-update option is given, will update ccpy working copy if either .git or .svn directory is detected, discarding any local changes
#  2. starts ccpy in background or in foreground, when --fg argument is given
# ./ccpy.sh stop - stop ccpy recursively killing all children spawned by ccpy. It is highly recommended to reboot after stopping ccpy!

function usage()
{
    echo "Usage: "
    echo "./$0 [--skip-update] [--fg]"
    echo "./$0 stop"
    exit 1
}

# usage _killtree <pid>
function _killtree()
{
    local _pid=$1

    kill -STOP ${_pid} # to prevent the process from producing more children while killing its current children
    for _child in $(pgrep -P ${_pid}); do
        _killtree ${_child}
    done

    kill ${_pid}
    sleep 0.1
    if kill -0 ${_pid} > /dev/null 2>&1; then
        kill -9 ${_pid}
    fi
}

function is_ccpy_running()
{
    if [ -f /var/run/ccpyd.pid ] ; then
        local _pid=$(cat /var/run/ccpyd.pid)
        if kill -0 ${_pid} > /dev/null 2>&1; then
            return 0
        fi
    fi
    return 1
}

function stop_ccpy()
{
    if [ -f /var/run/ccpyd.pid ] ; then
        local _pid=$(cat /var/run/ccpyd.pid)
        _killtree ${_pid}
        echo "ccpy has been stopped. IT IS HIGHLY RECOMMENDED to reboot to clean up any orphan jobs"
    fi
}

function update_ccpy_wc()
{
    pushd $( dirname "${BASH_SOURCE[0]}" ) > /dev/null
    if [ -d ".svn" ]; then
        svn revert --recursive --non-interactive ./
        svn up --non-interactive
    elif [ -d ".git" ]; then
        git fetch --all
        git reset --hard @{upstream}
        git submodule update --init --recursive
    fi
    popd > /dev/null
}

function load_system_environment()
{
    if [ -f /etc/environment ]; then
        set -a
        . /etc/environment
        set +a
    fi
}

function start_ccpy_in_bg()
{
    load_system_environment
    pushd $( dirname "${BASH_SOURCE[0]}" ) > /dev/null
    ./ccpyd.py
    popd > /dev/null
}

function start_ccpy_in_fg()
{
    load_system_environment
    pushd $( dirname "${BASH_SOURCE[0]}" ) > /dev/null
    ./ccpyd.py --fg
    popd > /dev/null
}

if [ $# -eq 0 ]; then
    if is_ccpy_running ; then
        echo "WARNING: ccpy is still running, not starting"
        return 1
    fi
    update_ccpy_wc
    start_ccpy_in_bg

elif [ $# -eq 1 ]; then
    if [ x"$1" == x"stop" ]; then
        stop_ccpy
    elif [ x"$1" == x"--skip-update" ]; then
        if is_ccpy_running ; then
            echo "WARNING: ccpy is still running, not starting"
            return 1
        fi
        start_ccpy_in_bg
    elif [ x"$1" == x"--fg" ]; then
        if is_ccpy_running ; then
            echo "WARNING: ccpy is still running, not starting"
            return 1
        fi
        update_ccpy_wc
        start_ccpy_in_fg
    else
        usage
    fi

elif [ $# -eq 2 ]; then
    if [[ x"$1" == x"--skip-update" && x"$2" == x"--fg" ]]; then
        if is_ccpy_running ; then
            echo "WARNING: ccpy is still running, not starting"
            return 1
        fi
        start_ccpy_in_fg
    elif [[ x"$1" == x"--fg" && x"$2" == x"--skip-update" ]]; then
        if is_ccpy_running ; then
            echo "WARNING: ccpy is still running, not starting"
            return 1
        fi
        start_ccpy_in_fg
    else
        usage
    fi

else
    usage
fi
