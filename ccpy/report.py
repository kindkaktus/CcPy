#
#  Andrei Korostelev <andrei at korostelev dot net>
#
#  Before using this product in any way please read the license agreement.
#  If you do not agree to the terms in this agreement you are not allowed
#  to use this product or parts of it. You can read this license in the
#  file named LICENSE.
#

"""
CcPy reports
"""

import cgi
from string import Template

from . import common
from .util import EmailFormat, formatTimeDelta, getTotalSeconds

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

# #########################
# Public API
# #########################


def makeEmailBody(aFormat, aSummary, aStatusPerTask, aBuildFailedBecauseOfTaskError):
    """
    Produces the email body in the requested format

    aFormat is one of util.EmailFormat.
    aSummary is a dictionary with a build summary as:
      {'prjName', 'prjStatus', 'numSucceededTasks', 'numSucceededTasksWithWarning', 'numFailedTasks', 'startTime', 'endTime'}
    aStatusPerTask is a list of dicts holding build statuses per task
      Each task status is a dictionary with the following keys:
      'name', 'status', 'description', 'startTime', 'endTime' and optionally 'allocatedTime' as int, 'stdout', 'stderr'
    aBuildFailedBecauseOfTaskError - flag indicating whether the build failed because of the failed task
    """
    if aFormat == EmailFormat.attachment:
        return _makeHtmlSummaryEmailBody(aSummary)
    elif aFormat == EmailFormat.plain:
        return _makePlainEmailBody(aSummary, aStatusPerTask, aBuildFailedBecauseOfTaskError)
    elif aFormat == EmailFormat.html:
        return _makeHtmlEmailBody(aSummary, aStatusPerTask, aBuildFailedBecauseOfTaskError)
    raise Exception("Unsupported format %s" % aFormat)


def makeAttachmentText(aFormat, aStatusPerTask, aBuildFailedBecauseOfTaskError):
    if aFormat != EmailFormat.attachment:
        return None

    myBody = ''
    for task in aStatusPerTask:
        myBody += '%(name)s => %(status)s. %(description)s' % task
        if 'startTime' in task and 'endTime' in task:
            elapsed_time = task['endTime'] - task['startTime']
            myBody += '\nElapsed time: %s (start: %s, end %s)' % (formatTimeDelta(elapsed_time), task['startTime'], task['endTime'])
            if 'allocatedTime' in task and task['allocatedTime'] > 0:
                myUsedTimePercentage = getTotalSeconds(elapsed_time) * 100 / task['allocatedTime']
                myBody += ' (%0.2f%% of allocated time)' % myUsedTimePercentage
        if 'stdout' in task and len(task['stdout']):
            myBody += '\nStdout:\n%(stdout)s' % task
        if 'stderr' in task and len(task['stderr']):
            myBody += '\nStderr:\n%(stderr)s' % task
        myBody += "\n--------\n\n"

    if aBuildFailedBecauseOfTaskError:
        myBody += "\n**** FAILING the project because of the failed task\n"

    return myBody


# ######################
# Private API
# #######################

