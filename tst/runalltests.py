#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
#  Copyright (c) 2008-2014, Andrei Korostelev <andrei at korostelev dot net>
#
#  Before using this product in any way please read the license agreement.
#  If you do not agree to the terms in this agreement you are not allowed
#  to use this product or parts of it. You can read this license in the
#  file named LICENSE.
#


"""
Executes all unit tests in the current directory
"""

import sys
import os
import re
import unittest


def testAll():
    myDir = os.path.abspath(os.path.dirname(sys.argv[0]))
    myFiles = os.listdir(myDir)
    myUnitTestFileRegex = re.compile(r"test.py$", re.IGNORECASE)
    myUnitTestFiles = list(filter(myUnitTestFileRegex.search, myFiles))
    myUnitTestModuleNames = [os.path.splitext(f)[0] for f in myUnitTestFiles]
    myUnitTestModules = list(map(__import__, myUnitTestModuleNames))
    return unittest.TestSuite(
        list(map(unittest.defaultTestLoader.loadTestsFromModule, myUnitTestModules)))

if __name__ == "__main__":
    unittest.main(defaultTest="testAll")
