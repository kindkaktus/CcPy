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
Svn task
"""

import os
import subprocess
import logging

from . import task
from .common import LoggerName
from .util import to_utf8, to_unicode

Logger = logging.getLogger(LoggerName)

class SvrModifications:
    exist, notExist, notWorkingCopy = range(3)

class SvnTask(task.Task):
    def __init__(self, anArgs):
        task.Task.__init__(self)
        self._trunkUrl = anArgs['trunkUrl']
        self._workingDir = anArgs['workingDir']
        self._preCleanWorkingDir = anArgs['preCleanWorkingDir']

    @property
    def trunkUrl(self):
        return  self._trunkUrl

    @property
    def workingDir(self):
        return  self._workingDir

    @property
    def preCleanWorkingDir(self):
        return  self._preCleanWorkingDir

    def __str__(self):
        return "Task: '%s', trunk url: '%s', working directory: '%s', clean working directory before check out: '%s'" \
               % (self.__class__.__name__,  self._trunkUrl, self._workingDir, self._preCleanWorkingDir )

    def execute(self):            
        if self._preCleanWorkingDir:
            myCleanStatus = self._cleanWorkingDir()
            if not myCleanStatus['statusFlag']:
                return myCleanStatus
                    
        myCmd = ''
        try:
                    
            Logger.debug("Executing %s" % self)
            if  (os.path.exists(self._workingDir+"/.svn") and os.path.isdir(self._workingDir+"/.svn")) or \
                (os.path.exists(self._workingDir+"/_svn") and os.path.isdir(self._workingDir+"/_svn")):
                # Performing svn update
                Logger.debug("Updating %s" % self._workingDir)
                myCmd = "svn up --non-interactive"
                myProcess = subprocess.Popen(myCmd, shell=True, cwd=self._workingDir, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                myStdout, myStderr  = myProcess.communicate()
                myStdout = to_unicode(myStdout, Logger)
                myStderr = to_unicode(myStderr, Logger)

                if myProcess.returncode != 0:
                    return { "statusFlag" : False, 
                             "statusDescr" : "'svn update' to %s finished with return code %d." % (self._workingDir, myProcess.returncode ),
                             "stdout" : myStdout.rstrip(),
                             "stderr" : myStderr.rstrip() }
                return { "statusFlag" : True, 
                         "statusDescr" : "'svn update' to %s completed successfully." % self._workingDir, 
                         "stdout" : myStdout.rstrip(),
                         "stderr" : myStderr.rstrip() }
                         
            # Performing svn checkout
            Logger.debug("Checking out '%s' to %s" % (self._trunkUrl, self._workingDir))
            if not os.path.exists(self._workingDir):
                os.makedirs(self._workingDir)
            #myTrunkUrl = urllib.quote(self._trunkUrl)
            myCmd = "svn co --non-interactive %s %s" % ( self._trunkUrl, self._workingDir) 
            myProcess = subprocess.Popen(myCmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            myStdout, myStderr  = myProcess.communicate()
            myStdout = to_unicode(myStdout, Logger)
            myStderr = to_unicode(myStderr, Logger)
            
            if myProcess.returncode != 0:
                return { "statusFlag" : False,  
                         "statusDescr" : "'svn checkout' for '%s' to %s finished with return code %d." % (self._trunkUrl, self._workingDir, myProcess.returncode),
                         "stdout" : myStdout.rstrip(),
                         "stderr" : myStderr.rstrip() }
            return { "statusFlag" : True, 
                     "statusDescr" : "'svn checkout' for '%s' to %s completed successfully." % (self._trunkUrl, self._workingDir),
                     "stdout" : myStdout.rstrip(),
                     "stderr" : myStderr.rstrip() }
        except OSError as e:
           return {"statusFlag" : False, 
                   "statusDescr" : "Failed to execute '%s'. Error: %s" % (myCmd, str(e))}


    @property
    def modificationsStatus(self):
        """ 
        Return working copy modifications status on the server 

        Return SvrModifications
        """
        Logger.debug("Checking whether server modifications exist. %s" % self)
        if ( not os.path.exists(self._workingDir+"/.svn") or not os.path.isdir(self._workingDir+"/.svn")) and \
           ( not os.path.exists(self._workingDir+"/_svn") or not os.path.isdir(self._workingDir+"/_svn")):
           Logger.debug("The specified working copy dir appears not to be a valid svn working copy directory")   
           return SvrModifications.notWorkingCopy
                     
        myCmd = "svn status --non-interactive -u | awk '{print $1}' | grep -q '*'"
        myProcess = subprocess.Popen(myCmd + " > /dev/null" , shell=True, cwd=self._workingDir, stderr=subprocess.PIPE)
        myStderr = myProcess.communicate()[1]
        if myProcess.returncode != 0:
            if len(myStderr):
                if myStderr.find('is not a working copy') != -1:
                    Logger.debug("The specified working copy dir appears not to be a valid svn working copy directory")   
                    return SvrModifications.notWorkingCopy
                raise RuntimeError("'%s'command for '%s' working dir finished with return code %d. Sterrr: %s" % \
                                    (myCmd, self._workingDir , myProcess.returncode, myStderr) )
            Logger.debug("No modifications exist on the server")   
            return SvrModifications.notExist
        Logger.debug("Modifications exist on the server")   
        return SvrModifications.exist
        
    def _cleanWorkingDir(self):
        Logger.debug("Cleaning %s" % self._workingDir)
        if os.path.exists(self._workingDir):
            if os.path.isdir(self._workingDir):
                myCmd = "rm -rf ./* ./.*[!.]* ./...*"
                myProcess = subprocess.Popen(myCmd, shell=True, cwd=self._workingDir, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                myStdout, myStderr  = myProcess.communicate()
                if myProcess.returncode != 0:            
                    return { "statusFlag" : False, 
                             "statusDescr" : "'%s' in %s finished with return code %d." % (myCmd, self._workingDir, myProcess.returncode ),
                             "stdout" : myStdout.rstrip(),
                             "stderr" : myStderr.rstrip() }
            else:
                os.remove(self._workingDir)
        return { "statusFlag" : True}
             


        
