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
Unit tests for CcPy config parser
"""

import unittest
import sys

sys.path.append("..")
import ccpy.ccpyconfparser as ccpyconfparser
import ccpy.svntask as svntask
import ccpy.gittask as gittask
import ccpy.maketask as maketask
import ccpy.exectask as exectask
import ccpy.util as util
import ccpy.common as common


class CcPyConfParserTestCase(unittest.TestCase):
    _logger = util.initLogger(
        common.LoggerName,
        'CcPyConfParserTest.log',
        common.ProductName +
        ' v.' +
        common.ProductVersion,
        "DEBUG")

    def testNonExistentConfig(self):
        self.assertRaises(ccpyconfparser.ParseError, ccpyconfparser.parse, "ccpy.conf.nonexistent")

    def testGoodConfig1Order(self):
        myProjects = ccpyconfparser.parse("ccpy.conf.good.1")
        self.assertEqual(len(myProjects), 5)

        prjName, prjVal = next(myProjects)
        self.assertEqual(prjName, 'Product2')
        prjName, prjVal = next(myProjects)
        self.assertEqual(prjName, 'Product3')
        prjName, prjVal = next(myProjects)
        self.assertEqual(prjName, 'Product4')
        prjName, prjVal = next(myProjects)
        self.assertEqual(prjName, 'Product5')
        prjName, prjVal = next(myProjects)
        self.assertEqual(prjName, 'Product6')
        self.assertRaises(StopIteration, myProjects.__next__)

    def testGoodConfig1Contents(self):
        try:
            myProjects = ccpyconfparser.parse("ccpy.conf.good.1")
            self.assertEqual(len(myProjects), 5)

            # Product2 project
            myProjName = 'Product2'
            myTasks = myProjects[myProjName]['tasks']
            self.assertEqual(len(myTasks), 6)
            self.assertEqual(
                len([task for task in myTasks if isinstance(task, svntask.SvnTask)]), 1)
            self.assertEqual(
                len([task for task in myTasks if isinstance(task, gittask.GitTask)]), 1)
            self.assertEqual(
                len([task for task in myTasks if isinstance(task, maketask.MakeTask)]), 2)
            self.assertEqual(
                len([task for task in myTasks if isinstance(task, exectask.ExecTask)]), 2)
            self.assertEqual(myProjects[myProjName]['emailFrom'], 'product2.builds@company.com')
            self.assertEqual(
                myProjects[myProjName]['emailTo'], [
                    'product2.developer@company.com', 'product2.buildmaster@company.com'])
            self.assertEqual(myProjects[myProjName]['emailFormat'], util.EmailFormat.attachment)
            self.assertEqual(myProjects[myProjName]['emailServerHost'], 'localhost')
            self.assertEqual(myProjects[myProjName]['emailServerPort'], 25)
            self.assertEqual(myProjects[myProjName]['emailServerUsername'], None)
            self.assertEqual(myProjects[myProjName]['emailServerPassword'], None)
            self.assertEqual(myProjects[myProjName]['failOnError'], True)

            myTask = myTasks[0]
            self.assertTrue(isinstance(myTask, svntask.SvnTask))
            self.assertEqual(myTask.url, "https://company.com/repos/product2/mk")
            self.assertEqual(myTask.workingDir, "/ProductBuilds/mk")
            self.assertTrue(myTask.preCleanWorkingDir)

            myTask = myTasks[1]
            self.assertTrue(isinstance(myTask, maketask.MakeTask))
            self.assertEqual(myTask.workingDir, "/ProductBuilds/SysInfra/Projects/common")
            self.assertEqual(myTask.args, "clean release")
            self.assertEqual(myTask.timeout, 120)

            myTask = myTasks[2]
            self.assertTrue(isinstance(myTask, maketask.MakeTask))
            self.assertEqual(myTask.workingDir, "/ProductBuilds/SysInfra/Projects/logging")
            self.assertEqual(myTask.args, "")
            self.assertEqual(myTask.timeout, 600)

            myTask = myTasks[3]
            self.assertTrue(isinstance(myTask, exectask.ExecTask))
            self.assertEqual(myTask.executable, "commontests")
            self.assertEqual(myTask.args, "--xmlout")
            self.assertEqual(myTask.workingDir, "/ProductBuilds/SysInfra/TestProjects/commontests")
            self.assertEqual(myTask.timeout, 30)
            self.assertEqual(myTask.warningExitCode, 2)

            myTask = myTasks[4]
            self.assertTrue(isinstance(myTask, exectask.ExecTask))
            self.assertEqual(myTask.executable, "loggingTests")
            self.assertEqual(myTask.args, "")
            self.assertEqual(myTask.workingDir, "")
            self.assertEqual(myTask.timeout, 600)

            myTask = myTasks[5]
            self.assertTrue(isinstance(myTask, gittask.GitTask))
            self.assertEqual(myTask.url, "https://company.com/repos/product2/Common")
            self.assertEqual(myTask.workingDir, "/ProductBuilds/Common")
            self.assertFalse(myTask.preCleanWorkingDir)

            # Product3 project
            myProjName = "Product3"
            myTasks = myProjects[myProjName]['tasks']
            self.assertEqual(len(myTasks), 1)
            self.assertEqual(
                len([task for task in myTasks if isinstance(task, svntask.SvnTask)]), 1)
            self.assertEqual(myProjects[myProjName]['emailFrom'], 'product3.builds@company.com')
            self.assertEqual(myProjects[myProjName]['emailTo'], ['product3.developer@company.com'])
            self.assertEqual(myProjects[myProjName]['emailFormat'], util.EmailFormat.attachment)
            self.assertEqual(myProjects[myProjName]['emailAttachments'], [])
            self.assertEqual(myProjects[myProjName]['failOnError'], False)

            myTask = myTasks[0]
            self.assertTrue(isinstance(myTask, svntask.SvnTask))
            self.assertEqual(myTask.url, "https://company.com/repos/product3/server")
            self.assertEqual(myTask.workingDir, "/ProductBuilds/server")
            self.assertFalse(myTask.preCleanWorkingDir)

            # Product4 project
            myProjName = "Product4"
            myTasks = myProjects[myProjName]['tasks']
            self.assertEqual(len(myTasks), 1)
            self.assertEqual(
                len([task for task in myTasks if isinstance(task, maketask.MakeTask)]), 1)
            self.assertEqual(myProjects[myProjName]['failOnError'], True)
            self.assertEqual(myProjects[myProjName]['emailFrom'], '')
            self.assertEqual(myProjects[myProjName]['emailTo'], [])

            myTask = myTasks[0]
            self.assertTrue(isinstance(myTask, maketask.MakeTask))
            self.assertEqual(myTask.workingDir, "/ProductBuilds/SysInfra/Projects/common")
            self.assertEqual(myTask.args, "")
            self.assertEqual(myTask.timeout, 600)

            # Product5 project
            myProjName = "Product5"
            self.assertEqual(
                myProjects[myProjName]['emailFrom'],
                'product5.buildserver@company.com')
            self.assertEqual(
                myProjects[myProjName]['emailTo'], [
                    'product5.developer@company.com', 'product5.buildmaster@company.com'])
            self.assertEqual(myProjects[myProjName]['emailFormat'], util.EmailFormat.plain)
            self.assertEqual(myProjects[myProjName]['emailServerHost'], 'localhost')
            self.assertEqual(myProjects[myProjName]['emailServerPort'], 25)
            self.assertEqual(myProjects[myProjName]['emailServerUsername'], None)
            self.assertEqual(myProjects[myProjName]['emailServerPassword'], None)
            self.assertEqual(myProjects[myProjName]['emailAttachments'], [])

            # Product6 project
            myProjName = "Product6"
            self.assertEqual(
                myProjects[myProjName]['emailFrom'],
                'product6.buildserver@company.com')
            self.assertEqual(myProjects[myProjName]['emailTo'], ['product6.developer@company.com'])
            self.assertEqual(myProjects[myProjName]['emailFormat'], util.EmailFormat.html)
            self.assertEqual(myProjects[myProjName]['emailServerHost'], 'smtp.mymail.com')
            self.assertEqual(myProjects[myProjName]['emailServerPort'], 2626)
            self.assertEqual(myProjects[myProjName]['emailServerUsername'], 'jos')
            self.assertEqual(myProjects[myProjName]['emailServerPassword'], 'topsecret')
            self.assertEqual(myProjects[myProjName]['emailAttachments'], ['/var/log/messages', '/var/log/messages.1'])

        except BaseException as e:
            print(("Error. %s. %s. %s" % (type(e), str(e), util.formatTb())))
            self.assertTrue(False)

    def testBadConfig1(self):
        self.assertRaises(ccpyconfparser.ParseError, ccpyconfparser.parse, "ccpy.conf.bad.1")

if __name__ == '__main__':
    unittest.main()
