#!/usr/bin/env python
# -*- coding: UTF-8 -*-

#
#  Copyright (c) 2008-2014, Andrei Korostelev <andrei at korostelev dot net>
#
#  Before using this product in any way please read the license agreement.
#  If you do not agree to the terms in this agreement you are not allowed
#  to use this product or parts of it. You can read this license in the
#  file named LICENSE.
#


"""
Make task
"""

import os
import sys
import datetime
import time
import subprocess
import logging
import threading

from . import task
from .common import LoggerName
from . import util

Logger = logging.getLogger(LoggerName)

class MakeTask(task.Task):
    def __init__(self, workingDir, args, timeout):
        task.Task.__init__(self)
        self._workingDir = workingDir
        self._args  = args
        self._timeout = timeout
    
    @property
    def workingDir(self):
        return  self._workingDir
        
    @property
    def args(self):
        return  self._args

    @property
    def timeout(self):
        return  self._timeout

    def __str__(self):
        return "Task: '%s', working directory: '%s', build args: '%s', timeout: %u sec" \
               % (self.__class__.__name__, self._workingDir, self._args, self._timeout )
  
    def execute(self):
        try:
            Logger.debug("Executing %s" % self) 
            myCmd = ("make %s" % self._args) if len(self._args) else "make"
            myStart = datetime.datetime.now()

            # 'preexec_fn = os.setpgrp' is needed to create a new process group for a subprocess 
            # which will be used by os.killpg to kill the subprocess with its children
            # Without specifying 'preexec_fn = os.setpgrp' the subprocess would use the parent's (i.e. python's)
            # group id and therefore os.killpg would kill our script ;(
            myProcess = subprocess.Popen(myCmd, shell=True, cwd=self._workingDir, stderr=subprocess.PIPE, stdout=subprocess.PIPE, preexec_fn = os.setpgrp)     
            myPgid = os.getpgid(myProcess.pid) # grab pgid immidiately because we could not do it after the group leader dies
                            
            myStdoutConsumer = util.ProcOutputConsumerThread(myProcess, True, Logger)
            myStderrConsumer = util.ProcOutputConsumerThread(myProcess, False, Logger)
            myStdoutConsumer.start()
            myStderrConsumer.start()
            
            while myProcess.poll() is None:
                time.sleep(1)
                myNow = datetime.datetime.now()
                if util.getTotalSeconds(myNow - myStart) > self._timeout:
                    Logger.warning("The execution of %s (pid %d, pgid %d) is timed out after %d seconds, killing all processes of its group" % (myCmd, myPgid, myProcess.pid, self._timeout))
                    util.kill_chld_pg(myPgid)
                    myStdoutConsumer.join()
                    myStderrConsumer.join()
                    return { "statusFlag" : False, 
                             "statusDescr" : "'%s' in %s terminated because of timeout (after %u seconds)." % (myCmd, self._workingDir, self._timeout),
                             "stdout" : myStdoutConsumer.out,
                             "stderr" : myStderrConsumer.out}

            ## This may happen that we're here because parent finished but some its childern are not, 
            ## so we need to cleanup any possible leftovers also to make sure we can grab stdout/stderr below without blocking
            Logger.debug("The execution of %s (pid %d, pgid %d) is finished, cleaning up by killing any remaining processes of its group" % (myCmd, myPgid, myProcess.pid))
            util.kill_chld_pg(myPgid)
            myStdoutConsumer.join()
            myStderrConsumer.join()
            if myProcess.returncode != 0:
                return { "statusFlag" : False,
                         "statusDescr" : "'%s' in %s finished with return code %d." % (myCmd , self._workingDir, myProcess.returncode),
                         "stdout" : myStdoutConsumer.out,
                         "stderr" : myStderrConsumer.out }
            return { "statusFlag" : True, 
                     "statusDescr" : "'%s' in '%s' completed successfully." % (myCmd, self._workingDir), 
                     "stdout" : myStdoutConsumer.out,
                     "stderr" : myStderrConsumer.out }
        except OSError as e:
           return {"statusFlag" : False, 
                   "statusDescr" : "Failed to execute '%s' in %s. Error: %s" % (myCmd, self._workingDir, str(e))}

