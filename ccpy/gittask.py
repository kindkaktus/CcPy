#
#  Andrei Korostelev <andrei at korostelev dot net>
#
#  Before using this product in any way please read the license agreement.
#  If you do not agree to the terms in this agreement you are not allowed
#  to use this product or parts of it. You can read this license in the
#  file named LICENSE.
#


"""
Git task
"""

import os
import subprocess
import logging

from . import task
from .common import LoggerName
from .util import to_unicode, clean_directory

Logger = logging.getLogger(LoggerName)


class GitTask(task.Task):

    def __init__(self, url, workingDir, preCleanWorkingDir):
        task.Task.__init__(self)
        self._url = url
        self._workingDir = workingDir
        self._preCleanWorkingDir = preCleanWorkingDir

    @property
    def url(self):
        return self._url

    @property
    def workingDir(self):
        return self._workingDir

    @property
    def preCleanWorkingDir(self):
        return self._preCleanWorkingDir

    def __str__(self):
        return "Task: '%s', repository url: '%s', working directory: '%s', clean working directory before check out: '%s'" \
               % (self.__class__.__name__, self._url, self._workingDir, self._preCleanWorkingDir)

    def execute(self):
        if self._preCleanWorkingDir:
            Logger.debug("Cleaning %s" % self._workingDir)
            myCleanStatus = clean_directory(self._workingDir)
            if not myCleanStatus['statusFlag']:
                return myCleanStatus

        myCmd = ''
        try:

            Logger.debug("Executing %s" % self)
            if (os.path.exists(self._workingDir + "/.git")
                    and os.path.isdir(self._workingDir + "/.git")):
                # Found git repo, getting the latest upstream
                Logger.debug("Updating %s" % self._workingDir)
                myCmd = "git fetch --all && git reset --hard @{upstream}"
                myProcess = subprocess.Popen(
                    myCmd,
                    shell=True,
                    cwd=self._workingDir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE)
                myStdout, myStderr = myProcess.communicate()
                myStdout = to_unicode(myStdout, Logger)
                myStderr = to_unicode(myStderr, Logger)

                if myProcess.returncode != 0:
                    return {
                        "statusFlag": False,
                        "statusDescr": "'%s' in %s finished with return code %d." %
                        (myCmd,
                         self._workingDir,
                         myProcess.returncode),
                        "stdout": myStdout.rstrip(),
                        "stderr": myStderr.rstrip()}
                return {
                    "statusFlag": True,
                    "statusDescr": "'%s' in %s completed successfully." %
                    (myCmd,
                     self._workingDir),
                    "stdout": myStdout.rstrip(),
                    "stderr": myStderr.rstrip()}

            # No git repository found, cloning the repo
            Logger.debug("Cloning '%s' to %s" % (self._url, self._workingDir))
            if not os.path.exists(self._workingDir):
                os.makedirs(self._workingDir)
            myCmd = "git clone %s %s" % (self._url, self._workingDir)
            myProcess = subprocess.Popen(
                myCmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)
            myStdout, myStderr = myProcess.communicate()
            myStdout = to_unicode(myStdout, Logger)
            myStderr = to_unicode(myStderr, Logger)

            if myProcess.returncode != 0:
                return {
                    "statusFlag": False,
                    "statusDescr": "'%s' finished with return code %d." %
                    (myCmd,
                     myProcess.returncode),
                    "stdout": myStdout.rstrip(),
                    "stderr": myStderr.rstrip()}
            return {"statusFlag": True,
                    "statusDescr": "'%s' completed successfully." % myCmd,
                    "stdout": myStdout.rstrip(),
                    "stderr": myStderr.rstrip()}
        except OSError as e:
            return {"statusFlag": False,
                    "statusDescr": "Failed to execute '%s'. Error: %s" % (myCmd, str(e))}
