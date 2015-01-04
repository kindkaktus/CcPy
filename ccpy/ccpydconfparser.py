#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
#  Copyright (c) 2008-2015, Andrei Korostelev <andrei at korostelev dot net>
#
#  Before using this product in any way please read the license agreement.
#  If you do not agree to the terms in this agreement you are not allowed
#  to use this product or parts of it. You can read this license in the
#  file named LICENSE.
#


"""
CcPy daemon configuration file parser
"""

import xml.etree.ElementTree as ET
import logging

from .common import LoggerName

DefCcPydConfigFileName = "/etc/ccpyd.conf"
Logger = logging.getLogger(LoggerName)


class ParseError(Exception):
    pass


def _get_elem_value(element, default_value):
    if element is not None:
        return element.text
    else:
        return default_value


def parse(aCcPydConfigFileName=DefCcPydConfigFileName):
    """Parse CcPy daemon configuration file

    Return a dictionary of config settings. See README for more info
    Throw ParseError
    """
    try:
        Logger.debug("Reading ccpyd configuration from %s..." % aCcPydConfigFileName)

        tree = ET.parse(aCcPydConfigFileName)
        root = tree.getroot()
        if (root.tag != 'ccpyd'):
            raise Exception('Invalid root tag name: ' + root.tag)

        ccpyConfig = _get_elem_value(root.find('./ccpyConfig'), "/etc/ccpy.conf")
        loggingElem = root.find('./logging')
        if loggingElem is not None and loggingElem.attrib['enabled'].lower() in (
                'on',
                'yes',
                'true'):
            logFile = _get_elem_value(loggingElem.find('./file'), "/var/log/ccpyd.log")
            logLevel = _get_elem_value(loggingElem.find('./level'), "DEBUG")
            return {'ccpyConfig': ccpyConfig,
                    'logging': True,
                    'logFile': logFile,
                    'logLevel': logLevel}
        else:
            return {'ccpyConfig': ccpyConfig,
                    'logging': False}

    except BaseException as e:
        raise ParseError("Failed to parse %s. %s" % (aCcPydConfigFileName, str(e)))
