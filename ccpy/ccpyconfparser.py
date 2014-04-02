#
#  Copyright (c) 2008-2014, Andrei Korostelev <andrei at korostelev dot net>
#
#  Before using this product in any way please read the license agreement.
#  If you do not agree to the terms in this agreement you are not allowed
#  to use this product or parts of it. You can read this license in the
#  file named LICENSE.
#

"""
CcPy project configuration file parser
"""

import xml.sax
import logging
from copy import deepcopy

from .common import LoggerName
from .util import EmailFormat, formatTb
from . import svntask
from . import maketask
from . import exectask

Logger = logging.getLogger(LoggerName)
DefCcPyConfigFileName = "/etc/ccpy.conf"

class Projects:
    def __init__(self):
        self._projects = []
        self.cur = 0
        
    def exists(self, name):
       for project in self._projects:
           if project['name'] == name:
               return True
       return False
       
    def append(self, name, tasks = None, emailFrom = "", emailTo = None, emailFormat = EmailFormat.html, emailServerHost = 'localhost', emailServerPort = 25, emailServerUsername = None, emailServerPassword = None, failOnError = True, skipIfNoModifications = False):
        if self.exists(name):
            raise Exception("Failed to add project because the project named '%s' already exists" % name)
        if tasks is None:
            tasks = []
        if emailTo is None:
            emailTo = []
        self._projects.append({'name':name, 'tasks': tasks, 'emailFrom':emailFrom, 'emailTo':emailTo, 'emailFormat': emailFormat, 'emailServerHost' : emailServerHost, 'emailServerPort' : emailServerPort, 'emailServerUsername' : emailServerUsername, 'emailServerPassword' : emailServerPassword, 'failOnError': failOnError, 'skipIfNoModifications': skipIfNoModifications})
        
    def addTask(self, name, task):    
        if not self.exists(name):
            raise Exception("Failed to add task because the project named '%s' does not exist" % name)   
        for project in self._projects:
            if project['name'] == name:
                project['tasks'].append(task) 
        
    def setProject(self, name, **kwargs):
        if not self.exists(name):
            raise Exception("Failed to set project because project named '%s' does not exist" % name)        
        for key in list(kwargs.keys()):
            if key not in ('emailFrom', 'emailTo', 'emailFormat', 'emailServerHost', 'emailServerPort', 'emailServerUsername', 'emailServerPassword', 'failOnError', 'skipIfNoModifications'):
                raise Exception("Unexpected key '%s'" % key)
        for project in self._projects:
            if project['name'] == name:
                for key, val in list(kwargs.items()):
                    project[key] = val
        
    def __next__(self):
        if self.cur >= len(self._projects):
            self.cur = 0
            raise StopIteration
        else:
            cur = self.cur
            self.cur = cur + 1
            key = self._projects[cur]['name']
            val =  deepcopy(self._projects[cur])
            val.pop('name')
            return key, val
        
    def __iter__(self):
        return self
        
    def __getitem__(self, name):    
        for project in self._projects:
            if project['name'] == name:
                retVal =  deepcopy(project)
                retVal.pop('name')
                return retVal
        raise Exception("Project named '%s' does not exist" % name)        
        
    def __len__(self):
        return len(self._projects)

class CcPyParseState:
    project, tasks, svntask, maketask, exectask, emailnot, other = list(range(7))

