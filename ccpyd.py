#
#  HeadURL : $HeadURL: svn://korostelev.net/CcPy/Trunk/ccpyd.py $
#  Id      : $Id: ccpyd.py 210 2012-04-17 12:14:14Z akorostelev $
#
#  Copyright (c) 2008-2009, Andrei Korostelev <andrei at korostelev dot net>
#
#  Before using this product in any way please read the license agreement.
#  If you do not agree to the terms in this agreement you are not allowed
#  to use this product or parts of it. You can read this license in the
#  file named LICENSE.
#
"""
CcPy daemon
"""

import sys
import datetime
import logging

import ccpy.ccpydconfparser as ccpydconfparser
import ccpy.ccpyconfparser as ccpyconfparser
from ccpy.ccpystate import CcPyState, PrjStates
import ccpy.util as util
import ccpy.svntask as svntask
import ccpy.maketask as maketask
import ccpy.exectask as exectask
import ccpy.common as common
import ccpy.report as report
import ccpy.util as util

def execTasks(aCcPyConf):
    """ Execute tasks from the ccpy project configuration file and send email report for each project """
    Logger = logging.getLogger(common.LoggerName)
    Logger.debug("Loading configuration from %s" % aCcPyConf)
    myProjects = ccpyconfparser.parse(aCcPyConf)
    Logger.debug("%u project(s) queued for integration", len(myProjects))

    # Iterate thru projects
    for prjName,prjVal in myProjects: 
        myPrjStart = datetime.datetime.today()
        myNumSucceededTasks, myNumFailedTasks = 0,0
        myFailOnErrorSetting = prjVal['failOnError']
        mySkipIfNoModSetting = prjVal['skipIfNoModifications']
        mySkipTasks = None
        myFailedBecauseOfTaskError = False
        myTasksStatus = []

        # Iterate thru tasks
        for task in prjVal['tasks']:
            myTaskStart = datetime.datetime.today()
            if mySkipIfNoModSetting and isinstance(task, svntask.SvnTask) and (mySkipTasks is None or mySkipTasks):
                mySkipTasks = (task.modificationsStatus == svntask.SvrModifications.notExist)

            myTaskStatus = {'name':task.__class__.__name__}
            if mySkipTasks:
                myTaskStatus['status'] = 'SKIPPED (no modifications detected)'
                myTaskStatus['description'] = str(task)
            else:
                myTaskExecStatus = task.execute()
                myTaskStatus['description'] = myTaskExecStatus['statusDescr']
                myTaskStatus['elapsedTime'] = datetime.datetime.today()-myTaskStart
                if myTaskExecStatus['statusFlag']:
                    myTaskStatus['status'] = 'OK'
                    if isinstance(task, maketask.MakeTask) or isinstance(task, exectask.ExecTask):
                        myTaskStatus['allocatedTime'] = task.timeout
                    myNumSucceededTasks += 1
                else:
                    myTaskStatus['status'] = 'FAILED'
                    myNumFailedTasks += 1
                    if myFailOnErrorSetting:
                        myFailedBecauseOfTaskError = True
                if myTaskExecStatus.has_key('stdout'):
                    myTaskStatus['stdout'] = myTaskExecStatus['stdout']
                if myTaskExecStatus.has_key('stderr'):
                    myTaskStatus['stderr'] = myTaskExecStatus['stderr']

            myTasksStatus.append(myTaskStatus)
            Logger.debug('  Task finished. Status: %s', myTaskStatus)
            if myFailedBecauseOfTaskError:
                break
  	# End: Iterate thru tasks

        myPrjEnd = datetime.datetime.today()

        myCcPyState = CcPyState()
        myOldPrjState = myCcPyState.getPrjState(prjName)
        if myNumFailedTasks:  myPrjState = PrjStates.FAILED
        elif myNumSucceededTasks: myPrjState = PrjStates.OK
        else: myPrjState = myOldPrjState
        myCcPyState.setPrjState(prjName, myPrjState)    

        myPrjStatus = "%s%s" % (myPrjState, ' (FIXED)' if myOldPrjState==PrjStates.FAILED and myPrjState==PrjStates.OK else '')
        myNumSkippedTasks  = len(prjVal['tasks']) - myNumFailedTasks - myNumSucceededTasks
        Logger.debug("Finished with project %s. Status: %s. %u task(s) SUCCEEDED, %u task(s) FAILED, %u task(s) SKIPPED.  Elapsed time: %s" 
                     % (prjName, myPrjStatus, myNumSucceededTasks, myNumFailedTasks, myNumSkippedTasks, util.formatTimeDelta(myPrjEnd-myPrjStart)) )   
        if len(prjVal['emailTo']):
          Logger.debug("Sending email notification to %s" % (", ".join(prjVal['emailTo'])) )   
          mySubj = "Integration status for %s: %s" % (prjName, myPrjStatus)
          myBody = report.makeEmailBody(prjVal['emailFormat'], 
                                {'prjName':prjName, 'prjStatus':myPrjStatus, 
                                 'numSucceededTasks':myNumSucceededTasks, 'numFailedTasks':myNumFailedTasks, 'numSkippedTasks':myNumSkippedTasks,
                                 'elapsedTime': myPrjEnd-myPrjStart },
                                myTasksStatus,
                                myFailedBecauseOfTaskError)
          util.sendEmailNotification(prjVal['emailFrom'], prjVal['emailTo'], mySubj, myBody, prjVal['emailFormat'], prjVal['emailServerHost'], prjVal['emailServerPort'], prjVal['emailServerUsername'], prjVal['emailServerPassword'])
    # Iterate thru projects


