#
#  Copyright (c) 2008-2014, Andrei Korostelev <andrei at korostelev dot net>
#
#  Before using this product in any way please read the license agreement.
#  If you do not agree to the terms in this agreement you are not allowed
#  to use this product or parts of it. You can read this license in the
#  file named LICENSE.
#

"""
Execution task
"""

import os
import sys
import datetime
import time
import subprocess
import logging

from . import task
from . import util
from .common import LoggerName

Logger = logging.getLogger(LoggerName)

class ExecTask(task.Task):
    def __init__(self, anArgs):
        task.Task.__init__(self)
        self._executable = anArgs['executable']
        self._args       = anArgs['args']
        self._workingDir = anArgs['workingDirectory']
        self._timeout    = anArgs['timeout']
        self._warningExitCode = anArgs.get('warningExitCode', None)

    @property
    def workingDir(self):
        return self._workingDir
        
    @property
    def executable(self):
        return self._executable

    @property
    def args(self):
        return self._args

    @property
    def timeout(self):
        return self._timeout
        
    @property
    def warningExitCode(self):
        return self._warningExitCode

    def __str__(self):
        return "Task: '%s', working directory: '%s', executable: '%s', args: '%s', timeout: %u sec, warning exit code: %s" \
               % (self.__class__.__name__, self._workingDir, self._executable, self._args, self._timeout, self._warningExitCode if self._warningExitCode else "<not defined>")

    def execute(self):
        try:
            Logger.debug("Executing %s" % self)   
            myStart = datetime.datetime.now()

            # 'preexec_fn = os.setpgrp' is needed to create a new process group for a subprocess 
            # which will be used by os.killpg to kill the subprocess with its children
            # Without specifying 'preexec_fn = os.setpgrp' the subprocess would use the parent's (i.e. python's)
            # group id and therefore os.killpg would kill our script ;(
            myCmd = [self._executable] + self._args.split()
            myEnv = os.environ.copy()
            myEnv['PATH'] += ":."  # allows launching executables from cwd
            myProcess = subprocess.Popen(myCmd, shell=False, cwd=self._workingDir, stderr=subprocess.PIPE, stdout=subprocess.PIPE, preexec_fn = os.setpgrp, env= myEnv)
            myPgid = os.getpgid(myProcess.pid) # grab pgid immidiately because we could not do it after the group leader dies

            myStdoutConsumer = util.ProcOutputConsumerThread(myProcess, True, Logger)
            myStderrConsumer = util.ProcOutputConsumerThread(myProcess, False, Logger)
            myStdoutConsumer.start()
            myStderrConsumer.start()
            
            while myProcess.poll() is None:
                time.sleep(1)
                myNow = datetime.datetime.now()
                
                # timeout
                if util.getTotalSeconds(myNow - myStart) > self._timeout:
                    Logger.warning("The execution of %s (pid %d, pgid %d) is timed out after %d seconds, killing all processes of its group" % (myCmd, myPgid, myProcess.pid, self._timeout))
                    util.kill_chld_pg(myPgid)
                    myStdoutConsumer.join()
                    myStderrConsumer.join()
                    return { "statusFlag" : False, 
                             "statusDescr" : "The execution of '%s %s' in %s was terminated because of timeout (after %u seconds)." % (self._executable, self._args, self._workingDir, self._timeout),
                             "stdout" : myStdoutConsumer.out,
                             "stderr" : myStderrConsumer.out}

            ## This may happen that we're here because parent finished but some its childern are not, 
            ## so we need to cleanup any possible leftovers also to make sure we can grab stdout/stderr below without blocking
            Logger.debug("The execution of %s (pid %d, pgid %d) is finished, cleaning up by killing any remaining processes of its group" % (myCmd, myPgid, myProcess.pid))
            util.kill_chld_pg(myPgid)
            myStdoutConsumer.join()
            myStderrConsumer.join()
            
            # success
            if myProcess.returncode == 0:
                return { "statusFlag" : True, 
                         "statusDescr" : "The execution of '%s %s' in %s completed successfully." % (self._executable, self._args, self._workingDir),
                         "stdout" : myStdoutConsumer.out,
                         "stderr" : myStderrConsumer.out }
                         
            # warning exit code
            if self._warningExitCode is not None and myProcess.returncode == self._warningExitCode:
                return { "statusFlag" : True,
                         "warning" : True,
                         "statusDescr" : "The execution of '%s %s' in %s completed with warning and return code %d." % (self._executable, self._args, self._workingDir, myProcess.returncode),
                         "stdout" : myStdoutConsumer.out,
                         "stderr" : myStderrConsumer.out}
            
            # error
            return { "statusFlag" : False,
                     "statusDescr" : "The execution of '%s %s' in %s finished with return code %d." % (self._executable, self._args, self._workingDir, myProcess.returncode),
                     "stdout" : myStdoutConsumer.out,
                     "stderr" : myStderrConsumer.out }
        except OSError as e:
            return {"statusFlag" : False, 
                    "statusDescr" : "Failed to execute '%s %s' in %s. Error: %s" % (self._executable, self._args, self._workingDir, str(e))}