def _makeHtmlSummaryEmailBody(aSummary):
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
                          $numSucceeded task$succSuffix SUCCEEDED of which $numSucceededWithWarning have WARNINGs, $numFailed task$failedSuffix FAILED<BR>
                          Elapsed time: $elapsedTime (started $startTime, ended $endTime)
                      </DIV>
                  </BODY>
                </HTML>
            """)

    myBody = myBodyTempl.safe_substitute(
        css=_Css,
        product=common.ProductName,
        ver=common.ProductVersion,
        prjName=aSummary['prjName'],
        prjStatus=aSummary['prjStatus'],
        numSucceeded=int(aSummary['numSucceededTasks']),
        succSuffix='' if int(aSummary['numSucceededTasks']) == 1 else 's',
        numSucceededWithWarning=int(aSummary['numSucceededTasksWithWarning']),
        numFailed=int(aSummary['numFailedTasks']),
        failedSuffix='' if int(aSummary['numFailedTasks']) == 1 else 's',
        elapsedTime=formatTimeDelta(aSummary['endTime'] - aSummary['startTime']),
        startTime=aSummary['startTime'],
        endTime=aSummary['endTime'])

    return myBody


def _makePlainEmailBody(aSummary, aStatusPerTask, aBuildFailedBecauseOfTaskError):
    mySummaryTempl = Template("\
$product-$ver Integration Results for project $prjName\r\n\
$sep1\r\n\
\r\n\
Status: $prjStatus\r\n\
$numSucceeded task$succSuffix SUCCEEDED of which $numSucceededWithWarning have WARNINGs, $numFailed task$failedSuffix FAILED\r\n\
Elapsed time: $elapsedTime (started $startTime, ended $endTime)\r\n\
$sep2\r\n\
\r\n")
    myBody = mySummaryTempl.safe_substitute(
        product=common.ProductName,
        ver=common.ProductVersion,
        prjName=aSummary['prjName'],
        sep1="===================================================================================",
        prjStatus=aSummary['prjStatus'],
        numSucceeded=int(aSummary['numSucceededTasks']),
        succSuffix='' if int(aSummary['numSucceededTasks']) == 1 else 's',
        numSucceededWithWarning=int(aSummary['numSucceededTasksWithWarning']),
        numFailed=int(aSummary['numFailedTasks']),
        failedSuffix='' if int(aSummary['numFailedTasks']) == 1 else 's',
        elapsedTime=formatTimeDelta(aSummary['endTime'] - aSummary['startTime']),
        startTime=aSummary['startTime'],
        endTime=aSummary['endTime'],
        sep2="------------------------------------------------------------------------------------")
    for task in aStatusPerTask:
        myBody += '%(name)s => %(status)s. %(description)s' % task
        if 'startTime' in task and 'endTime' in task:
            elapsed_time = task['endTime'] - task['startTime']
            myBody += '\nElapsed time: %s (start: %s, end %s)' % (formatTimeDelta(elapsed_time), task['startTime'], task['endTime'])
            if 'allocatedTime' in task and task['allocatedTime'] > 0:
                myUsedTimePercentage = getTotalSeconds(elapsed_time) * 100 / task['allocatedTime']
                myBody += ' (%0.2f%% of allocated time)' % myUsedTimePercentage
        if 'stdout' in task and len(task['stdout']):
            myBody += '\nStdout:\n%(stdout)s' % task
        if 'stderr' in task and len(task['stderr']):
            myBody += '\nStderr:\n%(stderr)s' % task
        myBody += "\n--------\n\n"

    if aBuildFailedBecauseOfTaskError:
        myBody += "\r\n**** FAILING the project because of the failed task\r\n"
    return myBody


def _makeHtmlEmailBody(aSummary, aStatusPerTask, aBuildFailedBecauseOfTaskError):
    myTaskTempl = Template("""
                 <TR>
                   <TD>$taskName</TD><TD>$taskStatus</TD><TD>$taskDescription</TD><TD>$elapsedTime (started $startTime, ended $endTime) $usedTimePercentage</TD><TD>$stdout</TD><TD>$stderr</TD>
                 </TR>
                 """)
    # TODO: make stderr and stdout columns bigger. WIDTH=25% does not help in
    # email, but it is ok on saved html
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
                          $numSucceeded task$succSuffix SUCCEEDED of which $numSucceededWithWarning have WARNINGs, $numFailed task$failedSuffix FAILED<BR>
                          Elapsed time: $elapsedTime (started $startTime, ended $endTime)
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
    for task in aStatusPerTask:
        elapsed_time = task['endTime'] - task['startTime'] if 'startTime' in task and 'endTime' in task else None
        if 'allocatedTime' in task and task['allocatedTime'] > 0 and 'startTime' in task and 'endTime' in task:
            myUsedTimePercentage = getTotalSeconds(elapsed_time) * 100 / task['allocatedTime']
        else:
            myUsedTimePercentage = None

        myTasks += myTaskTempl.safe_substitute(
            taskName=task['name'],
            taskStatus=task['status'],
            taskDescription=task['description'],
            elapsedTime=formatTimeDelta(elapsed_time) if elapsed_time is not None else '',
            startTime=task['startTime'] if 'startTime' in task else '',
            endTime=task['endTime'] if 'endTime' in task else '',
            usedTimePercentage=' (%s%% of allocated time)' %
            myUsedTimePercentage if myUsedTimePercentage is not None else '',
            stdout="<pre>" +
            cgi.escape(
                task.get(
                    'stdout',
                    ' ')) +
            "</pre>",
            stderr="<pre>" +
            cgi.escape(
                task.get(
                    'stderr',
                    ' ')) +
            "</pre>")

    myError = "FAILING the project because of the failed task" if aBuildFailedBecauseOfTaskError else ''

    myBody = myBodyTempl.safe_substitute(
        css=_Css,
        product=common.ProductName,
        ver=common.ProductVersion,
        prjName=aSummary['prjName'],
        prjStatus=aSummary['prjStatus'],
        numSucceeded=int(aSummary['numSucceededTasks']),
        succSuffix='' if int(aSummary['numSucceededTasks']) == 1 else 's',
        numSucceededWithWarning=int(aSummary['numSucceededTasksWithWarning']),
        numFailed=int(aSummary['numFailedTasks']),
        failedSuffix='' if int(aSummary['numFailedTasks']) == 1 else 's',
        elapsedTime=formatTimeDelta(aSummary['endTime'] - aSummary['startTime']),
        startTime=aSummary['startTime'],
        endTime=aSummary['endTime'],
        tasks=myTasks,
        error=myError)

    return myBody
