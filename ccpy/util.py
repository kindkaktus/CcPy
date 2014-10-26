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
Various helper utilities
"""

import os
import time
import sys
import signal
from .enum import Enum

IS_PYTHON2 = sys.version_info < (3,0)

import logging
import traceback
import threading

def formatTb():
    tb = traceback.format_tb(sys.exc_info()[2])
    fmt='\nTraceback:\n'
    for tb_frame in tb:
        fmt = fmt + tb_frame.replace('\n','').replace('  ', ' ') + '\n'
    return fmt  

def _parseLogLevel(aLevelNameStr):
    for lev in [logging.CRITICAL, logging.ERROR, logging.WARNING, logging.INFO, logging.DEBUG ]:
        if logging.getLevelName(lev) == aLevelNameStr:
            return lev
    raise Exception("%s is not a valid logging level" % aLevelNameStr)

def initLogger(aLoggerName, aLogFileName, anAppName, aLogLevelStr):
    """ Initialize logger """
    myLogger = logging.getLogger(aLoggerName)
    if sys.platform == 'win32':
        myHandler = logging.FileHandler(aLogFileName)
    else:
        try:
            from logging import WatchedFileHandler
        except ImportError:
            from .logger_compatibility import WatchedFileHandler
        myHandler = WatchedFileHandler(aLogFileName)   
    myHandler.setFormatter(logging.Formatter('%(asctime)s <'+str(os.getpid())+'> [%(levelname)s] %(module)s.%(funcName)s: %(message)s'))
    myLogger.addHandler(myHandler)
    myLogLevelStr = _parseLogLevel(aLogLevelStr) 
    myLogger.setLevel(myLogLevelStr)
    myLogger.info('******************** %s. Logging Started ********************' % anAppName)
    return myLogger
    
def closeLogger(aLogger):
    """ Deinitialize logger """
    aLogger.info('******************** Logging Finished ********************')

def daemonize(aDaemonCurDir = '/'):
    """
    Detach the process from the controlling terminal and run it in the background
    """
    try:
        myPid = os.fork()
    except OSError as e:
        raise Exception("%s. Errno: %d" % (e.strerror, e.errno))
    if (myPid == 0):
        # child
        os.setsid()
        try:
            # second fork is to guarantee that the child is no longer a session leader, preventing the daemon from ever acquiring a controlling terminal.
            myPid = os.fork()
        except OSError as e:
            raise Exception("%s. Errno: %d" % (e.strerror, e.errno))
        if (myPid == 0):
            # child
            os.chdir(aDaemonCurDir)
            os.umask(0)
            
            _close_all_fds()
            dev_null = os.devnull if hasattr(os, "devnull") else '/dev/null' 
            os.open(dev_null, os.O_RDWR)    # STDIN
            os.dup2(0, 1) # STDOUT
            os.dup2(0, 2) # STDERR
                        
        else:
            os._exit(0) # Exit parent (the first child) of the second child.
    else:
        os._exit(0) # Exit parent of the first child.

def _close_all_fds():
    DEF_MAXFD = 2048
    import resource        # Resource usage information.
    maxfd = resource.getrlimit(resource.RLIMIT_NOFILE)[1]
    if (maxfd == resource.RLIM_INFINITY):
        maxfd = DEF_MAXFD
  
    for fd in range(maxfd):
       try:
          os.close(fd)
       except OSError:
          pass

EmailFormat = Enum('plain', 'html', 'attachment')

def to_utf8(s):
    if IS_PYTHON2:
        if isinstance(s, unicode):
            return s.encode('utf-8')
        else:
            return s # just suppose it is already utf8. @todo proper implementation should have detected the encoding and convert to utf8 then...
    else:
        return s.encode('utf-8')
     
# if s is a sequence type it it joined to a string/bytearray separated with one space
def to_unicode(s, logger = None):
    if isinstance(s, list) or isinstance(s, tuple):
        if IS_PYTHON2:
            s = " ".join(s)
        else:
            s = b" ".join(s)
        
    needs_decode = False
    if IS_PYTHON2 and not isinstance(s, unicode):
        needs_decode = True
    if not IS_PYTHON2 and not isinstance(s, str):
        needs_decode = True
        
    if needs_decode:
        try:
            s = s.decode('utf-8')
        except UnicodeDecodeError as e: 
            if logger:
                logger.error("Failed to utf8 decode process output, 'bad' characters will be replaced with U+FFFD. %s. %s" % (str(e), formatTb()))
            s = s.decode('utf-8', 'replace')
    return s
            
def body_mime_type(aFmt):
    if aFmt == EmailFormat.plain:
        return "plain"
    elif aFmt in (EmailFormat.plain, EmailFormat.attachment):
        return "html"
    raise Ecxeption("Unsupported email format " + str(aFmt))

def sendEmailNotification(aFrom, aTo, aSubj, aBody, anAttachmentText, aFmt, anSmtpSvrHost, anSmtpSvrPort, aSmtpSvrUser, aSmtpSvrPassword):
    """ 
    Sends email notification
    
    aFrom - sender address 
    aTo - list or tuple of correspondent addresses 
    aSubj - subject string 
    aBody - message body string
    anAttachmentText - message attachment text if format is attachment, otherwise None
    aFmt - format, one of EmailFormat
    anSmtpSvrHost, anSmtpSvrPort - SMTP Server location
    aSmtpSvrUser, aSmtpSvrPassword - SMTP Server credentials (skipped if None)
    """
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    from email.utils import formatdate

    if aFmt not in EmailFormat:
        raise Exception("%s is not a valid email format" % aFmt)

    if aFmt == EmailFormat.attachment and anAttachmentText is not None:
        msg = MIMEMultipart()
        attachment = MIMEText(to_utf8(anAttachmentText), 'plain', 'utf-8')
        attachment.add_header('Content-Disposition', 'attachment', filename='build.log')           
        msg.attach(attachment)
        msg.attach(MIMEText(to_utf8(aBody), 'html', 'utf-8'))
    else:
        msg = MIMEText(to_utf8(aBody), body_mime_type(aFmt), 'utf-8')
        
    msg['Subject'] = aSubj
    msg['From'] = aFrom
    msg['To'] = ', '.join(aTo)
    msg['Date'] = formatdate()
    
    mySmtpSvr = smtplib.SMTP(anSmtpSvrHost, anSmtpSvrPort)
    if aSmtpSvrUser and (aSmtpSvrPassword is not None):
        mySmtpSvr.login(aSmtpSvrUser, aSmtpSvrPassword)

    mySmtpSvr.sendmail(aFrom, aTo, msg.as_string())
    mySmtpSvr.quit()


class SysSingletonCreateError(Exception):
    def __init__(self, anAppName, anAppPid):
        self.__appName = anAppName
        self.__appPid = anAppPid
    def __str__(self):
        return "%s is already running (pid=%d)" % (self.__appName, self.__appPid)

class SysSingleton:
    """ The object of this class represents the system-wide single instance of the running app """
    def __init__(self, anAppName, aRecursive = True):
        """ Throws SysSingletonCreateError if such app singleton already exists (app is running), other exceptions for the rest """
        self.__isCreated = False
        self.__mutexPath = '/var/run/%s.pid' % anAppName

        if not os.access(self.__mutexPath, os.F_OK):
            if not os.access('/var/run/', os.F_OK):
                os.makedirs('/var/run/')
            myMutexFile = open(self.__mutexPath, 'w')
            myMutexFile.write("%d\n" % os.getpid())
            myMutexFile.close()
            self.__isCreated = True
            return

        myMutexFile = open(self.__mutexPath, 'r')
        myPid = int(myMutexFile.readline())
        myMutexFile.close()
        if myPid == os.getpid():
            if aRecursive:
                return
            raise SysSingletonCreateError(anAppName, myPid)

        if isPidExist(myPid):
            raise SysSingletonCreateError(anAppName, myPid)

        myMutexFile = open(self.__mutexPath, 'w')
        myMutexFile.write("%d\n" % os.getpid())
        myMutexFile.close()
        self.__isCreated = True

    def __del__(self):
        if self.__isCreated: 
            try:
                os.remove(self.__mutexPath) 
            except:
                pass

def isPidExist(aPid):
    try:
        os.kill(aPid, 0)
        return True
    except OSError as err:
        import errno
        return err.errno == errno.EPERM


def formatTimeDelta(aTimeDelta):
    """Return string representation of time delta as 'x day(s), y hour(s), z min, s sec' for pretty-printing.
    
    param delta the instance of datetime.timedelta
    """
    mySeconds = aTimeDelta.seconds % 60 
    myMinutes = (aTimeDelta.seconds // 60) % 60
    myHours = (aTimeDelta.seconds // 3600) % 24
    myDays = aTimeDelta.days
    if myDays != 0:
        return "%u day(s), %u hour(s), %u min, %u sec" % (myDays, myHours, myMinutes, mySeconds)
    if myHours != 0:
        return "%u hour(s), %u min, %u sec" % (myHours, myMinutes, mySeconds)        
    if myMinutes != 0:
        return "%u min, %u sec" % (myMinutes, mySeconds)
    return "%u sec" % mySeconds

def getTotalSeconds(aTimeDelta):
    return aTimeDelta.days * 24 * 3600 + aTimeDelta.seconds
    
class ProcOutputConsumerThread(threading.Thread):
    def __init__(self,  aProc, aReadStdout = True, aLogger = None):
        self._proc = aProc
        self._readStdout = aReadStdout
        self._logger = aLogger        
        self._out = []   
        threading.Thread.__init__(self)

    def run(self):
        try:
            self._out = self._proc.stdout.readlines() if self._readStdout else self._proc.stderr.readlines()
        except BaseException as e:
            if self._logger:
                self._logger.error("%s: %s. %s" % (type(e), str(e), formatTb()))
        
    @property
    #@return output as unicode string
    def out(self):
        myOut = to_unicode(self._out, self._logger)
        return myOut.rstrip()

## Kill child process group
def kill_chld_pg(pgid):
    try:
        os.killpg(pgid, signal.SIGTERM)
        time.sleep(1)
        os.killpg(pgid, signal.SIGKILL) 
    except OSError as e:
        # tolerate 'No such process' error
        import errno
        if e.errno != errno.ESRCH:
            raise
    #os.waitpid(-1, os.WNOHANG)

# More precise than time.sleep
def wait(interval):
    import threading
    finished = threading.Event()
    finished.wait(interval)
    finished.set()
    del finished        
