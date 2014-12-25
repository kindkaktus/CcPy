#!/usr/bin/env python
# -*- coding: utf-8 -*-
#  HeadURL : $HeadURL: svn://korostelev.net/CcPy/Trunk/tst/ccpystatetest.py $
#  Id      : $Id: ccpystatetest.py 125 2009-06-01 15:46:29Z akorostelev $
#
#  Copyright (c) 2008-2009, Andrei Korostelev <andrei at korostelev dot net>
#
#  Before using this product in any way please read the license agreement.
#  If you do not agree to the terms in this agreement you are not allowed
#  to use this product or parts of it. You can read this license in the
#  file named LICENSE.
#

"""
Unit tests for CcPyState
"""

import sys
import unittest
import shutil
import os

sys.path.append("..")
from ccpy.ccpystate import CcPyState, PrjStates
import ccpy.util as util
import ccpy.common as common


class UtilTestCase(unittest.TestCase):
    _logger = util.initLogger(
        common.LoggerName,
        'UtilTest.log',
        common.ProductName +
        ' v.' +
        common.ProductVersion,
        "DEBUG")

    def setUp(self):
        shutil.copy('ccpy.state', 'ccpy.state.tmp')

    def tearDown(self):
        os.remove('ccpy.state.tmp')

    def testCcPyStateGetSet(self):
        try:
            myCcPyState = CcPyState('ccpy.state.tmp')
            self.assertEqual(myCcPyState.getPrjState('Product V2'), PrjStates.OK)
            self.assertEqual(myCcPyState.getPrjState('Product V3'), PrjStates.UNKNOWN)
            myCcPyState.setPrjState('Product V3', PrjStates.FAILED)
            self.assertEqual(myCcPyState.getPrjState('Product V2'), PrjStates.OK)
            self.assertEqual(myCcPyState.getPrjState('Product V3'), PrjStates.FAILED)
            myCcPyState.setPrjState('Product V2', PrjStates.FAILED)
            myCcPyState.setPrjState('Product V3', PrjStates.OK)
            self.assertEqual(myCcPyState.getPrjState('Product V2'), PrjStates.FAILED)
            self.assertEqual(myCcPyState.getPrjState('Product V3'), PrjStates.OK)

            os.remove('ccpy.state.tmp')
            myCcPyState = CcPyState('ccpy.state.tmp')
            self.assertEqual(myCcPyState.getPrjState('Product V2'), PrjStates.UNKNOWN)
            self.assertEqual(myCcPyState.getPrjState('Product V3'), PrjStates.UNKNOWN)
            myCcPyState.setPrjState('Product V2', PrjStates.OK)
            self.assertEqual(myCcPyState.getPrjState('Product V2'), PrjStates.OK)
            self.assertEqual(myCcPyState.getPrjState('Product V3'), PrjStates.UNKNOWN)
        except BaseException as e:
            print(("Error. %s. %s. %s" % (type(e), str(e), util.formatTb())))
            self.assertTrue(False)

if __name__ == '__main__':
    unittest.main()
