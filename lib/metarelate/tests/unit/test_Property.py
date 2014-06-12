# (C) British Crown Copyright 2013, Met Office
#
# This file is part of metarelate.
#
# metarelate is free software: you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public License
# as published by the Free Software Foundation, either version 3 of
# the License, or (at your option) any later version.
#
# metarelate is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with metarelate. If not, see <http://www.gnu.org/licenses/>.
"""
Test the metarelate framework.

"""

import unittest

import metarelate
import metarelate.tests as tests
import metarelate.tests.stock as stock


# class Test___init___data(tests.MetarelateTestCase):

class Test_checks(tests.MetarelateTestCase):
    def setUp(self):
        self.prop = stock.property_cf_standard_name()
        self.uri = self.prop.uri
        self.ptype = self.prop.ptype
        self.closematch = self.prop.closematch
        self.cprop = metarelate.Property('uri', ptype=self.ptype,
                                       component=stock.simple_component_cf())

    def test_eq_pass(self):
        prop = metarelate.Property(self.uri, self.ptype,
                                 self.closematch)
        self.assertEqual(self.prop, prop)

    def test_eq_fail(self):
        prop = metarelate.Property(self.uri, self.ptype,
                                 self.closematch,
                                 defby='<http://metarelate.net/somegraph>')
        self.assertNotEqual(self.prop, prop)



    def test_simple(self):
        self.assertTrue(self.prop.simple)
        self.assertFalse(self.cprop.simple)

    def test_compound(self):
        self.assertTrue(self.cprop.compound)
        self.assertFalse(self.prop.compound)

    def test_complete(self):
        self.assertTrue(self.prop.complete)
        prop = metarelate.Property(self.uri, self.name)
        self.assertFalse(prop.complete)
        self.assertFalse(self.cprop.complete)


# class TestProperty(tests.MetarelateTestCase):

#     def test_sync(self):
#         with self.assertRaises(ValueError):
#             metarelate.Property(self.uri, self.name, self.value)
#         with self.assertRaises(ValueError):
#             metarelate.Property(self.uri, self.name, operator=self.operator)


#     def test_eq_pass_compound(self):
#         cprop = metarelate.Property('uri', 'name',
#                                   stock.property_component_cf(),
#                                   'operator')
#         self.assertEqual(self.cprop, cprop)

#     def test_eq_fail(self):
#         prop = metarelate.Property(self.uri, self.name.data,
#                                  self.value, self.operator)
#         self.assertNotEqual(self.prop, prop)
#         prop = stock.property_um_stash()
#         self.assertNotEqual(self.prop, prop)

#     def test_eq_fail_compound(self):
#         prop = metarelate.Property('uri', 'name', 'value', 'operator')
#         self.assertNotEqual(self.cprop, prop)
#         self.assertNotEqual(prop, self.cprop)

#     def test_eq_item(self):
#         self.assertEqual(self.prop, self.value)
#         self.assertNotEqual(self.prop, self.name)

#     def test_eq_string(self):
#         self.assertEqual(self.prop.closematch.data, self.closematch.data)
#         self.assertEqual(self.prop.closematch.notation, self.closematch.notation)
#         self.assertNotEqual(self.prop, self.ptype.data)
#         self.assertNotEqual(self.prop, self.ptype.notation)

#     def test_simple(self):
#         self.assertTrue(self.prop.simple)
#         self.assertFalse(self.cprop.simple)

#     def test_compound(self):
#         self.assertTrue(self.cprop.compound)
#         self.assertFalse(self.prop.compound)

#     def test_complete(self):
#         self.assertTrue(self.prop.complete)
#         prop = metarelate.Property(self.uri, self.name)
#         self.assertFalse(prop.complete)
#         self.assertFalse(self.cprop.complete)



if __name__ == '__main__':
    unittest.main()
