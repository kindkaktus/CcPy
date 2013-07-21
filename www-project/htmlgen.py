#
#  HeadURL : $HeadURL: svn://korostelev.net/CcPy/Trunk/www-project/htmlgen.py $
#  Id      : $Id: htmlgen.py 87 2009-02-04 20:46:23Z akorostelev $
#
#  Copyright (c) 2008-2009, Andrei Korostelev <andrei at korostelev dot net>
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
    myContent = ''
    for line in file(aFileName , "r"):
        myContent += line
    return myContent
    
def _writeFile(aFileName, aContent):
    myFile = open( aFileName , "w+")
    myFile.write(aContent)
    myFile.close()

#######
# BL
######
SrcSuffix=".src"
MainTemplFile ="maintempl.htm" + SrcSuffix
GenHtmlPages=('index.htm', 'quickstart.htm', 'ccpyd.htm', 'ccpy.htm', 'changelog.htm', 'download.htm')
    
for genHtmlPage in GenHtmlPages:
    print "Generating %s" %  genHtmlPage
    myTempl = Template(_readFile(MainTemplFile))
    mySrcContentFile = genHtmlPage+SrcSuffix
    myContent = _readFile(mySrcContentFile)
    myGenContent = myTempl.substitute(content=myContent)
    _writeFile(genHtmlPage, myGenContent)