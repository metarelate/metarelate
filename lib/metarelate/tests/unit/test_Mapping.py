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

class Test_checks(tests.MetarelateTestCase):
    def setUp(self):
        self.mapping = stock.simple_mapping_um_cf()

    def test_eq_pass(self):
        self.assertEqual(self.mapping, stock.simple_mapping_um_cf())

    def test_eq_fail(self):
        mapping = metarelate.Mapping('uri', stock.simple_component_cf(),
                                     stock.simple_component_um())
        self.assertNotEqual(self.mapping, mapping)

    def test_dot(self):
        self.check_dot(self.mapping)


if __name__ == '__main__':
    unittest.main()
