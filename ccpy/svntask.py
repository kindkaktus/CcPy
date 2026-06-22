#
#  Andrei Korostelev <andrei at korostelev dot net>
#
#  Before using this product in any way please read the license agreement.
#  If you do not agree to the terms in this agreement you are not allowed
#  to use this product or parts of it. You can read this license in the
#  file named LICENSE.
#


"""
Svn task
"""

import os
import logging

from . import task
from .common import LoggerName
from .util import clean_directory, ensure_directory, run_command

Logger = logging.getLogger(LoggerName)


class SvnTask(task.Task):

    def __init__(self, url, workingDir, preCleanWorkingDir, runAsUser=None):
        task.Task.__init__(self)
        self._url = url
        self._workingDir = workingDir
        self._preCleanWorkingDir = preCleanWorkingDir
        self._runAsUser = runAsUser

    @property
    def url(self):
        return self._url

    @property
    def workingDir(self):
        return self._workingDir

    @property
    def preCleanWorkingDir(self):
        return self._preCleanWorkingDir

    @property
    def runAsUser(self):
        return self._runAsUser

    def __str__(self):
        return "Task: '%s', repository url: '%s', working directory: '%s', clean working directory before check out: '%s', run as user: '%s'" \
               % (self.__class__.__name__, self._url, self._workingDir, self._preCleanWorkingDir, self._runAsUser)

    def execute(self):
        myCmd = ''
        try:
            if self._preCleanWorkingDir:
                Logger.debug("Cleaning %s" % self._workingDir)
                myCleanStatus = clean_directory(self._workingDir, self._runAsUser)
                if not myCleanStatus['statusFlag']:
                    return myCleanStatus

            Logger.debug("Executing %s" % self)
            if (os.path.exists(self._workingDir +
                               "/.svn") and os.path.isdir(self._workingDir +
                                                          "/.svn")) or (os.path.exists(self._workingDir +
                                                                                       "/_svn") and os.path.isdir(self._workingDir +
                                                                                                                  "/_svn")):
                # svn working copy found, performing svn update
                Logger.debug("Updating %s" % self._workingDir)
                myCmd = "svn revert --recursive --non-interactive {0} && svn up --non-interactive {0}".format(
                    self._workingDir)
                myReturnCode, myStdout = run_command(
                    myCmd,
                    aRunAsUser=self._runAsUser,
                    aLogger=Logger)

                if myReturnCode != 0:
                    return {
                        "statusFlag": False,
                        "statusDescr": "'%s' finished with return code %d." %
                        (myCmd,
                         myReturnCode),
                        "output": myStdout.rstrip()}
                return {"statusFlag": True,
                        "statusDescr": "'%s' completed successfully." % myCmd,
                        "output": myStdout.rstrip()}

            # No svn working copy found, performing svn checkout
            Logger.debug("Checking out '%s' to %s" % (self._url, self._workingDir))
            myEnsureDirStatus = ensure_directory(self._workingDir, self._runAsUser, Logger)
            if not myEnsureDirStatus['statusFlag']:
                return myEnsureDirStatus
            myCmd = "svn co --non-interactive %s %s" % (self._url, self._workingDir)
            myReturnCode, myStdout = run_command(
                myCmd,
                aRunAsUser=self._runAsUser,
                aLogger=Logger)

            if myReturnCode != 0:
                return {
                    "statusFlag": False,
                    "statusDescr": "'%s' finished with return code %d." %
                    (myCmd,
                     myReturnCode),
                    "output": myStdout.rstrip()}
            return {"statusFlag": True,
                    "statusDescr": "'%s' completed successfully." % myCmd,
                    "output": myStdout.rstrip()}
        except Exception as e:
            return {"statusFlag": False,
                    "statusDescr": "Failed to execute '%s'. Error: %s" % (myCmd, str(e))}