def calcExecWaitTime(aParsedExecTime):
    """ Return a number of seconds before tasks execution """
    myNowDateTime  = datetime.datetime.today()
    myExecDateTime = datetime.datetime(myNowDateTime.year, myNowDateTime.month, myNowDateTime.day, aParsedExecTime.hour, aParsedExecTime.minute)
    if myExecDateTime < myNowDateTime:
        myExecDateTime += datetime.timedelta(days=1)
    myDelta = myExecDateTime - myNowDateTime
    assert myDelta.days in [0,1], "Invalid time delta"
    myWaitTimeSec = myDelta.days*24*60 + myDelta.seconds
    Logger = logging.getLogger(common.LoggerName)
    Logger.debug("Execution is scheduled for %s. Wait %u sec..." % (myExecDateTime, myWaitTimeSec) )
    return myWaitTimeSec

def main(argv=None):
    if  sys.version_info[0] < 2 or ( sys.version_info[0] == 2 and sys.version_info[1] < 5 ):
        print >>sys.stderr,"Python 2.5 or higher is required for the program to run."
        return -1
        
    if argv is None:
        argv = sys.argv       
    try:
        #import os, pwd
        #util.daemonize(pwd.getpwuid(os.getuid()).pw_dir)
        myScheduleArg = "" if len(argv) < 2 else argv[1]
        util.daemonize()
        myCcPydConf = ccpydconfparser.parse()
        if not myCcPydConf['logging']:
            myCcPydConf['logFile'] = '/dev/null'
        Logger = util.initLogger( common.LoggerName, myCcPydConf['logFile'], common.ProductName+' v.'+common.ProductVersion, myCcPydConf['logLevel'] )
    except Exception, e:
        print >>sys.stderr,"%s. %s. %s" % (type(e), str(e), util.formatTb())
        return -1

    try:
        mySysSingleton = util.SysSingleton(common.DaemonName)
        myCcPyConf = myCcPydConf['ccpyConfig']
        if (myScheduleArg == "--force-once") or (not myCcPydConf['schedule']):
            Logger.debug("Executing tasks once")
            execTasks(myCcPyConf)
            util.closeLogger(Logger)
            return 0
    except BaseException, e:
        Logger.error("%s: %s. %s" % (type(e), str(e), util.formatTb()))
        util.closeLogger(Logger)
        return -1
    except: 
        Logger.error("Unexpected error")
        util.closeLogger(Logger)
        return -2

    # 'schedule' mode
    if myScheduleArg == "--force-continue":
        Logger.debug("Executing tasks and continue")
        try:
            execTasks(myCcPyConf)
        except BaseException, e:
            Logger.error("%s: %s. %s.\nTolerating the error." % (type(e), str(e), util.formatTb()))
        except: 
            Logger.error("Unexpected error. \nTolerating the error.")
    myParsedExecTime = myCcPydConf['scheduleTime']
    while True: 
        myWaitTimeSec = calcExecWaitTime(myParsedExecTime)
        util.wait(myWaitTimeSec)
        Logger.debug("Executing tasks (scheduled)")
        try:
            execTasks(myCcPyConf)
        except BaseException, e:
            Logger.error("%s: %s. %s.\nTolerating the error." % (type(e), str(e), util.formatTb()))
        except: 
            Logger.error("Unexpected error. \nTolerating the error.")
            
    Logger.error("We should never get here.")
    return -3

if __name__ == "__main__":
    sys.exit(main())