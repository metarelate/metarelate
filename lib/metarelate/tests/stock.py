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
A collection of routines that create standard metarelate mappings for
test purposes.

"""

import metarelate


def property_cf_standard_name():
    data = '<http://def.cfconventions.org/datamodel/standard_name>'
    notation = 'standard_name'
    ptype = metarelate.Item(data, notation)

    data = '<http://def.cfconventions.org/standard_names/' \
        'tendency_of_sea_ice_thickness_due_to_dynamics>'
    notation = 'tendency_of_sea_ice_thickness_due_to_dynamics'
    value = metarelate.Item(data, notation)

    uri = '<http://www.metarelate.net/test/property/test_p001'
    return metarelate.Property(uri, ptype=ptype, closematch=value)

def property2_cf_standard_name():
    data = '<http://def.cfconventions.org/datamodel/standard_name>'
    notation = 'standard_name'
    ptype = metarelate.Item(data, notation)

    data = '<http://def.cfconventions.org/standard_names/x_wind'
    notation = 'x_wind'
    value = metarelate.Item(data, notation)

    uri = '<http://www.metarelate.net/test/property/test_p002'
    return metarelate.Property(uri, ptype=ptype, closematch=value)

def property_cf_units():
    data = '<http://def.cfconventions.org/datamodel/units>'
    notation = 'units'
    name = metarelate.Item(data, notation)

    value = 'm s-1'#metarelate.Item(data='"m s-1"', notation='m s-1')

    uri = '<http://www.metarelate.net/test/property/test_p003>'
    return metarelate.Property(uri, ptype=name, value=value)


def property_um_stash():
    data = '<http://reference.metoffice.gov.uk/def/um/umdp/F3/stash>'
    notation = 'stash'
    name = metarelate.Item(data, notation)

    data = '<http://reference.metoffice.gov.uk/def/um/stash/concept/' \
        'm02s32i202>'
    notation = 'm02s32i202'
    closematch = metarelate.Item(data, notation)

    uri = '<http://www.metarelate.net/test/property/test_p004>'
    return metarelate.Property(uri, ptype=name, closematch=closematch)


def simple_component_cf():
    properties = [property_cf_standard_name(),
                  property_cf_units()]
    uri = '<http://www.metarelate.net/test/component/test_c001>'
    ctype = '<http://def.cfconventions.org/datamodel/Field>'
    return metarelate.Component(uri, com_type=ctype,
                                properties=properties)

def simple_component2_cf():
    properties = [property2_cf_standard_name(),
                  property_cf_units()]
    uri = '<http://www.metarelate.net/test/component/test_c002>'
    ctype = '<http://def.cfconventions.org/datamodel/Field>'
    return metarelate.Component(uri, com_type=ctype,
                                properties=properties)


def compound_component_cf():
    uri = '<http://www.metarelate.net/test/component/test_c003>'
    ctype = '<http://def.cfconventions.org/datamodel/Field>'
    return metarelate.Component(uri, com_type=ctype,
                                components=[simple_component_cf(),
                                            simple_component2_cf()])

def simple_component_um():
    uri = '<http://www.metarelate.net/test/component/test_c002>'
    ctype='<http://reference.metoffice.gov.uk/um/f3/stash>'
    return metarelate.Component(uri, com_type=ctype,
                                properties=[property_um_stash()])



def simple_mapping_um_cf():
    uri = '<http://www.metarelate.net/test/mapping/test_m001>'
    return metarelate.Mapping(uri, source=simple_component_um(),
                              target=simple_component_cf())
