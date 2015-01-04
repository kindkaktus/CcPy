#!/bin/bash

# pylint onwards 1.4 does not support python-2.6 any more.
# use 'pip install pylint==1.3.0' for systems with python-2.6
FILE_LIST="./*.py ../*.py ../ccpy/*.py ../www-project/*.py"
pylint --errors-only --msg-template='{abspath}:{line:3d},{column}: {obj}: [{msg_id}] {msg}' --disable=E1002,E1101 ${FILE_LIST}