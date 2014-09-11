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
Test the metarelate Apache Fuseki server.

"""

import unittest

import metarelate
import metarelate.tests as tests
from metarelate.fuseki import FusekiServer

SCHEME_CF = '<http://def.scitools.org.uk/cfdatamodel/Field>'
SCHEME_UM = '<http://reference.metoffice.gov.uk/um/f3/UMField>'


class TestFuseki(tests.MetarelateTestCase):
    @classmethod
    def setUpClass(cls):
        cls.fuseki = FusekiServer(test=True)
        cls.fuseki.load()
        cls.fuseki.start()

    @classmethod
    def tearDownClass(cls):
        cls.fuseki.stop()

    def test_retrieve_um_cf(self):
        mappings = self.fuseki.retrieve_mappings(SCHEME_UM, SCHEME_CF)
        self.assertEqual(len(mappings), 1)
        imappings = self.fuseki.retrieve_mappings(SCHEME_CF, SCHEME_UM)
        self.assertEqual(len(imappings), 1)



if __name__ == '__main__':
    unittest.main()
