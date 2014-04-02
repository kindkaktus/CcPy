#
#  HeadURL : $HeadURL: svn://korostelev.net/CcPy/Trunk/ccpy/ccpydconfparser.py $
#  Id      : $Id: ccpydconfparser.py 179 2010-11-10 09:24:28Z akorostelev $
#
#  Copyright (c) 2008-2009, Andrei Korostelev <andrei at korostelev dot net>
#
#  Before using this product in any way please read the license agreement.
#  If you do not agree to the terms in this agreement you are not allowed
#  to use this product or parts of it. You can read this license in the
#  file named LICENSE.
#

"""
CcPy daemon configiration file parser
"""

import xml.sax
import logging

from .common import LoggerName

DefCcPydConfigFileName = "/etc/ccpyd.conf"
Logger = logging.getLogger(LoggerName)

class CcPydParseState:
    root, log, other = list(range(3))

class CcPydConfigContentHandler(xml.sax.ContentHandler):
    """ SAX content handler for the CruiseControl.py daemon configuration file """
    _rootElem = "ccpyd"
    _ccpyConfigElem = "ccpyConfig"
    _scheduleElem = "schedule"
    _scheduleTimeAttrName = "time"
    _logElem = "logging"
    _logEnabledAttrName = "enabled"
    _logFileElem = "file"
    _logLevelElem = "level"

    def __init__(self):
        self._curElem = None
        self._curState = None
        self._dataDict = {}

    def startElement(self, anElem, anAttrs):
        if self._curElem is None:
            if anElem != CcPydConfigContentHandler._rootElem:
                raise RuntimeError("Invalid root element '%s'. Expected: '%s'" % anElem % CcPydConfigContentHandler._rootElem)
        self._curElem = anElem
        if self._curState == CcPydParseState.root:
            if anElem == CcPydConfigContentHandler._logElem:
                if anAttrs.get(CcPydConfigContentHandler._logEnabledAttrName) in ['on', 'yes', 'true']:
                    self._curState = CcPydParseState.log
                    self._dataDict["logging"] = True
                    return
                if anAttrs.get(CcPydConfigContentHandler._logEnabledAttrName) in ['off', 'no', 'false']:
                    self._dataDict["logging"] = False
                    return
                return
            if anElem == CcPydConfigContentHandler._scheduleElem:
                self._dataDict["schedule"] = True
                myTimeStr = anAttrs.get(CcPydConfigContentHandler._scheduleTimeAttrName)
                (myHour, myMin) =  myTimeStr.split(':')
                from datetime import time
                self._dataDict['scheduleTime'] = time(int(myHour), int(myMin))
                return
            return
        if self._curState is None:
            self._curState = CcPydParseState.root
            return
   
    def characters(self, aText):
        def accum(aKey):
            if aText is None: return
            if aKey in self._dataDict: self._dataDict[aKey] += aText.strip()
            else: self._dataDict[aKey] = aText.strip()

        if self._curState == CcPydParseState.root:
            if self._curElem == CcPydConfigContentHandler._ccpyConfigElem:
                accum('ccpyConfig')
                return 
            return
        if self._curState == CcPydParseState.log:
            if self._curElem == CcPydConfigContentHandler._logFileElem:
                accum('logFile')
                return
            if self._curElem == CcPydConfigContentHandler._logLevelElem:
                accum('logLevel')
                return
            return


    def endElement(self, anElem):
        if self._curState is CcPydParseState.log:
            if anElem == CcPydConfigContentHandler._logElem:
                self._curElem = CcPydConfigContentHandler._rootElem
                self._curState = CcPydParseState.root
                return
            return
        if self._curState is CcPydParseState.root:
            if anElem == CcPydConfigContentHandler._rootElem:
                self._applyDefaults()
                self._curElem = None
                self._curState = None
                return
            if anElem in [ CcPydConfigContentHandler._ccpyConfigElem,
                           CcPydConfigContentHandler._scheduleElem,
                           CcPydConfigContentHandler._logFileElem, 
                           CcPydConfigContentHandler._logLevelElem ]:
                self._curElem = CcPydConfigContentHandler._rootElem
                return
            return

    def _applyDefaults(self):
        """ Apply default settings for missing config settings which support defaults """
        if "ccpyConfig" not in self._dataDict:
            self._dataDict["ccpyConfig"] = "/etc/ccpy.conf"
        if "schedule" not in self._dataDict:
            self._dataDict["schedule"] = False
        if "logging" not in self._dataDict:
            self._dataDict["logging"] = False
        if self._dataDict["logging"] and "logFile" not in self._dataDict:
            self._dataDict["logFile"] = "/var/log/ccpyd.log"

    @property
    def dataDict(self):
        from copy import deepcopy
        return deepcopy(self._dataDict)

class ParseError(Exception):
    pass

def parse(aCcPydConfigFileName = DefCcPydConfigFileName):
    """Parse CcPy daemon configuration file

    Return a dictionary of config settings. See README for more info
    Throw ParseError
    """
    try:
        Logger.debug("Reading ccpyd configuration from %s..." % aCcPydConfigFileName)
        myParser = xml.sax.make_parser()
        myCcPydConfigContentHandler = CcPydConfigContentHandler()
        myParser.setContentHandler(myCcPydConfigContentHandler)
        myParser.parse(aCcPydConfigFileName )
        return myCcPydConfigContentHandler.dataDict
    except BaseException as e:
        raise ParseError( "Failed to parse %s. %s" % (aCcPydConfigFileName , str(e)) )


   
