#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
#  Andrei Korostelev <andrei at korostelev dot net>
#
#  Before using this product in any way please read the license agreement.
#  If you do not agree to the terms in this agreement you are not allowed
#  to use this product or parts of it. You can read this license in the
#  file named LICENSE.
#
"""
CcPy daemon

Usage ./ccpyd.py [--fg]
   --fg - run in foreground (default is to run in background)
"""

import sys
import datetime
import logging

import ccpy.ccpydconfparser as ccpydconfparser
import ccpy.ccpyconfparser as ccpyconfparser
from ccpy.ccpystate import CcPyState, PrjStates
import ccpy.util as util
import ccpy.maketask as maketask
import ccpy.exectask as exectask
import ccpy.common as common
import ccpy.report as report


def execTasks(aCcPyConf):
    """ Execute tasks from the ccpy project configuration file and send email report for each project """
    Logger = logging.getLogger(common.LoggerName)
    Logger.debug("Loading configuration from %s" % aCcPyConf)
    myProjects = ccpyconfparser.parse(aCcPyConf)
    Logger.debug("%u project(s) queued for integration", len(myProjects))

    # Iterate thru projects
    for prjName, prjVal in myProjects:
        myPrjStart = datetime.datetime.today()
        myNumSucceededTasks = 0
        myNumSucceededTasksWithWarning = 0
        myNumFailedTasks = 0
        myFailedBecauseOfTaskError = False
        myTasksStatus = []

        # Iterate thru tasks
        for task in prjVal['tasks']:
            myTaskStart = datetime.datetime.today()

            # execute the task
            myTaskExecStatus = task.execute()
            myTaskStatus = {'name': task.__class__.__name__,
                            'description': myTaskExecStatus['statusDescr'],
                            'startTime': myTaskStart,
                            'endTime': datetime.datetime.today(),
                            }
            if myTaskExecStatus['statusFlag']:
                myNumSucceededTasks += 1
                if "warning" in myTaskExecStatus and myTaskExecStatus["warning"]:
                    myTaskStatus['status'] = "WARNING"
                    myNumSucceededTasksWithWarning += 1
                else:
                    myTaskStatus['status'] = "OK"
                if isinstance(task, maketask.MakeTask) or isinstance(task, exectask.ExecTask):
                    myTaskStatus['allocatedTime'] = task.timeout
            else:
                myTaskStatus['status'] = 'FAILED'
                myNumFailedTasks += 1
                if prjVal['failOnError'] or not isinstance(task, exectask.ExecTask):
                    # fail the entire build on non-executable task error and on on executable task error when 'failOnError' is set
                    myFailedBecauseOfTaskError = True
            if 'stdout' in myTaskExecStatus:
                myTaskStatus['stdout'] = myTaskExecStatus['stdout']
            if 'stderr' in myTaskExecStatus:
                myTaskStatus['stderr'] = myTaskExecStatus['stderr']

            myTasksStatus.append(myTaskStatus)

            myTaskStatus2Log = dict(myTaskStatus)
            myTaskStatus2Log['startTime'] = str(myTaskStatus2Log['startTime'])
            myTaskStatus2Log['endTime'] = str(myTaskStatus2Log['endTime'])
            if 'allocatedTime' in myTaskStatus2Log:
                myTaskStatus2Log['allocatedTime'] = "%s seconds" % myTaskStatus2Log['allocatedTime']
            Logger.debug('  Task finished. Status: %s', myTaskStatus2Log)

            if myFailedBecauseOfTaskError:
                break
        # End: Iterate thru tasks

        myPrjEnd = datetime.datetime.today()

        myCcPyState = CcPyState()
        myOldPrjState = myCcPyState.getPrjState(prjName)

        if myNumFailedTasks > 0:
            # fail
            myCcPyState.setPrjState(prjName, PrjStates.FAILED)
            myPrjStatusStr = str(PrjStates.FAILED)
        elif myNumSucceededTasks > 0:
            # success
            myCcPyState.setPrjState(prjName, PrjStates.OK)
            if myNumSucceededTasksWithWarning > 0:
                myPrjStatusStr = "WARNING %s" % (
                    ' (FIXED)' if myOldPrjState == PrjStates.FAILED else '', )
            else:
                myPrjStatusStr = "%s%s" % (
                    PrjStates.OK, ' (FIXED)' if myOldPrjState == PrjStates.FAILED else '')
        else:
            # nothing is ran, use yesterday weather
            myCcPyState.setPrjState(prjName, myOldPrjState)
            myPrjStatusStr = str(myOldPrjState)

        Logger.debug(
            "Finished with project %s. Status: %s. %u task(s) SUCCEEDED of which %d have WARNINGs, %u task(s) FAILED.  Elapsed time: %s (started %s, ended %s)" %
            (prjName,
             myPrjStatusStr,
             myNumSucceededTasks,
             myNumSucceededTasksWithWarning,
             myNumFailedTasks,
             util.formatTimeDelta(myPrjEnd - myPrjStart),
             str(myPrjStart),
             str(myPrjEnd)))
        if len(prjVal['emailTo']):
            Logger.debug(
                "Sending email notification as %s to %s via %s:%d (security: %s)" %
                (prjVal['emailFormat'],
                 ", ".join(
                    prjVal['emailTo']),
                    prjVal['emailServerHost'],
                    prjVal['emailServerPort'],
                    prjVal['emailServerSecurity']))
            mySubj = "Integration status for %s: %s" % (prjName, myPrjStatusStr)
            myBody = report.makeEmailBody(prjVal['emailFormat'],
                                          {'prjName': prjName,
                                           'prjStatus': myPrjStatusStr,
                                           'numSucceededTasks': myNumSucceededTasks,
                                           'numFailedTasks': myNumFailedTasks,
                                           'numSucceededTasksWithWarning': myNumSucceededTasksWithWarning,
                                           'startTime': myPrjStart,
                                           'endTime': myPrjEnd,
                                           },
                                          myTasksStatus,
                                          myFailedBecauseOfTaskError)
            myAttachmentText = report.makeAttachmentText(
                prjVal['emailFormat'],
                myTasksStatus,
                myFailedBecauseOfTaskError)
            util.sendEmailNotification(prjVal['emailFrom'],
                                       prjVal['emailTo'],
                                       mySubj,
                                       myBody,
                                       myAttachmentText,
                                       prjVal['emailAttachments'],
                                       prjVal['emailFormat'],
                                       prjVal['emailServerHost'],
                                       prjVal['emailServerPort'],
                                       prjVal['emailServerSecurity'],
                                       prjVal['emailServerUsername'],
                                       prjVal['emailServerPassword'])
    # Iterate thru projects


