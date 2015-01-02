#!/usr/bin/env python
# (C) British Crown Copyright 2011 - 2012, Met Office
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

import os
import sys

if len(sys.argv) == 1:
    sys.argv.append('runserver')
    #sys.argv.append('--noreload')

from django.core.management import execute_from_command_line

import metarelate.editor.settings as settings

import metarelate.fuseki as fu

if __name__ == "__main__":
    with fu.FusekiServer() as server:
    # if True:
    #     server = fu.FusekiServer()
        #server.load()
        settings.fuseki_process = server
        # execute_from_command_line(settings)
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "metarelate.editor.settings")
        execute_from_command_line(sys.argv)

