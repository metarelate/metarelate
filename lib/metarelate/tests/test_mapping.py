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


class TestItem(tests.MetarelateTestCase):
    def test_eq_full_pass(self):
        i1 = metarelate.Item('data', 'notation')
        i2 = metarelate.Item('data', 'notation')
        self.assertEqual(i1, i2)
        i1 = metarelate.Item('data', '"notation"')
        i2 = metarelate.Item('data', 'notation')
        self.assertEqual(i1, i2)
        i1 = metarelate.Item('data', 'notation')
        i2 = metarelate.Item(i1)
        self.assertEqual(i1, i2)

    def test_eq_full_fail(self):
        i1 = metarelate.Item('data', 'notation')
        i2 = metarelate.Item('data', 'wibble')
        self.assertNotEqual(i1, i2)
        i1 = metarelate.Item('data', 'notation')
        i2 = metarelate.Item('wibble', 'notation')
        self.assertNotEqual(i1, i2)

    def test_eq_part_pass(self):
        i1 = metarelate.Item('data')
        i2 = metarelate.Item('data')
        self.assertEqual(i1, i2)

    def test_eq_part_fail(self):
        i1 = metarelate.Item('data')
        i2 = metarelate.Item('wibble')
        self.assertNotEqual(i1, i2)

    def test_eq_string_pass(self):
        i1 = metarelate.Item('data', 'notation')
        self.assertEqual(i1, 'data')
        self.assertEqual(i1, 'notation')

    def test_eq_string_fail(self):
        i1 = metarelate.Item('data', 'notation')
        self.assertNotEqual(i1, 'wibble')

    def test_complete(self):
        self.assertTrue(metarelate.Item('data', 'notation').complete)
        self.assertFalse(metarelate.Item('data').complete)
        self.assertFalse(metarelate.Item(None).complete)

    def test_immutable(self):
        item = metarelate.Item('data', 'notation')
        with self.assertRaises(TypeError):
            item.wibble = 'wobble'
        with self.assertRaises(TypeError):
            item.uri = 'uri'

    def test_uri_pass(self):
        item = metarelate.Item('http://www.metarelate.net/')
        self.assertTrue(item.is_uri())
        item = metarelate.Item('<http://www.metarelate.net/>')
        self.assertTrue(item.is_uri())

    def test_uri_fail(self):
        item = metarelate.Item('wibble')
        self.assertFalse(item.is_uri())


class TestProperty(tests.MetarelateTestCase):
    def setUp(self):
        self.prop = stock.property_cf_standard_name()
        self.uri = self.prop.uri
        self.name = self.prop.name
        self.value = self.prop.value
        self.operator = self.prop.operator
        self.cprop = metarelate.Property('uri', 'name',
                                       stock.property_component_cf(),
                                       'operator')

    def test_sync(self):
        with self.assertRaises(ValueError):
            metarelate.Property(self.uri, self.name, self.value)
        with self.assertRaises(ValueError):
            metarelate.Property(self.uri, self.name, operator=self.operator)

    def test_eq_pass(self):
        prop = metarelate.Property(self.uri, self.name,
                                 self.value, self.operator)
        self.assertEqual(self.prop, prop)

    def test_eq_pass_compound(self):
        cprop = metarelate.Property('uri', 'name',
                                  stock.property_component_cf(),
                                  'operator')
        self.assertEqual(self.cprop, cprop)

    def test_eq_fail(self):
        prop = metarelate.Property(self.uri, self.name.data,
                                 self.value, self.operator)
        self.assertNotEqual(self.prop, prop)
        prop = stock.property_um_stash()
        self.assertNotEqual(self.prop, prop)

    def test_eq_fail_compound(self):
        prop = metarelate.Property('uri', 'name', 'value', 'operator')
        self.assertNotEqual(self.cprop, prop)
        self.assertNotEqual(prop, self.cprop)

    def test_eq_item(self):
        self.assertEqual(self.prop, self.value)
        self.assertNotEqual(self.prop, self.name)

    def test_eq_string(self):
        self.assertEqual(self.prop, self.value.data)
        self.assertEqual(self.prop, self.value.notation)
        self.assertNotEqual(self.prop, self.name.data)
        self.assertNotEqual(self.prop, self.name.notation)

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


