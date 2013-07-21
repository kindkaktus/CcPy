#
#  HeadURL : $HeadURL: svn://korostelev.net/CcPy/Trunk/tst/alltests.py $
#  Id      : $Id: alltests.py 87 2009-02-04 20:46:23Z akorostelev $
#
#  Copyright (c) 2008-2009, Andrei Korostelev <andrei at korostelev dot net>
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
    myUnitTestFiles = filter(myUnitTestFileRegex.search, myFiles)                     
    myUnitTestModuleNames = map(lambda f: os.path.splitext(f)[0], myUnitTestFiles)         
    myUnitTestModules = map(__import__, myUnitTestModuleNames)                 
    return unittest.TestSuite(map(unittest.defaultTestLoader.loadTestsFromModule, myUnitTestModules))          

if __name__ == "__main__":                   
    unittest.main(defaultTest="testAll")
