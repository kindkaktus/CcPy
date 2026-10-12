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
Unit tests for CcPy utilities
"""

import sys
import contextlib
import socket
import smtplib
import unittest
from unittest import mock

sys.path.append("..")
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

    def testPidExist(self):
        try:
            import os
            self.assertTrue(util.isPidExist(os.getpid()))
            self.assertTrue(util.isPidExist(1))
            self.assertTrue(not util.isPidExist(-123))
        except BaseException as e:
            print(("Error. %s. %s. %s" % (type(e), str(e), util.formatTb())))
            self.assertTrue(False)

    def testSysSingleton(self):
        try:
            mySingleton1 = util.SysSingleton('testapp1')
            mySingleton2 = util.SysSingleton('testapp2')
            self.assertRaises(util.SysSingletonCreateError, util.SysSingleton, 'testapp1', False)
            mySingleton1 = util.SysSingleton('testapp1')
            mySingleton1 = util.SysSingleton('testapp1', True)
            self.assertRaises(util.SysSingletonCreateError, util.SysSingleton, 'testapp2', False)
            mySingleton2 = util.SysSingleton('testapp2')
            mySingleton2 = util.SysSingleton('testapp2', True)
        except BaseException as e:
            print(("Error. %s. %s. %s" % (type(e), str(e), util.formatTb())))
            self.assertTrue(False)


class SendEmailNotificationTestCase(unittest.TestCase):
    _from = 'ccpy@example.com'
    _to = ['dev1@example.com', 'dev2@example.com']

    def setUp(self):
        sleep_patcher = mock.patch.object(util.time, 'sleep')
        self.sleep = sleep_patcher.start()
        self.addCleanup(sleep_patcher.stop)

    @contextlib.contextmanager
    def _patchedSmtp(self, aClassName, aSideEffects):
        """
        Yield (mocked smtplib class, mocked server connection)
        Each connection to the SMTP server gets the next item of aSideEffects: an exception to raise or None to succeed
        """
        with mock.patch.object(smtplib, aClassName, autospec=True) as smtp_class:
            smtp_class.side_effect = [e if e is not None else smtp_class.return_value for e in aSideEffects]
            yield smtp_class, smtp_class.return_value.__enter__.return_value

    def _send(self, aFmt=util.EmailFormat.plain, aSecurity=util.EmailSecurity.none, aUser=None, aPassword=None, **kwargs):
        util.sendEmailNotification(self._from, self._to, 'Subject', 'Body', None, [], aFmt,
                                   'smtp.example.com', 25, aSecurity, aUser, aPassword, **kwargs)

    def _sentMessage(self, aSvr):
        self.assertEqual(aSvr.sendmail.call_count, 1)
        from_addr, to_addrs, msg = aSvr.sendmail.call_args[0]
        self.assertEqual(from_addr, self._from)
        self.assertEqual(to_addrs, self._to)
        return msg

    def testSentAtFirstAttempt(self):
        with self._patchedSmtp('SMTP', [None]) as (smtp_class, svr):
            self._send()
            smtp_class.assert_called_once_with('smtp.example.com', 25, timeout=util.EmailSmtpTimeoutSec)
            self.assertIn('Subject: Subject', self._sentMessage(svr))
            svr.login.assert_not_called()
            svr.starttls.assert_not_called()
        self.sleep.assert_not_called()

    def testSentAfterNetworkErrors(self):
        errors = [OSError(101, 'Network is unreachable'), ConnectionResetError(), socket.timeout(), None]
        with self._patchedSmtp('SMTP', errors) as (smtp_class, svr):
            self._send(aMaxAttempts=4, aFirstRetryDelaySec=10)
            self.assertEqual(smtp_class.call_count, 4)
            self._sentMessage(svr)
        self.assertEqual(self.sleep.call_args_list, [mock.call(10), mock.call(20), mock.call(40)])

    def testSentAfterTemporarySmtpErrors(self):
        errors = [smtplib.SMTPConnectError(-1, b'no greeting'),
                  smtplib.SMTPServerDisconnected('Connection unexpectedly closed'),
                  smtplib.SMTPResponseException(421, b'Service not available'),
                  smtplib.SMTPSenderRefused(451, b'Try again later', self._from),
                  None]
        with self._patchedSmtp('SMTP', errors) as (smtp_class, svr):
            self._send()
            self.assertEqual(smtp_class.call_count, 5)
            self._sentMessage(svr)
        self.assertEqual(self.sleep.call_args_list, [mock.call(30), mock.call(60), mock.call(120), mock.call(240)])

    def testFailsWhenNetworkErrorPersists(self):
        errors = [OSError(101, 'Network is unreachable') for _ in range(3)]
        with self._patchedSmtp('SMTP', errors) as (smtp_class, _):
            with self.assertRaises(OSError) as ctx:
                self._send(aMaxAttempts=3)
            self.assertIs(ctx.exception, errors[-1])
            self.assertEqual(smtp_class.call_count, 3)
        self.assertEqual(self.sleep.call_count, 2)

    def testNoRetryWhenOneAttempt(self):
        with self._patchedSmtp('SMTP', [OSError(101, 'Network is unreachable')]) as (smtp_class, _):
            self.assertRaises(OSError, self._send, aMaxAttempts=1)
            self.assertEqual(smtp_class.call_count, 1)
        self.sleep.assert_not_called()

    def testNoRetryOnPermanentErrors(self):
        permanent_errors = [smtplib.SMTPAuthenticationError(535, b'Authentication credentials invalid'),
                            smtplib.SMTPRecipientsRefused({'dev1@example.com': (550, b'No such user')}),
                            smtplib.SMTPDataError(554, b'Message rejected'),
                            smtplib.SMTPNotSupportedError('STARTTLS extension not supported by server'),
                            ValueError('unexpected')]
        for error in permanent_errors:
            with self.subTest(error=type(error).__name__):
                self.sleep.reset_mock()
                with self._patchedSmtp('SMTP', [None]) as (smtp_class, svr):
                    svr.sendmail.side_effect = error
                    with self.assertRaises(type(error)):
                        self._send(aUser='user', aPassword='secret')
                    self.assertEqual(smtp_class.call_count, 1)
                self.sleep.assert_not_called()

    def testRetryOnRealConnectionRefused(self):
        # No mocked smtplib here: connect to a local port nobody listens on
        with socket.socket() as s:
            s.bind(('127.0.0.1', 0))
            port = s.getsockname()[1]
        with self.assertRaises(ConnectionRefusedError):
            util.sendEmailNotification(self._from, self._to, 'Subject', 'Body', None, [], util.EmailFormat.plain,
                                       '127.0.0.1', port, util.EmailSecurity.none, None, None, aMaxAttempts=2)
        self.assertEqual(self.sleep.call_count, 1)

    def testTls(self):
        with self._patchedSmtp('SMTP_SSL', [OSError(101, 'Network is unreachable'), None]) as (smtp_class, svr):
            self._send(aSecurity=util.EmailSecurity.tls, aUser='user', aPassword='secret')
            self.assertEqual(smtp_class.call_count, 2)
            smtp_class.assert_called_with('smtp.example.com', 25, timeout=util.EmailSmtpTimeoutSec)
            svr.login.assert_called_once_with('user', 'secret')
            self._sentMessage(svr)

    def testStartTls(self):
        with self._patchedSmtp('SMTP', [None]) as (_, svr):
            self._send(aSecurity=util.EmailSecurity.starttls, aUser='user', aPassword='secret')
            svr.starttls.assert_called_once_with()
            svr.login.assert_called_once_with('user', 'secret')
            self._sentMessage(svr)

    def testFormats(self):
        for fmt, content_type in [(util.EmailFormat.plain, 'text/plain'),
                                  (util.EmailFormat.html, 'text/html'),
                                  (util.EmailFormat.attachment, 'text/html')]:
            with self.subTest(fmt=str(fmt)):
                with self._patchedSmtp('SMTP', [None]) as (_, svr):
                    self._send(aFmt=fmt)
                    self.assertIn('Content-Type: ' + content_type, self._sentMessage(svr))

    def testAttachments(self):
        with self._patchedSmtp('SMTP', [None]) as (_, svr):
            util.sendEmailNotification(self._from, self._to, 'Subject', 'Body', 'build log',
                                       [__file__, '/nonexistent.txt'], util.EmailFormat.attachment,
                                       'smtp.example.com', 25, util.EmailSecurity.none, None, None)
            msg = self._sentMessage(svr)
        self.assertIn('multipart/mixed', msg)
        self.assertIn('filename="utiltest.py"', msg)
        self.assertIn('filename="nonexistent.txt"', msg)
        self.assertIn('filename="build.log"', msg)

    def testInvalidArguments(self):
        with self._patchedSmtp('SMTP', [None]) as (smtp_class, _):
            self.assertRaises(Exception, self._send, aMaxAttempts=0)
            self.assertRaises(Exception, self._send, aFmt='rtf')
            smtp_class.assert_not_called()


if __name__ == '__main__':
    unittest.main()