class TestPropertyComponent(tests.MetarelateTestCase):
    def setUp(self):
        self.pcomp = stock.property_component_cf()
        cprop = metarelate.Property('uri', 'name',
                                  stock.property_component_cf(),
                                  'operator')
        self.cpcomp = metarelate.PropertyComponent('uri', cprop)

    def test_empty(self):
        with self.assertRaises(ValueError):
            metarelate.PropertyComponent('uri', [])

    def test_eq_pass(self):
        self.assertEqual(self.pcomp, stock.property_component_cf())

    def test_eq_fail(self):
        properties = [prop for prop in self.pcomp.values()]
        pcomp = metarelate.PropertyComponent('uri', properties)
        self.assertNotEqual(self.pcomp, pcomp)

        pcomp = metarelate.PropertyComponent(self.pcomp.uri, properties[:-1])
        self.assertNotEqual(self.pcomp, pcomp)

        properties = [stock.property_cf_standard_name(),
                      stock.property_cf_units(),
                      stock.property_cf_type(),
                      stock.property_um_stash()]
        pcomp = metarelate.PropertyComponent(self.pcomp.uri, properties)

        properties = [stock.property_cf_standard_name(),
                      stock.property_cf_units(),
                      stock.property_um_stash()]
        pcomp = metarelate.PropertyComponent(self.pcomp.uri, properties)
        self.assertNotEqual(self.pcomp, pcomp)

        prop = stock.property_cf_standard_name()
        uri = prop.uri
        name = prop.name
        value = prop.value
        operator = prop.operator
        properties = [metarelate.Property(uri, name.data, value, operator),
                      stock.property_cf_units(),
                      stock.property_cf_type()]
        pcomp = metarelate.PropertyComponent(self.pcomp.uri, properties)
        self.assertNotEqual(self.pcomp, pcomp)

    def test_getitem(self):
        prop = stock.property_cf_standard_name()
        self.assertEqual(self.pcomp[prop.name], prop)
        self.assertEqual(self.pcomp[prop.name.notation], prop)
        self.assertIsNone(self.pcomp['wibble'])

    def test_getattr(self):
        prop = stock.property_cf_standard_name()
        self.assertEqual(self.pcomp.standard_name, prop)
        prop = stock.property_cf_units()
        self.assertEqual(self.pcomp.units, prop)
        prop = stock.property_cf_type()
        self.assertEqual(self.pcomp.type, prop)
        self.assertIsNone(self.pcomp.wibble)

    def test_len(self):
        self.assertEqual(len(self.pcomp), 3)

    def test_contains(self):
        prop = stock.property_cf_standard_name()
        self.assertTrue(prop in self.pcomp)
        self.assertTrue(prop.name in self.pcomp)
        self.assertTrue(prop.name.data in self.pcomp)
        self.assertTrue(prop.name.notation in self.pcomp)

        prop = stock.property_um_stash()
        self.assertFalse(prop in self.pcomp)
        self.assertFalse(prop.name in self.pcomp)
        self.assertFalse(prop.name.data in self.pcomp)
        self.assertFalse(prop.name.notation in self.pcomp)

    def test_simple(self):
        self.assertTrue(self.pcomp.simple)
        self.assertFalse(self.cpcomp.simple)

    def test_compound(self):
        self.assertTrue(self.cpcomp.compound)
        self.assertFalse(self.pcomp.compound)


