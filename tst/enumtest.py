#!/usr/bin/env python
# -*- coding: utf-8 -*-
#  HeadURL : $HeadURL: svn://korostelev.net/CcPy/Trunk/tst/enumtest.py $
#  Id      : $Id: enumtest.py 78 2009-01-31 21:09:13Z akorostelev $
#

"""
Unit tests for enum
"""

import sys
import unittest
from copy import deepcopy
sys.path.append("..")
import ccpy.util as util
from ccpy.enum import Enum


class UtilTestCase(unittest.TestCase):

    def testEnum(self):
        try:
            clrs = Enum('red', 'green', 'blue')

            self.assertTrue(clrs.red in clrs)
            self.assertTrue("red" in clrs)
            self.assertTrue(clrs.green in clrs)
            self.assertTrue("green" in clrs)
            self.assertTrue(clrs.blue in clrs)
            self.assertTrue("blue" in clrs)
            self.assertTrue("yellow" not in clrs)

            self.assertEqual(clrs.red.index, 0)
            self.assertEqual(clrs.green.index, 1)
            self.assertEqual(clrs.blue.index, 2)

            self.assertEqual(clrs[0], clrs.red)
            self.assertEqual(clrs['red'], clrs.red)
            self.assertEqual(clrs[1], clrs.green)
            self.assertEqual(clrs['green'], clrs.green)
            self.assertEqual(clrs[2], clrs.blue)
            self.assertEqual(clrs['blue'], clrs.blue)

            self.assertEqual(str(clrs.red), "red")
            self.assertEqual(str(clrs[0]), "red")
            self.assertEqual(str(clrs['red']), "red")
            self.assertEqual(str(clrs.green), "green")
            self.assertEqual(str(clrs[1]), "green")
            self.assertEqual(str(clrs['green']), "green")
            self.assertEqual(str(clrs.blue), "blue")
            self.assertEqual(str(clrs[2]), "blue")
            self.assertEqual(str(clrs['blue']), "blue")

            self.assertTrue(clrs.green > clrs.red)
            self.assertTrue(clrs.blue > clrs.green)

            green_cpy = deepcopy(clrs.green)
            self.assertTrue(clrs.green in clrs)
            self.assertTrue("green" in clrs)
            self.assertEqual(clrs.green.index, 1)
            self.assertEqual(str(clrs.green), "green")
            self.assertEqual(green_cpy, clrs.green)

            same_clrs = Enum('red', 'green', 'blue')
            self.assertEqual(same_clrs, clrs)
            self.assertEqual(same_clrs.red, clrs.red)
            self.assertEqual(same_clrs.green, clrs.green)
            self.assertEqual(same_clrs.blue, clrs.blue)
            self.assertTrue(same_clrs.green > clrs.red)
            self.assertTrue(same_clrs.blue > clrs.green)

            another_clrs = Enum('red', 'blue', 'green')
            self.assertNotEqual(another_clrs, clrs)
            self.assertNotEqual(another_clrs.red, clrs.red)
            self.assertNotEqual(another_clrs.green, clrs.green)
            self.assertNotEqual(another_clrs.blue, clrs.blue)

        except BaseException as e:
            print(("Error. %s. %s. %s" % (type(e), str(e), util.formatTb())))
            self.assertTrue(False)

if __name__ == '__main__':
    unittest.main()