class CcPyConfigContentHandler(xml.sax.ContentHandler):
    """ SAX content handler for the CruiseControl.py configuration file """
    _rootElem = "ccpy"
    _projectElem = "project"
    _sccElem = "sourcecontrol"
    _sccAttrName = "type"
    _svnAttrVal = "svn"
    _tasksElem = "tasks"
    _makeElem = "make"
    _execElem = "exec"
    _svnTrunkUrlElem = "trunkUrl"
    _svnWorkingDirElem  = "workingDirectory"
    _svnPreCleanWorkingDirElem = "preCleanWorkingDirectory"    
    _makeWorkingDirElem  = "workingDirectory"
    _makeArgsElem = "args"
    _makeTimeoutElem = "timeout"
    _execExecutableElem = "executable"
    _execArgsElem = "args"
    _execWorkingDirElem  = "workingDirectory"
    _execTimeoutElem = "timeout"
    _execWarningExitCode = "warningExitCode"
    _emailNotElem = "emailNotification"
    _emailNotFromElem = "from"
    _emailNotToElem = "to"
    _emailFormatElem = "format"
    _emailServerHostElem = "server"
    _emailServerPortElem = "port"
    _emailServerUsernameElem = "username"
    _emailServerPasswordElem = "password"
    _failOnErrorElem = "failOnError"
    _skipIfNoModifElem = "skipIfNoModifications"

    def __init__(self):
        self._curElem = None
        self._curState = None
        self._curProjName = None
        self._curTaskType = None
        self._curEmailFrom = ""
        self._curEmailTo = ""
        self._curEmailFormat = ""
        self._curEmailServerHost = ""
        self._curEmailServerPort = ""
        self._curEmailServerUsername = None
        self._curEmailServerPassword = None
        self._curSkipIfNoModif = ""
        self._curFailOnError = ""
        self._curTaskArgs = {}
        self._projects = Projects()

    def startElement(self, anElem, anAttrs):
        if self._curElem is None:
            if anElem != CcPyConfigContentHandler._rootElem:
                raise RuntimeError("Invalid root element '%s'. Expected: '%s'" % anElem % CcPyConfigContentHandler._rootElem)
        self._curElem = anElem
        # we are in root 
        if self._curState == None:
            if anElem == CcPyConfigContentHandler._projectElem:
                self._curProjName = anAttrs.get('name')
                if self._curProjName is None:
                    raise RuntimeError("No name attribute found for project")
                if self._projects.exists(self._curProjName):
                    raise RuntimeError( "Project %s appears more than once" % self._curProjName)
                self._curState = CcPyParseState.project
                return
            return
        # we are in project
        if self._curState == CcPyParseState.project:
            if anElem == CcPyConfigContentHandler._tasksElem:
                self._curState = CcPyParseState.tasks
                return
            if anElem == CcPyConfigContentHandler._emailNotElem:
                self._curState = CcPyParseState.emailnot
                return
            return
        # we are in tasks
        if self._curState == CcPyParseState.tasks:
            if anElem == CcPyConfigContentHandler._sccElem:
                if anAttrs.get(CcPyConfigContentHandler._sccAttrName) == CcPyConfigContentHandler._svnAttrVal:
                    self._curTaskType = "svntask.SvnTask"
                    self._curState = CcPyParseState.svntask
                    return
                return
            if anElem == CcPyConfigContentHandler._makeElem:
                self._curState = CcPyParseState.maketask
                self._curTaskType = "maketask.MakeTask"
                return
            if anElem == CcPyConfigContentHandler._execElem:
                self._curState = CcPyParseState.exectask
                self._curTaskType = "exectask.ExecTask"
                return
            return
   
    def characters(self, aText):
        def accum(aKey):
            if aText is None: return
            if aKey in self._curTaskArgs: self._curTaskArgs[aKey] += aText.strip()
            else: self._curTaskArgs[aKey] = aText.strip()

        if self._curState == CcPyParseState.project:
            if self._curElem == CcPyConfigContentHandler._failOnErrorElem:
                if aText is not None:
                    self._curFailOnError += aText.strip()
                return 
            if self._curElem == CcPyConfigContentHandler._skipIfNoModifElem:
                if aText is not None:
                    self._curSkipIfNoModif += aText.strip()
                return 
            return
        if self._curState == CcPyParseState.emailnot:
            if self._curElem in CcPyConfigContentHandler._emailNotFromElem:
                if aText is not None:
                    self._curEmailFrom += aText.strip()
                return 
            if self._curElem == CcPyConfigContentHandler._emailNotToElem:
                if aText is not None:
                    self._curEmailTo += aText.strip()
                return 
            if self._curElem == CcPyConfigContentHandler._emailFormatElem:
                if aText is not None:
                    self._curEmailFormat += aText.strip()
                return 
            if self._curElem == CcPyConfigContentHandler._emailServerHostElem:
                if aText is not None:
                    self._curEmailServerHost += aText.strip()
                return 
            if self._curElem == CcPyConfigContentHandler._emailServerPortElem:
                if aText is not None:
                    self._curEmailServerPort += aText.strip()
                return 
            if self._curElem == CcPyConfigContentHandler._emailServerUsernameElem:
                if aText is not None:
                    if self._curEmailServerUsername is not None:  self._curEmailServerUsername += aText.strip()
                    else: self._curEmailServerUsername = aText.strip()
                return 
            if self._curElem == CcPyConfigContentHandler._emailServerPasswordElem:
                if aText is not None:
                    if self._curEmailServerPassword is not None:  self._curEmailServerPassword += aText.strip()
                    else: self._curEmailServerPassword = aText.strip()
                return                 
        if self._curState == CcPyParseState.svntask:
            if self._curElem == CcPyConfigContentHandler._svnTrunkUrlElem:
                accum('trunkUrl')
                return
            if self._curElem == CcPyConfigContentHandler._svnWorkingDirElem:
                accum('workingDir')
                return
            if self._curElem == CcPyConfigContentHandler._svnPreCleanWorkingDirElem:
                accum('preCleanWorkingDir')
                return
            return
        if self._curState == CcPyParseState.maketask:
            if self._curElem == CcPyConfigContentHandler._makeWorkingDirElem:
                accum('workingDir')
                return
            if self._curElem == CcPyConfigContentHandler._makeArgsElem:
                accum('args')
                return
            if self._curElem == CcPyConfigContentHandler._makeTimeoutElem:
                accum('timeout')
                return 
            return
        if self._curState == CcPyParseState.exectask:
            if self._curElem == CcPyConfigContentHandler._execExecutableElem:
                accum('executable')
                return
            if self._curElem == CcPyConfigContentHandler._execArgsElem:
                accum('args')
                return
            if self._curElem == CcPyConfigContentHandler._execWorkingDirElem:
                accum('workingDirectory')
                return
            if self._curElem == CcPyConfigContentHandler._execTimeoutElem:
                accum('timeout')
                return
            if self._curElem == CcPyConfigContentHandler._execWarningExitCode:
                accum('warningExitCode')
                return 
            return

    def endElement(self, anElem):
        if self._curState is None:
            if anElem == CcPyConfigContentHandler._rootElem:
                self._curElem = None
                return
            return
        if self._curState == CcPyParseState.project:
            if anElem == CcPyConfigContentHandler._projectElem:
                self._curElem = CcPyConfigContentHandler._rootElem
                self._curState = None
                self._curProjName = None
                return
            if anElem == CcPyConfigContentHandler._skipIfNoModifElem:
                self._add_skip_if_no_modif(self._curProjName, self._curSkipIfNoModif)
                self._curSkipIfNoModif = ""
                self._curElem = CcPyConfigContentHandler._projectElem
                self._curState = CcPyParseState.project
                return
            if anElem == CcPyConfigContentHandler._failOnErrorElem:
                self._add_fail_on_error(self._curProjName, self._curFailOnError)
                self._curFailOnError = ""
                self._curElem = CcPyConfigContentHandler._projectElem
                self._curState = CcPyParseState.project
                return
            return
        if self._curState == CcPyParseState.tasks:
            if anElem == CcPyConfigContentHandler._tasksElem:
                self._curElem = CcPyConfigContentHandler._projectElem
                self._curState = CcPyParseState.project
                return
            return
        if self._curState == CcPyParseState.emailnot:
            if anElem == CcPyConfigContentHandler._emailNotElem:
                self._add_email(self._curProjName, 
                              self._curEmailFrom, 
                              [] if len(self._curEmailTo) == 0 else self._curEmailTo.split(', '), 
                              self._curEmailFormat,
                              self._curEmailServerHost,
                              self._curEmailServerPort,
                              self._curEmailServerUsername,
                              self._curEmailServerPassword)
                self._curEmailFrom =""
                self._curEmailTo =""
                self._curEmailFormat = ""
                self._curEmailServerHost = ""
                self._curEmailServerPort = ""
                self._curEmailServerUsername = None
                self._curEmailServerPassword = None
                self._curElem = CcPyConfigContentHandler._projectElem
                self._curState = CcPyParseState.project
                return
            return
        if self._curState == CcPyParseState.svntask:
            if anElem == CcPyConfigContentHandler._sccElem:
                mySvnTaskArgs = CcPyConfigContentHandler._make_svn_task_ags(self._curTaskArgs)
                myTask = eval(self._curTaskType)(mySvnTaskArgs)
                self._add_task(self._curProjName, myTask)
                self._curElem = CcPyConfigContentHandler._tasksElem
                self._curState = CcPyParseState.tasks
                self._curTaskType = None
                self._curTaskArgs = {}
                return
            return
        if self._curState == CcPyParseState.maketask:
            if anElem == CcPyConfigContentHandler._makeElem:
                myMakeTaskArgs = CcPyConfigContentHandler._make_make_task_ags(self._curTaskArgs)
                myTask = eval(self._curTaskType)(myMakeTaskArgs)
                self._add_task(self._curProjName, myTask)
                self._curElem = CcPyConfigContentHandler._tasksElem
                self._curState = CcPyParseState.tasks
                self._curTaskType = None
                self._curTaskArgs = {}
                return
            return
        if self._curState == CcPyParseState.exectask:
            if anElem == CcPyConfigContentHandler._execElem:
                myExecTaskArgs = CcPyConfigContentHandler._make_exec_task_args(self._curTaskArgs)
                myTask = eval(self._curTaskType)(myExecTaskArgs)
                self._add_task(self._curProjName, myTask)
                self._curElem = CcPyConfigContentHandler._tasksElem
                self._curState = CcPyParseState.tasks
                self._curTaskType = None
                self._curTaskArgs = {}
                return
            return

    @staticmethod
    def _make_svn_task_ags(aRawArgs):
        myArgs = deepcopy(aRawArgs)
        if "preCleanWorkingDir" in myArgs:
            if myArgs['preCleanWorkingDir'] in ('on', 'yes', 'true'):
                myArgs['preCleanWorkingDir'] = True
            elif myArgs['preCleanWorkingDir'] in ('off', 'no', 'false'):
                myArgs['preCleanWorkingDir'] = False
            else:
                raise RuntimeError( "Invalid 'preCleanWorkingDir' value")
        else:   
            myArgs['preCleanWorkingDir'] = False            
        if "workingDir" not in myArgs:
            myArgs["workingDir"] = ''
        return myArgs

    @staticmethod
    def _make_make_task_ags(aRawArgs):
        myArgs = deepcopy(aRawArgs)
        if "workingDir" not in myArgs:
           myArgs["workingDir"] = ''
        if "args" not in myArgs:
           myArgs["args"] = ''
        if "timeout" in myArgs:
            myArgs["timeout"] = int(myArgs["timeout"])
        else:
            myArgs["timeout"] = 600
        return myArgs 

    @staticmethod
    def _make_exec_task_args(aRawArgs):
        myArgs = deepcopy(aRawArgs)
        if "args" not in myArgs:
           myArgs["args"] = ''
        if "workingDirectory" not in myArgs:
           myArgs["workingDirectory"] = ''
        myArgs["timeout"] = int(myArgs["timeout"]) if "timeout" in myArgs else 600
        if "warningExitCode" in myArgs:
            myArgs["warningExitCode"] = int(myArgs["warningExitCode"])
        return myArgs 

    @property
    def projects(self):
        return deepcopy(self._projects)

    def _add_task(self, aProjName, aTask):
        if not self._projects.exists(aProjName):
            self._projects.append(aProjName, tasks = [aTask])
        else:
            self._projects.addTask(aProjName, aTask)

    def _add_email(self, aProjName, aFrom, aTo, aFormat, aSvrHost, aSvrPort, aSvrUser, aSvrPass):
        myFormat = EmailFormat[aFormat] if aFormat else EmailFormat.html
        mySvrHost = aSvrHost if aSvrHost else 'localhost'
        mySvrPort = int(aSvrPort) if aSvrPort else 25
        if not self._projects.exists(aProjName):
            self._projects.append(aProjName, emailFrom = aFrom, emailTo = aTo, emailFormat = myFormat, emailServerHost = mySvrHost, emailServerPort = mySvrPort, emailServerUsername = aSvrUser, emailServerPassword = aSvrPass)
        else:
            self._projects.setProject(aProjName, emailFrom = aFrom, emailTo = aTo, emailFormat = myFormat, emailServerHost = mySvrHost, emailServerPort = mySvrPort, emailServerUsername  = aSvrUser, emailServerPassword = aSvrPass)
            
    def _add_skip_if_no_modif(self, aProjName, anSkipIfNoModif):
        if anSkipIfNoModif in ['on', 'yes', 'true']:
            mySkipIfNoModif = True
        elif anSkipIfNoModif in ['off', 'no', 'false', '']:
            mySkipIfNoModif = False
        else:
            raise RuntimeError( "Invalid %s element value" % CcPyConfigContentHandler._skipIfNoModifElem)
        if not self._projects.exists(aProjName):
            self._projects.append(aProjName, skipIfNoModifications = mySkipIfNoModif)
        else:
            self._projects.setProject(aProjName, skipIfNoModifications = mySkipIfNoModif)            
    
    def _add_fail_on_error(self, aProjName, aFailOnError):
        if aFailOnError in ['on', 'yes', 'true', '']:
            myFailOnError = True
        elif aFailOnError in ['off', 'no', 'false']:
            myFailOnError = False
        else:
            raise RuntimeError( "Invalid %s element value" % CcPyConfigContentHandler._failOnErrorElem)
        if not self._projects.exists(aProjName):
            self._projects.append(aProjName, failOnError = myFailOnError)
        else:
            self._projects.setProject(aProjName, failOnError = myFailOnError)              
   
class ParseError(Exception):
    pass

def parse(aCcPyConfigFileName = DefCcPyConfigFileName):
    """Parse ccpy project configuration file

    Return  the instance if Projects class
    Projects and tasks within each project are returned in the order they appear in the config file. 
    Supported tasks are: SvnTask, MakeTask and ExecTask
    Throw ParseError
    """
    try:
        Logger.debug("Reading ccpy configuration from %s..." % aCcPyConfigFileName )
        myParser = xml.sax.make_parser()
        myCcPyConfigContentHandler = CcPyConfigContentHandler()
        myParser.setContentHandler(myCcPyConfigContentHandler)
        myParser.parse(aCcPyConfigFileName )
        return myCcPyConfigContentHandler.projects
    except Exception as e:
        raise ParseError( "Failed to parse %s. %s: %s. %s" % (aCcPyConfigFileName , type(e), str(e), formatTb()) )


   
