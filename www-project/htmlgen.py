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
Html generator for CcPy project Web page
"""
from string import Template


def _readFile(aFileName):
    with open(aFileName, "r") as f:
        return f.read()


def _writeFile(aFileName, aContent):
    with open(aFileName, "w+") as f:
        f.write(aContent)

#######
# BL
######
SrcSuffix = ".src"
MainTemplFile = "maintempl.htm" + SrcSuffix
HtmlPages = (
    'index.htm',
    'quickstart.htm',
    'ccpyd.htm',
    'ccpy.htm',
    'changelog.htm',
    'download.htm')

for page in HtmlPages:
    print(("Generating %s" % page))
    myTempl = Template(_readFile(MainTemplFile))
    mySrcContentFile = page + SrcSuffix
    myContent = _readFile(mySrcContentFile)
    myGenContent = myTempl.substitute(content=myContent)
    _writeFile(page, myGenContent)
