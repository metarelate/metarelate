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
Unit tests for the `metarelateTest.Component` class.

"""

import unittest

import metarelate
import metarelate.tests as tests
import metarelate.tests.stock as stock


class Test___init___data(tests.MetarelateTestCase):
    def test_uri_only(self):
        comp = metarelate.Component('uri')

    def test_prop_type(self):
        with self.assertRaises(TypeError):
            metarelate.Component('uri', properties=['aprop'])

    def test_comp_type(self):
        with self.assertRaises(TypeError):
            metarelate.Component('uri', components=['acomp'])

class Test_checks(tests.MetarelateTestCase):
    def test_eq_pass(self):
        comp1 = stock.simple_component_cf()
        comp2 = stock.simple_component_cf()
        self.assertEqual(comp1, comp2)

    def test_eq_fail(self):
        comp1 = stock.simple_component_cf()
        comp3 = stock.simple_component_um()
        self.assertNotEqual(comp1, comp3)

class Test_attrs(tests.MetarelateTestCase):
    def test_getattr(self):
        prop = stock.property_cf_standard_name()
        comp = stock.simple_component_cf()
        self.assertEqual(comp.standard_name, prop)
        with self.assertRaises(AttributeError):
            comp.wibble

    def test_setattr(self):
        prop = stock.property_cf_units()
        ctype = '<http://def.cfconventions.org/datamodel/Field>'
        acomp = metarelate.Component(None, com_type=ctype,
                                     properties=[prop])
        data = '<http://def.cfconventions.org/datamodel/standard_name>'
        notation = 'standard_name'
        ptype = metarelate.Item(data, notation)
        data = '<http://def.cfconventions.org/standard_names/x_wind'
        notation = 'x_wind'
        value = metarelate.Item(data, notation)
        acomp.standard_name = metarelate.Property(None, ptype=ptype,
                                                  closematch=value)
        self.assertTrue(isinstance(acomp.standard_name, metarelate.Property))

    def test_len(self):
        comp = stock.simple_component_cf()
        self.assertEqual(len(comp), 2)

    def test_simple(self):
        comp = stock.simple_component_cf()
        self.assertTrue(comp.simple)

    def test_compound(self):
        comp = stock.compound_component_cf()
        self.assertFalse(comp.simple)

if __name__ == '__main__':
    unittest.main()
