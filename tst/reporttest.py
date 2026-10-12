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
Unit tests for CcPy reports
"""

import sys
import datetime
import unittest

sys.path.append("..")
import ccpy.report as report
from ccpy.util import EmailFormat


class ReportTestCase(unittest.TestCase):
    _start = datetime.datetime(2026, 10, 12, 1, 0, 0)
    _end = datetime.datetime(2026, 10, 12, 1, 30, 0)
    _summary = {'prjName': 'Product1', 'prjStatus': 'FAILED', 'numSucceededTasks': 1,
                'numSucceededTasksWithWarning': 0, 'numFailedTasks': 1, 'startTime': _start, 'endTime': _end}
    _output = 'if (a < b && c > d) "quoted" \'single\''
    _tasks = [{'name': 'ExecTask', 'status': 'OK', 'description': 'Built', 'startTime': _start, 'endTime': _end,
               'allocatedTime': 3600, 'output': _output},
              {'name': 'MakeTask', 'status': 'FAILED', 'description': 'Failed', 'startTime': _start, 'endTime': _end}]

    def testHtmlBodyEscapesTaskOutput(self):
        body = report.makeEmailBody(EmailFormat.html, self._summary, self._tasks, True)
        self.assertIn('<pre>if (a &lt; b &amp;&amp; c &gt; d) "quoted" \'single\'</pre>', body)
        self.assertNotIn(self._output, body)
        self.assertIn('Product1', body)
        self.assertIn('50.0% of allocated time', body)

    def testPlainBodyAndAttachmentKeepTaskOutput(self):
        body = report.makeEmailBody(EmailFormat.plain, self._summary, self._tasks, True)
        self.assertIn(self._output, body)
        attachment = report.makeAttachmentText(EmailFormat.attachment, self._tasks, True)
        self.assertIn(self._output, attachment)
        summary = report.makeEmailBody(EmailFormat.attachment, self._summary, self._tasks, True)
        self.assertIn('Product1', summary)


if __name__ == '__main__':
    unittest.main()