class TestComponent(tests.MetarelateTestCase):
    def setUp(self):
        self.comp = stock.simple_component_cf()
        self.ccomp = stock.compound_component_cf()

    def test_empty(self):
        with self.assertRaises(ValueError):
            metarelate.Component('uri', [])

    def test_eq_pass(self):
        self.assertEqual(self.comp, stock.simple_component_cf())
        self.assertEqual(self.ccomp, stock.compound_component_cf())

    def test_eq_fail(self):
        comp = metarelate.Component('uri', stock.property_component_cf())
        self.assertNotEqual(self.comp, comp)

        components = [stock.simple_component_cf(),
                      stock.compound_component_cf()]
        comp = metarelate.Component(self.comp.uri, components)
        self.assertNotEqual(self.comp, comp)

        properties = stock.property_component_cf().values()
        pcomp = metarelate.PropertyComponent('uri', properties)
        comp = metarelate.Component(self.comp.uri, pcomp)
        self.assertNotEqual(self.comp, comp)

    def test_getitem(self):
        prop = stock.property_cf_standard_name()
        self.assertEqual(self.comp[prop.name], prop)
        self.assertEqual(self.comp[prop.name.notation], prop)
        self.assertEqual(self.comp[0], stock.property_component_cf())
        self.assertIsNone(self.comp['wibble'])

        self.assertEqual(self.ccomp[0], stock.simple_component_cf())

        with self.assertRaises(TypeError):
            self.ccomp[prop.name]
        with self.assertRaises(TypeError):
            self.ccomp[prop.name.notation]
        with self.assertRaises(TypeError):
            self.ccomp['wibble']

    def test_getattr(self):
        prop = stock.property_cf_standard_name()
        self.assertEqual(self.comp.standard_name, prop)
        prop = stock.property_cf_units()
        self.assertEqual(self.comp.units, prop)
        prop = stock.property_cf_type()
        self.assertEqual(self.comp.type, prop)
        self.assertIsNone(self.comp.wibble)

        with self.assertRaises(TypeError):
            self.ccomp.standard_name
        with self.assertRaises(TypeError):
            self.ccomp.units
        with self.assertRaises(TypeError):
            self.ccomp.type
        with self.assertRaises(TypeError):
            self.ccomp.wibble

    def test_len(self):
        self.assertEqual(len(self.comp), 1)
        self.assertEqual(len(self.ccomp), 1)

    def test_contains(self):
        prop = stock.property_cf_standard_name()
        self.assertTrue(prop in self.comp)
        self.assertTrue(prop.name in self.comp)
        self.assertTrue(prop.name.data in self.comp)
        self.assertTrue(prop.name.notation in self.comp)

        with self.assertRaises(TypeError):
            prop in self.ccomp
        with self.assertRaises(TypeError):
            prop.name in self.ccomp
        with self.assertRaises(TypeError):
            prop.name.data in self.ccomp
        with self.assertRaises(TypeError):
            prop.name.notation in self.ccomp

        prop = stock.property_um_stash()
        self.assertFalse(prop in self.comp)
        self.assertFalse(prop.name in self.comp)
        self.assertFalse(prop.name.data in self.comp)
        self.assertFalse(prop.name.notation in self.comp)

    def test_simple(self):
        self.assertTrue(self.comp.simple)
        self.assertFalse(self.ccomp.simple)

    def test_compound(self):
        self.assertTrue(self.ccomp.compound)
        self.assertFalse(self.comp.compound)


class TestConcept(tests.MetarelateTestCase):
    def setUp(self):
        self.con = stock.simple_concept_cf()
        self.ccon = stock.compound_concept_cf()

    def test_eq_pass(self):
        self.assertEqual(self.con, stock.simple_concept_cf())
        self.assertEqual(self.ccon, stock.compound_concept_cf())

    def test_eq_fail(self):
        con = metarelate.Concept(self.con.uri, 'scheme',
                               stock.property_component_cf())
        self.assertNotEqual(self.con, con)


class TestMapping(tests.MetarelateTestCase):
    def setUp(self):
        self.mapping = stock.simple_mapping_um_cf()

    def test_eq_pass(self):
        self.assertEqual(self.mapping, stock.simple_mapping_um_cf())

    def test_eq_fail(self):
        mapping = metarelate.Mapping('uri', stock.simple_concept_cf(),
                                     stock.simple_concept_um())
        self.assertNotEqual(self.mapping, mapping)

    def test_dot(self):
        self.check_dot(self.mapping)


if __name__ == '__main__':
    unittest.main()
