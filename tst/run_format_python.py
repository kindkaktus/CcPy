#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This script checks and fixes formatting in python scripts
# - Checks and fixes python shebang to /usr/bin/env python
# - Checks and fixes python coding to utf-8
# - Checks and fixes PEP8 formatting
#
# Usage: run_format_python.py [--fix]
# Return values: 0 - success
#                1 - indicates invalid formatting when called to check formatting; indicates error when called to fix formatting
#
# Requires autopep8. Install it with:
# pip install --upgrade argparse autopep8

import sys
sys.path.append("../contrib")
import PrettyPython as fmt

# Configuration
DIRS = ['../']

success = fmt.install_deps()
if not success:
    sys.exit(1)

# Check
if len(sys.argv) == 1:
    success = fmt.check_shebang(DIRS)
    success = fmt.check_coding(DIRS) and success
    success = fmt.check_pep8(DIRS) and success
    sys.exit(0 if success else 1)

# Fix
elif len(sys.argv) == 2 and sys.argv[1] == "--fix":
    success = fmt.fix_shebang(DIRS) and fmt.fix_coding(DIRS) and fmt.fix_pep8(DIRS)
    sys.exit(0 if success else 1)

else:
    prog = sys.argv[0]
    print("Usage: %s [--fix]" % prog)
    sys.exit(1)
