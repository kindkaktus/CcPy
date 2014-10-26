#!/bin/bash

FILE_LIST="./*.py ../*.py ../ccpy/*.py ../www-project/*.py"
pylint --errors-only --msg-template='{abspath}:{line:3d},{column}: {obj}: [{msg_id}] {msg}' --disable=E1002,E1101 ${FILE_LIST}