#!/bin/bash

# check python scripts

# return 0 if Python version is legacy (< 2.7) for pylint-1.4+
function is_legacy_python_version()
{
    local version=$(python --version 2>&1 | cut -d ' ' -f 2)
    local major=$(echo ${version} | cut -d . -f 1)
    if ((major >= 3)); then
        return 1;
    fi
    local minor=$(echo ${version} | cut -d . -f 2)
    if ((minor >= 7)); then
        return 1;
    fi
    return 0;
}

function install_deps()
{
    if is_legacy_python_version ; then
        # old python versions need specific versions of packages
        local astroid_version=$(pip show astroid | grep ^Version | cut -d ' ' -f 2)
        if [ x"${astroid_version}" != x"1.2.1" ]; then
            echo "installing astroid-1.2.1"
            pip uninstall -y astroid > /dev/null
            # clean pip cache otherwise a newer package version might be installed regardless what we specify
            rm -rf /tmp/pip-build-root
            pip install astroid==1.2.1 > /dev/null
        fi
        local pylint_version=$(pip show pylint | grep ^Version | cut -d ' ' -f 2)
        if [ x"${pylint_version}" != x"1.3.0" ]; then
            echo "installing pylint-1.3.0"
            pip uninstall -y pylint > /dev/null
            # clean pip cache otherwise a newer package version might be installed regardless what we specify
            rm -rf /tmp/pip-build-root
            pip install pylint==1.3.0 > /dev/null
        fi
    else
        pip install --upgrade pylint > /dev/null
    fi
}


function check_python_scripts()
{
    local filelist="$1"
    local disabled_errors="E1101"  # pylint does not understand our infra.Enum
    disabled_errors+=",E1103" # false-positive
    disabled_errors+=",E0611" # known false-positive
    pylint --errors-only --msg-template='{abspath}:{line:3d},{column}: {obj}: [{msg_id}] {msg}' --disable=${disabled_errors} ${filelist}
}

install_deps

# check directories one-by-one (as separate projects) otherwise pylint gets confused by the same module names (e.g. common.py) and will not import them again

check_python_scripts "./*.py"
check_python_scripts "../*.py"
check_python_scripts "../ccpy/*.py"
check_python_scripts "../www-project/*.py"
