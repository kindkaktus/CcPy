#  HeadURL : $HeadURL: svn://korostelev.net/CcPy/Trunk/ccpy/report.py $
#  Id      : $Id: report.py 212 2012-06-19 19:00:08Z akorostelev $
#
#  Copyright (c) 2008-2009, Andrei Korostelev <andrei at korostelev dot net>
#
#  Before using this product in any way please read the license agreement.
#  If you do not agree to the terms in this agreement you are not allowed
#  to use this product or parts of it. You can read this license in the
#  file named LICENSE.
#
"""
CcPy reports
"""

import sys
import time
import datetime
import logging
import cgi
from string import Template

import common
from util import EmailFormat, formatTimeDelta, getTotalSeconds

_Css = """
table {
  padding:0px;
  width: 100%;
  margin-left: -2px;
  margin-right: -2px;
}

table.bodyTable th, table.bodyTable td {
  padding: 2px 4px 2px 4px;
  vertical-align: top;
}
.section {
  padding: 4px;
}
body {
    background-color: #fff;
	font-family: Verdana, Helvetica, Arial, sans-serif;
	margin-left: auto;
	margin-right: auto;
	background-repeat: repeat-y;
	font-size: 11px;
	padding: 0px;
}
a {
  text-decoration: none;
}
a:link {
  color:#7a;
}
a:visited  {
  color:#666666;
}
a:active, a:hover {
  color:#990000;
}

h2 {
    font-size: 13px;
    margin-top: 0px;
    margin-bottom: 6px;
}
h3 {
    font-size: 11px;
    margin-top: 0px;
    margin-bottom: 3px;
}

p {
  line-height: 1.3em;
  font-size: 12px;
  color: #000;
}
.wikitable {
    margin: 5px;
    border-collapse: collapse;
	
}
.wikitable td, .wikitable th {
    border: 1px solid #ccc;
    padding: 3px 4px 3px 4px;
	font-size: 11px;
}
.wikitable th {
    background: #f0f0f0;
    text-align: center;
}
"""

def makeEmailBody(aFormat, aSummary, aStatusPerTask, aBuildFailedBecauseOfTaskError):
    """
    Produces the email body in the requested format

    aFormat is one of util.EmailFormat. Currrently inly html and plain are supported
    aSummary is a dictionary with a build summary. 
      Contains keys: 'prjName', 'prjStatus', 'numSucceededTasks', 'numSucceededTasksWithWarning', 'numFailedTasks', 'numSkippedTasks', 'elapsedTime' as datetime.timedelta
    aStatusPerTask is a sequence of build statuses per task 
      Each task status is a dictionary with the following keys: 
      'name', 'status', 'description', 'elapsedTime' as datetime.timedelta and optionally 'allocatedTime' as int, 'stdout', 'stderr'
    aBuildFailedBecauseOfTaskError - flag indicating whether the build was failed because of the failed task
    """
    if aFormat == EmailFormat.plain:
        return _makePlainEmailBody(aSummary, aStatusPerTask, aBuildFailedBecauseOfTaskError)
    if aFormat == EmailFormat.html:
        return _makeHtmlEmailBody(aSummary, aStatusPerTask, aBuildFailedBecauseOfTaskError)
    raise Exception("Unsupported format %s" % aFormat)

def _makePlainEmailBody(aSummary, aStatusPerTask, aBuildFailedBecauseOfTaskError):
    mySummaryTempl = Template("\
$product-$ver Integration Results for project $prjName\r\n\
$sep1\r\n\
\r\n\
Status: $prjStatus\r\n\
$numSucceeded task$succSuffix SUCCEEDED of which $numSucceededWithWarning have WARNINGs, $numFailed task$failedSuffix FAILED, $numSkipped task$skippedSuffix SKIPPED\r\n\
Elapsed time: $elapsedTime\r\n\
$sep2\r\n\
\r\n") 
    myBody = mySummaryTempl.safe_substitute(
               product = common.ProductName, 
               ver = common.ProductVersion,
               prjName = aSummary['prjName'],
               sep1 = "===================================================================================",
               prjStatus = aSummary['prjStatus'], 
               numSucceeded = int(aSummary['numSucceededTasks']),
               succSuffix = '' if int(aSummary['numSucceededTasks'])==1 else 's', 
               numSucceededWithWarning = int(aSummary['numSucceededTasksWithWarning']),
               numFailed = int(aSummary['numFailedTasks']),
               failedSuffix = '' if int(aSummary['numFailedTasks'])==1 else 's', 
               numSkipped = int(aSummary['numSkippedTasks']),
               skippedSuffix = '' if int(aSummary['numSkippedTasks'])==1 else 's', 
               elapsedTime = formatTimeDelta(aSummary['elapsedTime']),
               sep2 = "------------------------------------------------------------------------------------")
    for myTaskStatus in aStatusPerTask:
      myBody += '    %(name)s => %(status)s. %(description)s' %  myTaskStatus
      if myTaskStatus.has_key('elapsedTime'): 
          myBody += ' Elapsed time: %s' %  formatTimeDelta(myTaskStatus['elapsedTime'])
          if myTaskStatus.has_key('allocatedTime') and myTaskStatus['allocatedTime']>0:
              myUsedTimePercentage = getTotalSeconds(myTaskStatus['elapsedTime'])*100/myTaskStatus['allocatedTime']
              myBody += ' (%s%% of allocated time)' % myUsedTimePercentage
      if myTaskStatus.has_key('stdout') and len(myTaskStatus['stdout']): 
          myBody += ' Stdout: %(stdout)s' % myTaskStatus
      if myTaskStatus.has_key('stderr') and len(myTaskStatus['stderr']): 
          myBody += ' Stderr: %(stderr)s' % myTaskStatus
      myBody += "\r\n"

    if aBuildFailedBecauseOfTaskError:
       myBody += "\r\n**** FAILING the project because of the failed task\r\n"
    return myBody

