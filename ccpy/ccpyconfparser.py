#
#  Andrei Korostelev <andrei at korostelev dot net>
#
#  Before using this product in any way please read the license agreement.
#  If you do not agree to the terms in this agreement you are not allowed
#  to use this product or parts of it. You can read this license in the
#  file named LICENSE.
#

"""
CcPy project configuration file parser
"""

import xml.etree.ElementTree as ET
import logging
from copy import deepcopy

from .common import LoggerName
from .util import EmailFormat, EmailSecurity, formatTb
from . import svntask
from . import gittask
from . import maketask
from . import exectask

Logger = logging.getLogger(LoggerName)
DefCcPyConfigFileName = "/etc/ccpy.conf"


def _get_elem_str_value(element, default_value):
    if element is not None:
        return element.text
    else:
        return default_value


def _get_elem_int_value(element, default_value):
    if element is not None:
        return int(element.text)
    else:
        return default_value


def _get_elem_bool_value(element, default_value):
    if element is not None:
        if element.text.lower() in ('on', 'yes', 'true'):
            return True
        elif element.text.lower() in ('off', 'no', 'false'):
            return False
        else:
            raise Exception("Invalid boolean value: %s in %s" % (element.text, element.tag))
    else:
        return default_value


def _get_elem_email_format_value(element, default_value):
    if element is not None:
        return EmailFormat[element.text]
    else:
        return default_value


def _get_elem_email_security_value(element, default_value):
    if element is not None:
        return EmailSecurity[element.text]
    else:
        return default_value


def _get_elem_list_value(element, default_value):
    if element is not None:
        return element.text.split(', ')
    else:
        return default_value


def _get_elem_tasks_value(element, default_value):
    if element is None:
        return default_value

    tasks = []
    for task in element:

        if task.tag == 'sourcecontrol':
            if task.attrib['type'] in ('svn', 'git'):
                url = task.find('./url').text
                workingDirectory = _get_elem_str_value(task.find('./workingDirectory'), '')
                preCleanWorkingDirectory = _get_elem_bool_value(
                    task.find('./preCleanWorkingDirectory'),
                    False)
                if task.attrib['type'] == 'svn':
                    tasks.append(svntask.SvnTask(url, workingDirectory, preCleanWorkingDirectory))
                else:  # git
                    tasks.append(gittask.GitTask(url, workingDirectory, preCleanWorkingDirectory))
            else:
                Logger.warning('Unsupported sourcecontrol type ' + task.attrib['type'])

        elif task.tag == 'make':
            workingDirectory = _get_elem_str_value(task.find('./workingDirectory'), '')
            args = _get_elem_str_value(task.find('./args'), '')
            timeout = _get_elem_int_value(task.find('./timeout'), 600)
            tasks.append(maketask.MakeTask(workingDirectory, args, timeout))

        elif task.tag == 'exec':
            executable = task.find('./executable').text
            workingDirectory = _get_elem_str_value(task.find('./workingDirectory'), '')
            args = _get_elem_str_value(task.find('./args'), '')
            timeout = _get_elem_int_value(task.find('./timeout'), 600)
            warningExitCode = _get_elem_int_value(task.find('./warningExitCode'), None)
            tasks.append(
                exectask.ExecTask(
                    executable,
                    workingDirectory,
                    args,
                    timeout,
                    warningExitCode))

        else:
            Logger.warning('Unsupported task ' + task.tag)

    return tasks


class ParseError(Exception):
    pass


