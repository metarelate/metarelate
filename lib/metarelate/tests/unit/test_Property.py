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
import metarelate.fuseki
import metarelate.tests as tests
import metarelate.tests.stock as stock


class Test_StatementProperty(tests.MetarelateTestCase):
    def setUp(self):
        self.prop = stock.property_cf_standard_name()

    def test_eq(self):
        other = stock.property2_cf_standard_name()
        self.assertNotEqual(self.prop, other)

    def test_get_identifiers(self):
        expected = {'standard_name': 
                    'tendency_of_sea_ice_thickness_due_to_dynamics'}
        with metarelate.fuseki.FusekiServer() as fu_p:
            self.assertEqual(self.prop.get_identifiers(fu_p),
                             expected)


if __name__ == '__main__':
    unittest.main()
