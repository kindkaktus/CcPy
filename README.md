CcPy
============================

Introduction
---------------------

CruisecControl.py (CcPy) is (yet another) Automatic Continuous Integration Server. 
The development is inspired by the CruiseControl Continuous Integration Server 
(http://confluence.public.thoughtworks.org/display/CCNET/Welcome+to+CruiseControl.NET).
The main idea is to create a backend capable of running on various *nix flavours while making it possible 
to use conventional CruiseControl.NET frontend tools such as http://ccnet.sourceforge.net/CCNET/CCTray.html
to control a build process.

CcPy is written in Python.


Features
---------------------
- Runs on any unix-derived system (written in Python)
- Supports svn repositories
- Can run on schedule or on demand
- Notifies on build results by email


Quick start
---------------------

Prerequisites:
    CcPy requires Python 2.5+ and python-expat module

To install CcPy:
  python setup.py [install]

Start CcPy daemon: 
    python ccpyd.py [--force-continue|--force-once] 
