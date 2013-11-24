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
Provides unit test support specific to metarelate.

"""

from collections import defaultdict
import filecmp
import os
import shutil
import sys
import unittest
import warnings


class MetarelateTestCase(unittest.TestCase):
    """
    A subclass of :class:`unittest.TestCase` which provides metarelate
    specific testing functionality.

    """
    _assertion_count = defaultdict(int)

    def _unique_id(self):
        """
        Returns the unique ID for the current assertion.

        The ID is composed of two parts: a unique ID for the current test
        (which is itself composed of the module, class, and test names), and
        a sequential counter (specific to the current test) that is incremented
        on each call.

        """
        # N.B. unittest.TestCase.id() returns different values depending on
        # whether the test has been run explicitly, or via test discovery.
        bits = self.id().split('.')[-3:]
        if bits[0] == '__main__':
            file_name = os.path.basename(sys.modules['__main__'].__file__)
            bits[0] = os.path.splitext(file_name)[0]
        test_id = '.'.join(bits)

        # Derive the sequential dot ID within the test.
        assertion_id = self._assertion_count[test_id]
        self._assertion_count[test_id] += 1
        return '{}.{:03}'.format(test_id, assertion_id)

    def check_dot(self, mapping):
        """
        Checks that the dot representation of the provided mapping
        is as expected.

        Args:
        * mapping: The :class:`metarelate.Mapping` to be compared.

        Returns:
            Boolean.

        """
        def _make_dirs(fname):
            path = os.path.dirname(fname)
            if not os.path.isdir(path):
                # Handle possible race-condition between directory
                # existence check and creation.
                try:
                    os.makedirs(path)
                except OSError as err:
                    # Ignore file exists error.
                    if err.errno == 17:
                        pass

        unique_id = self._unique_id()
        expected_fname = os.path.join(os.path.dirname(__file__),
                                      'results', 'dot_expected',
                                      unique_id + '.dot')
        _make_dirs(expected_fname)

        result_fname = os.path.join(os.path.dirname(__file__),
                                    'results', 'dot_actual',
                                    'result_' + unique_id + '.dot')
        _make_dirs(result_fname)

        graph = mapping.dot()
        graph.write_dot(result_fname)

        if not os.path.exists(expected_fname):
            msg = 'Created expected dot output for test {!r}'
            warnings.warn(msg.format(unique_id))
            shutil.copy2(result_fname, expected_fname)

        return filecmp.cmp(expected_fname, result_fname)