def _makeHtmlEmailBody(aSummary, aStatusPerTask, aBuildFailedBecauseOfTaskError):
    myTaskTempl = Template("""
                 <TR>
                   <TD>$taskName</TD><TD>$taskStatus</TD><TD>$taskDescription</TD><TD>$elapsedTime $usedTimePercentage</TD><TD>$stdout</TD><TD>$stderr</TD>
                 </TR>
                 """)
    #TODO: make stderr and stdout columns bigger. WIDTH=25% does not help in email, but it is ok on saved html
    myBodyTempl = Template(""" 
                <HTML>
                  <HEAD>
                    <STYLE  type="TEXT/CSS"> 
                    <!-- 
                    $css
                    -->
                    </STYLE> 
                  </HEAD>
                  <BODY>
                  <DIV class='section'>
                  <H2>$product-$ver Integration Results for project $prjName</H2>
                  <H2>Status: $prjStatus</H2>
                  $numSucceeded task$succSuffix SUCCEEDED of which $numSucceededWithWarning have WARNINGs, $numFailed task$failedSuffix FAILED, $numSkipped task$skippedSuffix SKIPPED<BR>
                  Elapsed time: $elapsedTime
                  <TABLE CLASS='wikitable'>
                    <TR>
                      <TH>Task</TH><TH>Status</TH><TH WIDTH=25%>Description</TH><TH>Elapsed Time</TH><TH WIDTH=25%>Stdout</TH><TH WIDTH=25%>Stderr</TH>
                    </TR>
                    $tasks
                    <TR>
                    </TR>
                  </TABLE>
                  <B>$error</B>
                  </DIV>
                  </BODY>
                </HTML>
            """)

    myTasks = ""
    for myTaskStatus in aStatusPerTask:
        if myTaskStatus.has_key('allocatedTime') and myTaskStatus['allocatedTime']>0 and myTaskStatus.has_key('elapsedTime'):
            myUsedTimePercentage = getTotalSeconds(myTaskStatus['elapsedTime'])*100/myTaskStatus['allocatedTime']
        else:
            myUsedTimePercentage = None
        myTasks += myTaskTempl.safe_substitute(
                taskName = myTaskStatus['name'], 
                taskStatus = myTaskStatus['status'], 
                taskDescription = myTaskStatus['description'],
                elapsedTime = formatTimeDelta(myTaskStatus['elapsedTime']) if myTaskStatus.has_key('elapsedTime') else '', 
                usedTimePercentage = ' (%s%% of allocated time)' % myUsedTimePercentage if myUsedTimePercentage is not None else '',
                stdout = "<pre>"+cgi.escape(myTaskStatus.get('stdout',' '))+"</pre>", 
                stderr = "<pre>"+cgi.escape(myTaskStatus.get('stderr',' '))+"</pre>")

    myError = "FAILING the project because of the failed task" if aBuildFailedBecauseOfTaskError else ''

    myBody = myBodyTempl.safe_substitute(
               css = _Css,
               product = common.ProductName, 
               ver = common.ProductVersion,
               prjName = aSummary['prjName'],
               prjStatus = aSummary['prjStatus'], 
               numSucceeded = int(aSummary['numSucceededTasks']),
               succSuffix = '' if int(aSummary['numSucceededTasks'])==1 else 's', 
               numSucceededWithWarning = int(aSummary['numSucceededTasksWithWarning']),
               numFailed = int(aSummary['numFailedTasks']),
               failedSuffix = '' if int(aSummary['numFailedTasks'])==1 else 's', 
               numSkipped = int(aSummary['numSkippedTasks']),
               skippedSuffix = '' if int(aSummary['numSkippedTasks'])==1 else 's', 
               elapsedTime = formatTimeDelta(aSummary['elapsedTime']),
               tasks = myTasks,
               error = myError)

    return myBody

