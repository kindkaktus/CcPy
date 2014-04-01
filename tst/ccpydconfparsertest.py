#
#  HeadURL : $HeadURL: svn://korostelev.net/CcPy/Trunk/tst/ccpydconfparsertest.py $
#  Id      : $Id: ccpydconfparsertest.py 179 2010-11-10 09:24:28Z akorostelev $
#
#  Copyright (c) 2008-2009, Andrei Korostelev <andrei at korostelev dot net>
#
#  Before using this product in any way please read the license agreement.
#  If you do not agree to the terms in this agreement you are not allowed
#  to use this product or parts of it. You can read this license in the
#  file named LICENSE.
#

"""
Unit tests for ccpyd config parser
"""

import sys
import unittest

sys.path.append("..") 
import ccpy.ccpydconfparser as ccpydconfparser
import ccpy.util as util
import ccpy.common as common

class CcPydConfParserTestCase(unittest.TestCase):
    _logger = util.initLogger( common.LoggerName, 'CcPydConfParserTest.log', common.ProductName+' v.'+common.ProductVersion, "DEBUG" )

    def testNonExistentConfig(self):
        self.assertRaises(ccpydconfparser.ParseError, ccpydconfparser.parse, "ccpyd.conf.nonexistent")

    def testGoodConfig1(self):
        from datetime import time
        try:
            myDataDict = ccpydconfparser.parse("ccpyd.conf.good.1")
            self.assertEqual( len(myDataDict), 6 )
            self.assertEqual( myDataDict['ccpyConfig'], '/etc/ccpy.conf.1' )
            self.assertTrue ( myDataDict['schedule'])
            self.assertEqual( myDataDict['scheduleTime'], time(6,30))
            self.assertEqual( myDataDict['logging'], True )
            self.assertEqual( myDataDict['logFile'], '/var/log/ccpyd.log' )
            self.assertEqual( myDataDict['logLevel'], 'DEBUG' )
        except BaseException, e:
            print("Error. %s. %s. %s" % (type(e), str(e), util.formatTb()))
            self.assert_(False)

    def testGoodConfig2(self):
        try:
            myDataDict = ccpydconfparser.parse("ccpyd.conf.good.2")
            self.assertEqual( len(myDataDict), 3 )
            self.assertEqual( myDataDict['ccpyConfig'], '/etc/ccpy.conf' )
            self.assertFalse( myDataDict['schedule'])
            self.assertEqual( myDataDict['logging'], False )
        except BaseException, e:
            print("Error. %s. %s. %s" % (type(e), str(e), util.formatTb()))
            self.assert_(False)

if __name__ == '__main__':
    if ( sys.version_info[0] < 2 or ( sys.version_info[0] == 2 and sys.version_info[1] < 5 ) ):
        print("Python 2.5 or higher is required for the program to run.")
    exit(-1)
    unittest.main()
