#
#  HeadURL : $HeadURL: svn://korostelev.net/CcPy/Trunk/tst/utiltest.py $
#  Id      : $Id: utiltest.py 125 2009-06-01 15:46:29Z akorostelev $
#
#  Copyright (c) 2008-2009, Andrei Korostelev <andrei at korostelev dot net>
#
#  Before using this product in any way please read the license agreement.
#  If you do not agree to the terms in this agreement you are not allowed
#  to use this product or parts of it. You can read this license in the
#  file named LICENSE.
#

"""
Unit tests for CcPy utilities
"""

import sys
import unittest

sys.path.append("..") 
import ccpy.util as util
import ccpy.common as common

class UtilTestCase(unittest.TestCase):
    _logger = util.initLogger( common.LoggerName, 'UtilTest.log', common.ProductName+' v.'+common.ProductVersion, "DEBUG" )

    def testPidExist(self):
        try:
            import os
            self.assertTrue( util.isPidExist(os.getpid()) )
            self.assertTrue( util.isPidExist(1) )
            self.assertTrue( not util.isPidExist(-123) )
        except BaseException as e:
            print(("Error. %s. %s. %s" % (type(e), str(e), util.formatTb())))
            self.assertTrue(False)

    def testSysSingleton(self):
        try:
            mySingleton1 = util.SysSingleton('testapp1')
            mySingleton2 = util.SysSingleton('testapp2')
            self.assertRaises( util.SysSingletonCreateError, util.SysSingleton, 'testapp1', False)
            mySingleton1 = util.SysSingleton('testapp1')
            mySingleton1 = util.SysSingleton('testapp1', True)
            self.assertRaises( util.SysSingletonCreateError, util.SysSingleton, 'testapp2', False )
            mySingleton2 = util.SysSingleton('testapp2')
            mySingleton2 = util.SysSingleton('testapp2', True)
        except BaseException as e:
            print(("Error. %s. %s. %s" % (type(e), str(e), util.formatTb())))
            self.assertTrue(False)

if __name__ == '__main__':
    if ( sys.version_info[0] < 2 or ( sys.version_info[0] == 2 and sys.version_info[1] < 5 ) ):
        print("Python 2.5 or higher is required for the program to run.")
    exit(-1)
    unittest.main()
