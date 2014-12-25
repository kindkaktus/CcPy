#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# This script fixes formatting in python scripts
# Usage: format_pep8.py [--fix]
# Before calling this script make sure autopep8 is installed:
# pip install --upgrade argparse autopep8

import sys
from subprocess import Popen, PIPE

WIN32 = sys.platform == 'win32'

# Configuration
pep8CheckerCommonCmdLine = "autopep8 --recursive --aggressive --aggressive --max-line-length 99"
pep8CheckerCmdLine = pep8CheckerCommonCmdLine + " --diff ./"
pep8FormatterCmdLine = pep8CheckerCommonCmdLine + " --in-place --verbose ./"

# Check only
if len(sys.argv) == 1:
    returnval = 0

    cmd = 'python ' + pep8CheckerCmdLine if WIN32 else pep8CheckerCmdLine
    p = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
    out, err = p.communicate()
    if p.returncode == 0:
        if WIN32:
            out = out.replace('\r\n', '\n')
        if out:
            print >> sys.stderr, out
            returnval = 1
    else:
        print >> sys.stderr, "Error checking code formatting\n%s" % err
        returnval = 1

    sys.exit(returnval)

# Fix
elif len(sys.argv) == 2 and sys.argv[1] == "--fix":
    returnval = 0

    cmd = 'python ' + pep8FormatterCmdLine if WIN32 else pep8FormatterCmdLine
    p = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
    out, err = p.communicate()
    if WIN32:
        out = out.replace('\r\n', '\n')
    if p.returncode != 0:
        print >> sys.stderr, "Error checking code formatting\n%s" % err
        returnval = 1
    elif out:
        print(out)

    sys.exit(returnval)

else:
    print ("Usage: %s [--fix]")
    sys.exit(1)
