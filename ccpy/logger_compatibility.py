#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import logging
import os
from stat import ST_DEV, ST_INO

# WatchedFileHandler is provided by Python standard library starting Python 3
# The earlier Python versions can use the implementation below which is
# adapted from the Python 3


class WatchedFileHandler(logging.FileHandler):

    """
    A handler for logging to a file, which watches the file
    to see if it has changed while in use. This can happen because of
    usage of programs such as newsyslog and logrotate which perform
    log file rotation. This handler, intended for use under Unix,
    watches the file to see if it has changed since the last emit.
    (A file has changed if its device or inode have changed.)
    If it has changed, the old file stream is closed, and the file
    opened to get a new stream.

    This handler is not appropriate for use under Windows, because
    under Windows open files cannot be moved or renamed - logging
    opens the files with exclusive locks - and so there is no need
    for such a handler. Furthermore, ST_INO is not supported under
    Windows; stat always returns zero for this value.

    This handler is based on a suggestion and patch by Chad J.
    Schroeder.
    """

    def __init__(self, filename, mode='a', encoding=None):
        logging.FileHandler.__init__(self, filename, mode, encoding)
        if not os.path.exists(self.baseFilename):
            self.dev, self.ino = -1, -1
        else:
            stat = os.stat(self.baseFilename)
            self.dev, self.ino = stat[ST_DEV], stat[ST_INO]

    def emit(self, record):
        """
        Emit a record.

        First check if the underlying file has changed, and if it
        has, close the old stream and reopen the file to get the
        current stream.
        """
        if not os.path.exists(self.baseFilename):
            stat = None
            changed = 1
        else:
            stat = os.stat(self.baseFilename)
            changed = (stat[ST_DEV] != self.dev) or (stat[ST_INO] != self.ino)
        if changed and self.stream is not None:
            self.stream.flush()
            self.stream.close()
            self.stream = open(self.baseFilename, self.mode)
            if stat is None:
                stat = os.stat(self.baseFilename)
            self.dev, self.ino = stat[ST_DEV], stat[ST_INO]
        logging.FileHandler.emit(self, record)