class Projects:

    def __init__(self):
        self._projects = []
        self.cur = 0

    def exists(self, name):
        for project in self._projects:
            if project['name'] == name:
                return True
        return False

    def append(self, name,
               tasks,
               emailFrom, emailTo, emailFormat,
               emailServerHost, emailServerPort,
               emailServerSecurity,
               emailServerUsername, emailServerPassword,
               emailAttachments,
               failOnError):
        if self.exists(name):
            raise Exception(
                "Failed to add project because the project named '%s' already exists" %
                name)
        if tasks is None:
            tasks = []
        if emailTo is None:
            emailTo = []
        self._projects.append({'name': name,
                               'tasks': tasks,
                               'emailFrom': emailFrom,
                               'emailTo': emailTo,
                               'emailFormat': emailFormat,
                               'emailServerHost': emailServerHost,
                               'emailServerPort': emailServerPort,
                               'emailServerSecurity': emailServerSecurity,
                               'emailServerUsername': emailServerUsername,
                               'emailServerPassword': emailServerPassword,
                               'emailAttachments': emailAttachments,
                               'failOnError': failOnError})

    def addTask(self, name, task):
        if not self.exists(name):
            raise Exception(
                "Failed to add task because the project named '%s' does not exist" %
                name)
        for project in self._projects:
            if project['name'] == name:
                project['tasks'].append(task)

    def next(self):
        if self.cur >= len(self._projects):
            self.cur = 0
            raise StopIteration
        else:
            cur = self.cur
            self.cur = cur + 1
            key = self._projects[cur]['name']
            val = deepcopy(self._projects[cur])
            val.pop('name')
            return key, val

    def __next__(self):
        # for compatibility between Python 2 that uses next() and Python 3 that uses __next__()
        return self.next()

    def __iter__(self):
        return self

    def __getitem__(self, name):
        for project in self._projects:
            if project['name'] == name:
                retVal = deepcopy(project)
                retVal.pop('name')
                return retVal
        raise Exception("Project named '%s' does not exist" % name)

    def __len__(self):
        return len(self._projects)


def parse(aCcPyConfigFileName=DefCcPyConfigFileName):
    """Parse ccpy project configuration file

    Return  the instance if Projects class
    Projects and tasks within each project are returned in the order they appear in the config file.
    Supported tasks are: SvnTask, MakeTask and ExecTask
    Throw ParseError
    """
    try:
        Logger.debug("Reading ccpy configuration from %s..." % aCcPyConfigFileName)
        tree = ET.parse(aCcPyConfigFileName)
        root = tree.getroot()
        if (root.tag != 'ccpy'):
            raise Exception('Invalid root tag name: ' + root.tag)

        projects = Projects()
        for projectElem in root.findall('./project'):
            tasks = _get_elem_tasks_value(projectElem.find('./tasks'), None)
            emailFrom = _get_elem_str_value(projectElem.find('./emailNotification/from'), "")
            emailTo = _get_elem_list_value(projectElem.find('./emailNotification/to'), None)
            emailFormat = _get_elem_email_format_value(
                projectElem.find('./emailNotification/format'),
                EmailFormat.attachment)
            emailServerHost = _get_elem_str_value(
                projectElem.find('./emailNotification/server'),
                'localhost')
            emailServerPort = _get_elem_int_value(
                projectElem.find('./emailNotification/port'),
                25)
            emailServerSecurity = _get_elem_email_security_value(
                projectElem.find('./emailNotification/security'),
                EmailSecurity.none)
            emailServerUsername = _get_elem_str_value(
                projectElem.find('./emailNotification/username'),
                None)
            emailServerPassword = _get_elem_str_value(
                projectElem.find('./emailNotification/password'),
                None)
            emailAttachments = []
            for emailAttachment in projectElem.findall('./emailNotification/attachment'):
                emailAttachments.append(emailAttachment.text)
            failOnError = _get_elem_bool_value(projectElem.find('./failOnError'), True)

            projects.append(projectElem.attrib['name'],
                            tasks=tasks,
                            emailFrom=emailFrom,
                            emailTo=emailTo,
                            emailFormat=emailFormat,
                            emailServerHost=emailServerHost,
                            emailServerPort=emailServerPort,
                            emailServerSecurity=emailServerSecurity,
                            emailServerUsername=emailServerUsername,
                            emailServerPassword=emailServerPassword,
                            emailAttachments=emailAttachments,
                            failOnError=failOnError)

        return projects

    except Exception as e:
        raise ParseError(
            "Failed to parse %s. %s: %s. %s" %
            (aCcPyConfigFileName, type(e), str(e), formatTb()))
