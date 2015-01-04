#!/usr/bin/env python
# -*- coding: utf-8 -*-
#  Copyright (c) 2008-2015, Andrei Korostelev <andrei at korostelev dot net>
#
#  Before using this product in any way please read the license agreement.
#  If you do not agree to the terms in this agreement you are not allowed
#  to use this product or parts of it. You can read this license in the
#  file named LICENSE.
#

"""
Task ABC
"""


class Task:

    """ Task interface """

    def __init__(self):
        pass

    def execute(self):
        """ Execute task

        execute() attribute is a part of Task interface to be implemented by derived classes
        Return dictionary:
            "statusFlag"  : task execution success flag
            "statusDescr" : brief user-oriented description of the task execution status
            "stderr": optional, stderr output, if applicable
            "stdout": optional, stdout output, if applicable
        Throw Exception
        """
        raise NotImplementedError("No method defined to execute the task")
