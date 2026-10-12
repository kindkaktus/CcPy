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

    def _runMain(self, aLoggingConf, aEmailErrors):
        """ Run ccpyd main() in foreground, return (exit code, initLogger call arguments) """
        ccpyd_conf = os.path.join(self._dir, 'ccpyd.conf')
        with open(ccpyd_conf, 'w') as f:
            f.write('<ccpyd><ccpyConfig>%s</ccpyConfig>%s</ccpyd>' % (self._ccpyConf, aLoggingConf))
        # keep logging to the test log: main() would otherwise redirect and close the shared logger
        with mock.patch.object(ccpyd.util, 'initLogger', return_value=self._logger) as init_logger, \
                mock.patch.object(ccpyd.util, 'closeLogger'), \
                mock.patch.object(ccpyd.util, 'sendEmailNotification', side_effect=aEmailErrors):
            exit_code = ccpyd.main(['--fg', '--conf', ccpyd_conf])
        init_logger.assert_called_once_with(common.LoggerName, mock.ANY, mock.ANY, mock.ANY)
        return exit_code, init_logger.call_args[0]

    def testMainExitCode(self):
        logging_conf = '<logging enabled="on"><file>/tmp/ccpyd.log</file><level>INFO</level></logging>'
        exit_code, logger_args = self._runMain(logging_conf, [None, None, None])
        self.assertEqual(exit_code, 0)
        self.assertEqual((logger_args[1], logger_args[3]), ('/tmp/ccpyd.log', 'INFO'))
        exit_code, _ = self._runMain(logging_conf, [None, OSError(101, 'Network is unreachable'), None])
        self.assertEqual(exit_code, -1)
        self._assertAllProjectsIntegrated()

    def testMainWithLoggingDisabled(self):
        for logging_conf in ['<logging enabled="off"><file>/tmp/ccpyd.log</file></logging>', '']:
            with self.subTest(logging_conf=logging_conf):
                exit_code, logger_args = self._runMain(logging_conf, [None, None, None])
                self.assertEqual(exit_code, 0)
                self.assertEqual(logger_args[1], '/dev/null')
        self._assertAllProjectsIntegrated()

if __name__ == '__main__':
    unittest.main()
