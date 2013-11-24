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


import datetime

from django import template

import metarelate.prefixes as pref

register = template.Library()

pre = pref.Prefixes()
inv_pre = dict([[v,k] for k,v in pre.items()])

@register.filter
@register.simple_tag
def prefix_uri(adict, keys=''):
    uri = multi_key(adict, keys)
    if uri and uri.startswith('<http:'):
        label = uri
        url = uri.lstrip('<').rstrip('>')
        for p in inv_pre:
            if url.startswith(p):
                suffix = url.split(p)[1]
                label = '{}: {}'.format(inv_pre[p],suffix)
    else:
        label = uri
    return label


@register.filter(name='dictKeyLookup')
@register.simple_tag
def dictKeyLookup(adict, key):
    # Try to fetch from the dict, and if it's not found return an empty string.
    return adict.get(key, None)

@register.filter
@register.simple_tag
def multi_key(adict, keys=''):
    key_list = keys.split(',')
    result = adict
    for key in key_list:
        if result:
            if isinstance(result, dict):
                result = result.get(key)
            else:
                result = None
    return result

@register.filter
@register.simple_tag
def get_keys(adict):
    return adict.keys()


@register.filter
@register.simple_tag
def kv(tuple, index):
    return tuple[int(index)]


@register.tag
def render_format(parser, token):
    try:
        member_string = str(token)
    except ValueError:
        raise template.TemplateSyntaxError("you must pass a dict")
    return MemberNode(member_string)

class MemberNode(template.Node):
    def __init__(self, member_string):
#        print member_string
        self.member_string = member_string
    def render(self, context):
        return self.member_string



class CurrentTimeNode(template.Node):
    def __init__(self, format_string):
        self.format_string = format_string
    def render(self, context):
        return datetime.datetime.now().strftime(self.format_string)

@register.tag
def current_time(parser, token):
    try:
        # split_contents() knows not to split quoted strings.
        tag_name, format_string = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError("%r tag requires a single argument"
                                           % token.contents.split()[0])
    if not (format_string[0] == format_string[-1] and \
            format_string[0] in ('"', "'")):
        ec = "%r tag's argument should be in quotes" % tag_name
        raise template.TemplateSyntaxError(ec)
    return CurrentTimeNode(format_string[1:-1])
