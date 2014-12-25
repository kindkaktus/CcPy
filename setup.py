#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
#  HeadURL : $HeadURL: svn://korostelev.net/CcPy/Trunk/setup.py $
#  Id      : $Id: setup.py 123 2009-03-28 19:50:48Z akorostelev $
#
#  Copyright (c) 2008-2014, Andrei Korostelev <andrei at korostelev dot net>
#
#  Before using this product in any way please read the license agreement.
#  If you do not agree to the terms in this agreement you are not allowed
#  to use this product or parts of it. You can read this license in the
#  file named LICENSE.
#

"""
Setup script
"""

import sys
import os


def main(argv=None):
    if argv is None:
        argv = sys.argv
    if not len(argv):
        print("*** Error: empty argv ?!")
        return -1
    if len(argv) == 1 or (len(argv) == 2 and argv[1] == "install"):
        return install()
    if len(argv) == 2 and argv[1] == "uninstall":
        return uninstall()
    usage()
    return 2


def usage():
    sys.stderr.write("usage: python setup.py [install]")
    sys.stderr.write("       python setup.py uninstall")


def install():
    print("Installing CcPy...")
    print("  Checking Python version...")
    if sys.version_info[0] < 2 or (sys.version_info[0] == 2 and sys.version_info[1] < 5):
        sys.stderr.write("*** Error: Python 2.5 or higher is required.")
        return -1

    print("  Copying config files...")
    try:
        import shutil
        shutil.copy("conf/ccpyd.conf", "/etc/")
        shutil.copy("conf/ccpy.conf", "/etc/")
        return 0
    except BaseException as e:
        sys.stderr.write("*** Error. %s" % str(e))
        return -1


def uninstall():
    print("Uninstalling CcPy...")
    try:
        if os.path.exists('/var/run/ccpyd.pid'):
            import signal
            print("  Stopping cppyd...")
            myPidFile = open('/var/run/ccpyd.pid', 'r')
            myPid = int(myPidFile.readline())
            myPidFile.close()
            os.kill(myPid, signal.SIGKILL)
    except BaseException as e:
        sys.stderr.write("*** Failed to stop ccpyd. %s" % str(e))
        return -1
    print("  Removing config files...")
    myRetVal = 0
    for myFile in [
            '/etc/ccpy.conf',
            '/etc/ccpyd.conf',
            '/etc/ccpy.state',
            '/var/log/ccpyd.log',
            '/var/run/ccpyd.pid']:
        myRetVal = _removeFileNoThrow(myFile)
    return myRetVal


def _removeFileNoThrow(aFileName):
    import os
    try:
        if os.path.exists(aFileName):
            os.remove(aFileName)
        return 0
    except OSError as e:
        sys.stderr.write("Warning. Cannot remove '%s'. Error: %s" % (aFileName, str(e)))
        return 1

if __name__ == "__main__":
    sys.exit(main())
