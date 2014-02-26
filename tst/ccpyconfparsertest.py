#
#  Copyright (c) 2008-2014, Andrei Korostelev <andrei at korostelev dot net>
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
import ccpy.maketask as maketask
import ccpy.exectask as exectask
import ccpy.util as util
import ccpy.common as common

class CcPyConfParserTestCase(unittest.TestCase):
    _logger = util.initLogger( common.LoggerName, 'CcPyConfParserTest.log', common.ProductName+' v.'+common.ProductVersion, "DEBUG" )

    def testNonExistentConfig(self):
        self.assertRaises(ccpyconfparser.ParseError, ccpyconfparser.parse, "ccpy.conf.nonexistent")

    def testGoodConfig1Order(self):
        myProjects  = ccpyconfparser.parse("ccpy.conf.good.1")
        self.assertEqual( len(myProjects), 5 )
        
        prjName, prjVal = myProjects.next()
        self.assertEquals(prjName, 'ProductV2')
        prjName, prjVal = myProjects.next()
        self.assertEquals(prjName, 'ProductV3')
        prjName, prjVal = myProjects.next()
        self.assertEquals(prjName, 'ProductV4')
        prjName, prjVal = myProjects.next()
        self.assertEquals(prjName, 'ProductV5')
        prjName, prjVal = myProjects.next()
        self.assertEquals(prjName, 'ProductV6')  
        self.assertRaises(StopIteration, myProjects.next)
        
        
    def testGoodConfig1Contents(self):
        try:
            myProjects  = ccpyconfparser.parse("ccpy.conf.good.1")
            self.assertEqual( len(myProjects), 5 )

            # Product V.2 project
            myProjName = 'ProductV2'
            myTasks = myProjects[myProjName]['tasks']
            self.assertEqual( len(myTasks), 6 )
            self.assertEqual( len(filter(lambda task: isinstance(task, svntask.SvnTask),  myTasks)), 2 )
            self.assertEqual( len(filter(lambda task: isinstance(task, maketask.MakeTask), myTasks)), 2 )
            self.assertEqual( len(filter(lambda task: isinstance(task, exectask.ExecTask), myTasks)), 2 )
            self.assertEqual( myProjects[myProjName]['emailFrom'], 'buildserver@company.com')
            self.assertEqual( myProjects[myProjName]['emailTo'], ['developer@company.com', 'buildmaster@company.com'] )
            self.assertEqual( myProjects[myProjName]['emailFormat'], util.EmailFormat.html )
            self.assertEqual( myProjects[myProjName]['emailServerHost'], 'localhost' )
            self.assertEqual( myProjects[myProjName]['emailServerPort'], 25 )
            self.assertEqual( myProjects[myProjName]['emailServerUsername'], None )
            self.assertEqual( myProjects[myProjName]['emailServerPassword'], None )
            self.assertEqual( myProjects[myProjName]['failOnError'], True )
            self.assertEqual( myProjects[myProjName]['skipIfNoModifications'], True )

            myTask = myTasks[0]
            self.assertTrue( isinstance(myTask, svntask.SvnTask) )
            self.assertEqual( myTask.trunkUrl, "https://company.com/repos/productv2/mk")
            self.assertEqual( myTask.workingDir, "/ProductBuilds/mk")
            self.assertTrue( myTask.preCleanWorkingDir)

            myTask = myTasks[1]
            self.assertTrue( isinstance(myTask, maketask.MakeTask) )
            self.assertEqual( myTask.workingDir, "/ProductBuilds/SysInfra/Projects/common")
            self.assertEqual( myTask.args, "clean release")
            self.assertEqual( myTask.timeout, 120);

            myTask = myTasks[2]
            self.assertTrue( isinstance(myTask, maketask.MakeTask) )
            self.assertEqual( myTask.workingDir, "/ProductBuilds/SysInfra/Projects/logging")
            self.assertEqual( myTask.args, "")
            self.assertEqual( myTask.timeout, 600);

            myTask = myTasks[3]
            self.assertTrue( isinstance(myTask, exectask.ExecTask) )
            self.assertEqual( myTask.executable, "commontests")
            self.assertEqual( myTask.args, "--xmlout")
            self.assertEqual( myTask.workingDir, "/ProductBuilds/SysInfra/TestProjects/commontests")
            self.assertEqual( myTask.timeout, 30);
            self.assertEqual( myTask.warningExitCode, 2);

            myTask = myTasks[4]
            self.assertTrue( isinstance(myTask, exectask.ExecTask) )
            self.assertEqual( myTask.executable, "loggingTests")
            self.assertEqual( myTask.args, "")
            self.assertEqual( myTask.workingDir, "")
            self.assertEqual( myTask.timeout, 600)

            myTask = myTasks[5]
            self.assertTrue( isinstance(myTask, svntask.SvnTask) )
            self.assertEqual( myTask.trunkUrl, "https://company.com/repos/productv2/Common")
            self.assertEqual( myTask.workingDir, "/ProductBuilds/Common")
            self.assertFalse( myTask.preCleanWorkingDir)

            # Product V.3 project
            myProjName = "ProductV3"
            myTasks = myProjects[myProjName]['tasks']
            self.assertEqual( len(myTasks), 1 )
            self.assertEqual( len(filter(lambda task: isinstance(task, svntask.SvnTask), myTasks)), 1 )
            self.assertEqual( myProjects[myProjName]['emailFrom'], '')
            self.assertEqual( myProjects[myProjName]['emailTo'], [] )
            self.assertEqual( myProjects[myProjName]['failOnError'], False )
            self.assertEqual( myProjects[myProjName]['skipIfNoModifications'], False )

            myTask = myTasks[0]
            self.assertTrue( isinstance(myTask, svntask.SvnTask) )
            self.assertEqual( myTask.trunkUrl, "https://company.com/repos/productv2/server")
            self.assertEqual( myTask.workingDir, "/ProductBuilds/server")
            self.assertFalse( myTask.preCleanWorkingDir)

            # Product V.4 project 
            myProjName = "ProductV4"
            myTasks = myProjects[myProjName]['tasks']
            self.assertEqual( len(myTasks), 1 )
            self.assertEqual( len(filter(lambda task: isinstance(task, maketask.MakeTask), myTasks)), 1 )
            self.assertEqual( myProjects[myProjName]['failOnError'], True )
            self.assertEqual( myProjects[myProjName]['emailFrom'], '')
            self.assertEqual( myProjects[myProjName]['emailTo'], [] )
            self.assertEqual( myProjects[myProjName]['skipIfNoModifications'], False )

            myTask = myTasks[0]
            self.assertTrue( isinstance(myTask, maketask.MakeTask) )
            self.assertEqual( myTask.workingDir, "/ProductBuilds/SysInfra/Projects/common")
            self.assertEqual( myTask.args, "")
            self.assertEqual( myTask.timeout, 600);

            # Product V.5 project 
            myProjName = "ProductV5"
            self.assertEqual( myProjects[myProjName]['emailFrom'], 'buildserver@company.com')
            self.assertEqual( myProjects[myProjName]['emailTo'], ['developer@company.com', 'buildmaster@company.com'] )
            self.assertEqual( myProjects[myProjName]['emailFormat'], util.EmailFormat.plain )
            self.assertEqual( myProjects[myProjName]['emailServerHost'], 'localhost' )
            self.assertEqual( myProjects[myProjName]['emailServerPort'], 25 )
            self.assertEqual( myProjects[myProjName]['emailServerUsername'], None )
            self.assertEqual( myProjects[myProjName]['emailServerPassword'], None )            

            # Product V.6 project 
            myProjName = "ProductV6"
            self.assertEqual( myProjects[myProjName]['emailFrom'], 'buildserver@company.com')
            self.assertEqual( myProjects[myProjName]['emailTo'], ['developer@company.com'] )
            self.assertEqual( myProjects[myProjName]['emailFormat'], util.EmailFormat.html )
            self.assertEqual( myProjects[myProjName]['emailServerHost'], 'smtp.mymail.com' )
            self.assertEqual( myProjects[myProjName]['emailServerPort'], 2626 )
            self.assertEqual( myProjects[myProjName]['emailServerUsername'], 'jos' )
            self.assertEqual( myProjects[myProjName]['emailServerPassword'], 'topsecret' )

        except BaseException, e:
            print "Error. %s. %s. %s" % (type(e), str(e), util.formatTb())
            self.assert_(False)

    def testBadConfig1(self):
        self.assertRaises(ccpyconfparser.ParseError, ccpyconfparser.parse, "ccpy.conf.bad.1")

if __name__ == '__main__':
    if ( sys.version_info[0] < 2 or ( sys.version_info[0] == 2 and sys.version_info[1] < 5 ) ):
        print "Python 2.5 or higher is required for the program to run."
	exit(-1)
    unittest.main()