def run_in_fg(argv):
    return "--fg" in argv


def main(argv):
    if sys.version_info[0] < 2 or (sys.version_info[0] == 2 and sys.version_info[1] < 5):
        sys.stderr.write("Python 2.5 or higher is required for the program to run.")
        return -1

    try:
        if run_in_fg(argv):
            print("Starting in foreground")
        else:
            print("Starting in background")
            util.daemonize()

        myCcPydConf = ccpydconfparser.parse()
        if not myCcPydConf['logging']:
            myCcPydConf['logFile'] = '/dev/null'
        Logger = util.initLogger(
            common.LoggerName,
            myCcPydConf['logFile'],
            common.ProductName +
            ' v.' +
            common.ProductVersion,
            myCcPydConf['logLevel'])
    except Exception as e:
        sys.stderr.write("%s. %s. %s" % (type(e), str(e), util.formatTb()))
        return -1

    try:
        mySysSingleton = util.SysSingleton(common.DaemonName)
        myCcPyConf = myCcPydConf['ccpyConfig']
        execTasks(myCcPyConf)
        util.closeLogger(Logger)
        return 0
    except BaseException as e:
        Logger.error("%s: %s. %s" % (type(e), str(e), util.formatTb()))
        util.closeLogger(Logger)
        return -1
    except:
        Logger.error("Unexpected error")
        util.closeLogger(Logger)
        return -2

    Logger.error("We should never get here.")
    return -3


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
