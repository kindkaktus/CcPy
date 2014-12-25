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
Ccpy state
"""

import os
import logging
import sys
import xml.dom.minidom

from .enum import Enum
from .common import LoggerName

DefCcPyStateConfigFileName = '/etc/ccpy.state'
PrjStates = Enum('OK', 'FAILED', 'UNKNOWN')
Logger = logging.getLogger(LoggerName)


def str2PrjState(anStr):
    for s in PrjStates:
        if str(s) == anStr:
            return s
    raise Exception("State '%s' does not exist in enum" % anStr)


class CcPyState:
    _rootElem = 'ccpystate'
    _prjElem = 'project'
    _prjNameAttrName = 'name'
    _prjStateAttrName = 'state'

    def __init__(self, aFileName=DefCcPyStateConfigFileName):
        self._fileName = aFileName

    def getPrjState(self, aName):
        if not os.path.exists(self._fileName):
            Logger.debug(
                "File '%s' does not exist, defaulting project state to %s" %
                (self._fileName, PrjStates.UNKNOWN))
            return PrjStates.UNKNOWN
        if not os.path.isfile(self._fileName):
            raise IOError("'%s' exists but is not a regular file" % self._fileName)
        myDom = xml.dom.minidom.parse(self._fileName)
        if myDom.documentElement.tagName != CcPyState._rootElem:
            raise RuntimeError(
                "'%s' is ill-formed ccpystate config (incorrect root element)" %
                self._fileName)
        myProjects = myDom.getElementsByTagName(CcPyState._prjElem)
        myRequestedProjects = [
            prj for prj in myProjects if prj.getAttribute(
                CcPyState._prjNameAttrName) == aName]
        if (len(myRequestedProjects) > 1):
            raise RuntimeError(
                "'%s' is ill-formed ccpystate config (more than one '%s' projects found)" %
                aName)
        if (len(myRequestedProjects) == 0):
            Logger.debug(
                "'%s' does not contain project '%s', defaulting project state to %s" %
                (self._fileName, aName, PrjStates.UNKNOWN))
            return PrjStates.UNKNOWN
        myStateStr = myRequestedProjects[0].getAttribute(CcPyState._prjStateAttrName)
        myState = str2PrjState(myStateStr)
        return myState

    def setPrjState(self, aName, aVal):
        if aVal not in PrjStates:
            raise TypeError("'%s' in not valid project state" % aVal)

        if os.path.exists(self._fileName):
            if not os.path.isfile(self._fileName):
                raise IOError("'%s' exists but is not a regular file" % self._fileName)
            myDom = xml.dom.minidom.parse(self._fileName)
            if myDom.documentElement.tagName != CcPyState._rootElem:
                raise RuntimeError(
                    "'%s' is ill-formed ccpystate config (incorrect root element)" %
                    self._fileName)
            myProjects = myDom.getElementsByTagName(CcPyState._prjElem)
            myProjects2Change = [
                prj for prj in myProjects if prj.getAttribute(
                    CcPyState._prjNameAttrName) == aName]
            if (len(myProjects2Change) > 1):
                raise RuntimeError(
                    "'%s' is ill-formed ccpystate config (more than one '%s' projects found)" %
                    aName)
            if (len(myProjects2Change) == 0):
                Logger.debug(
                    "'%s' does not contain project '%s', adding project with state %s" %
                    (self._fileName, aName, aVal))
                myElem = myDom.createElement(CcPyState._prjElem)
                myElem.setAttribute(CcPyState._prjNameAttrName, aName)
                myElem.setAttribute(CcPyState._prjStateAttrName, str(aVal))
                myDom.documentElement.appendChild(myElem)
            else:
                Logger.debug(
                    "'%s' contains project '%s', setting project state to %s" %
                    (self._fileName, aName, aVal))
                myElem = myProjects2Change[0]
                myElem.setAttribute(CcPyState._prjStateAttrName, str(aVal))
        else:
            myDom = xml.dom.minidom.parseString('<%s>\n<%s %s="%s" %s="%s"/>\n</%s>\n' %
                                                (CcPyState._rootElem,
                                                 CcPyState._prjElem,
                                                 CcPyState._prjNameAttrName, aName,
                                                 CcPyState._prjStateAttrName, aVal,
                                                 CcPyState._rootElem))
        myFp = open(self._fileName, 'w+')
        myDom.writexml(myFp)
        myFp.close()

    prjState = property(getPrjState, setPrjState)
