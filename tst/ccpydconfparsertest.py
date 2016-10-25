#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
#  Copyright (c) 2008-2016, Andrei Korostelev <andrei at korostelev dot net>
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
    _logger = util.initLogger(
        common.LoggerName,
        'CcPydConfParserTest.log',
        common.ProductName +
        ' v.' +
        common.ProductVersion,
        "DEBUG")

    def testNonExistentConfig(self):
        self.assertRaises(
            ccpydconfparser.ParseError,
            ccpydconfparser.parse,
            "ccpyd.conf.nonexistent")

    def testGoodConfig1(self):
        try:
            conf = ccpydconfparser.parse("ccpyd.conf.good.1")
            self.assertEqual(len(conf), 4)
            self.assertEqual(conf['ccpyConfig'], '/etc/ccpy.conf.1')
            self.assertEqual(conf['logging'], True)
            self.assertEqual(conf['logFile'], '/var/log/ccpyd.log')
            self.assertEqual(conf['logLevel'], 'DEBUG')
        except BaseException as e:
            print(("Error. %s. %s. %s" % (type(e), str(e), util.formatTb())))
            self.assertTrue(False)

    def testGoodConfig2(self):
        try:
            conf = ccpydconfparser.parse("ccpyd.conf.good.2")
            self.assertEqual(len(conf), 2)
            self.assertEqual(conf['ccpyConfig'], '/etc/ccpy.conf')
            self.assertEqual(conf['logging'], False)
        except BaseException as e:
            print(("Error. %s. %s. %s" % (type(e), str(e), util.formatTb())))
            self.assertTrue(False)

if __name__ == '__main__':
    unittest.main()
