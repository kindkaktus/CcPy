#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Andrei Korostelev <andrei at korostelev dot net>
#
#  Before using this product in any way please read the license agreement.
#  If you do not agree to the terms in this agreement you are not allowed
#  to use this product or parts of it. You can read this license in the
#  file named LICENSE.
#

"""
Unit tests for CcPy daemon
"""

import os
import sys
import shutil
import tempfile
import unittest
from unittest import mock

sys.path.append("..")
import ccpyd
from ccpy.ccpystate import CcPyState, PrjStates
import ccpy.util as util
import ccpy.common as common


class CcPydTestCase(unittest.TestCase):
    _logger = util.initLogger(
        common.LoggerName,
        'CcPydTest.log',
        common.ProductName +
        ' v.' +
        common.ProductVersion,
        "DEBUG")
    _projects = ['Product1', 'Product2', 'Product3']

    def setUp(self):
        self._dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self._dir)
        self._ccpyConf = self._writeCcPyConf()
        self._stateFile = os.path.join(self._dir, 'ccpy.state')
        state_patcher = mock.patch.object(ccpyd, 'CcPyState', lambda: CcPyState(self._stateFile))
        state_patcher.start()
        self.addCleanup(state_patcher.stop)

    def _writeCcPyConf(self):
        """ Each project runs one task creating '<project name>.done' in the temp dir and sends an email report """
        prjs = ''
        for prj in self._projects:
            prjs += '''
  <project name="%s">
    <tasks>
      <exec>
        <executable>touch</executable>
        <args>%s</args>
        <workingDirectory>%s</workingDirectory>
      </exec>
    </tasks>
    <emailNotification>
      <from>buildserver@company.com</from>
      <to>developer@company.com</to>
    </emailNotification>
  </project>''' % (prj, prj + '.done', self._dir)
        path = os.path.join(self._dir, 'ccpy.conf')
        with open(path, 'w') as f:
            f.write('<ccpy>%s\n</ccpy>\n' % prjs)
        return path

    def _assertAllProjectsIntegrated(self):
        for prj in self._projects:
            self.assertTrue(os.path.isfile(os.path.join(self._dir, prj + '.done')), prj)
            self.assertEqual(CcPyState(self._stateFile).getPrjState(prj), PrjStates.OK)

    def testAllEmailsSent(self):
        with mock.patch.object(ccpyd.util, 'sendEmailNotification') as send_email:
            self.assertEqual(ccpyd.execTasks(self._ccpyConf), [])
        self.assertEqual(send_email.call_count, 3)
        self._assertAllProjectsIntegrated()

    def testFailedEmailDoesNotStopOtherProjects(self):
        errors = [OSError(101, 'Network is unreachable'), None, Exception('Unexpected')]
        with mock.patch.object(ccpyd.util, 'sendEmailNotification', side_effect=errors) as send_email:
            self.assertEqual(ccpyd.execTasks(self._ccpyConf), ['Product1', 'Product3'])
        self.assertEqual(send_email.call_count, 3)
        self._assertAllProjectsIntegrated()

    def testMainExitCode(self):
        ccpyd_conf = os.path.join(self._dir, 'ccpyd.conf')
        with open(ccpyd_conf, 'w') as f:
            f.write('<ccpyd><ccpyConfig>%s</ccpyConfig><logging enabled="on"/></ccpyd>' % self._ccpyConf)
        argv = ['--fg', '--conf', ccpyd_conf]
        # keep logging to the test log: main() would otherwise redirect and close the shared logger
        for func, replacement in [('initLogger', lambda *args: self._logger), ('closeLogger', lambda *args: None)]:
            patcher = mock.patch.object(ccpyd.util, func, replacement)
            patcher.start()
            self.addCleanup(patcher.stop)
        with mock.patch.object(ccpyd.util, 'sendEmailNotification'):
            self.assertEqual(ccpyd.main(argv), 0)
        with mock.patch.object(ccpyd.util, 'sendEmailNotification', side_effect=[None, OSError(101, 'Network is unreachable'), None]):
            self.assertEqual(ccpyd.main(argv), -1)
        self._assertAllProjectsIntegrated()


if __name__ == '__main__':
    unittest.main()
