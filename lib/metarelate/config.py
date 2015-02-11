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
Provides support for site configuration of metarelate.

"""

import ConfigParser
import os
import warnings


# metarelate configuration file sections.
_SECTION_FUSEKI = 'fuseki'
_SECTION_RESOURCE = 'resource'
_SECTION_SYSTEM = 'system'
_SECTION_THREADING = 'threading'

# metarelate configuration option defaults.
_DEFAULT_FUSEKI_PORT = 3131
_DEFAULT_FUSEKI_TEST_PORT = 3636
_DEFAULT_FUSEKI_TIMEOUT_ATTEMPTS = 1000
_DEFAULT_FUSEKI_TIMEOUT_SLEEP = 0.1
_DEFAULT_WORKERS = 8

# environment variable prefix
ENV_PREF = 'METARELATE_'


def _get_option(parser, section, option, default=None):
    result = default
    if parser.has_option(section, option):
        result = parser.get(section, option)
    return result


def _get_dir_option(parser, section, option, default=None):
    result = default
    if parser.has_option(section, option):
        value = parser.get(section, option)
        if os.path.isdir(value):
            result = value
        else:
            msg = 'Metarelate Configuration - Invalid section {!r}, ' \
                'option {!r} directory path {!r}.'
            warnings.warn(msg.format(section, option, value))
    return result


def update(config):
    config_dir = os.path.join(config['root_dir'], 'etc')
    if os.path.isdir(config_dir):
        config['config_dir'] = config_dir
        defaults = dict(root_dir=config['root_dir'])
        parser = ConfigParser.SafeConfigParser(defaults)
        config_file = os.path.join(config_dir, 'site.cfg')
        if os.path.isfile(config_file):
            config['config_file'] = config_file
            parser.read(config_file)

            option = 'jena_dir'
            result = _get_dir_option(parser, _SECTION_SYSTEM, option)
            if result is None:
                msg = 'Metarelate Configuration - Missing Apache Jena ' \
                    'semantic web framework base directory. ' \
                    'Section {!r}, option {!r}.'
                warnings.warn(msg.format(_SECTION_SYSTEM, option))
            else:
                config[option] = result

            option = 'fuseki_dir'
            result = _get_dir_option(parser, _SECTION_SYSTEM, option)
            if result is None:
                msg = 'Metarelate Configuration - Missing Apache ' \
                    'Fuseki SPARQL server base directory. ' \
                    'Section {!r}, option {!r}.'
                warnings.warn(msg.format(_SECTION_SYSTEM, option))
            else:
                config[option] = result

            option = 'static_dir'
            result = None
            env_var = ENV_PREF + option.upper()
            if os.environ.has_key(env_var):
                result = os.environ[env_var]
            # if result is None:
            #     msg = ('Metarelate Configuration - Missing static data '
            #            'directory: environment variable {!r} for the Apache '
            #            'Jena triple store database.')
            #     raise ValueError(msg.format(env_var))
            # else:
            if result is not None:
                config[option] = result

            option = 'data_project'
            result = None
            env_var = ENV_PREF + option.upper()
            if os.environ.has_key(env_var):
                result = os.environ[env_var]
            if result is None:
                msg = ('Metarelate Configuration - Missing data project'
                       'name: environment variable {!r} for the static data.')
                raise ValueError(msg.format(env_var))
            else:
                config['fuseki_dataset'] = result

            option = 'tdb_dir'
            result = None
            env_var = ENV_PREF + option.upper()
            if os.environ.has_key(env_var):
                result = os.environ[env_var]
            if result is None:
                msg = ('Metarelate Configuration - Missing triplestore ' 
                       'directory: environment variable {!r} for the Apache '
                       'Jena triple store database.')
                raise ValueError(msg.format(env_var))
            else:
                if not os.path.exists(result):
                    try:
                        os.makedirs(result)
                    except OSError:
                        msg = ('Metarelate Configuration - triplestore '
                       'directory: environment variable {!r} for the Apache '
                       'Jena triple store database is not writeable.')
                        msg = msg.format(env_var)
                        raise OSError(msg)
                config['tdb_dir'] = os.path.join(result, 'tdb')
                config['log_dir'] = os.path.join(result, 'logs')
                if not os.path.exists(config['tdb_dir']):
                    os.mkdir(config['tdb_dir'])
                if not os.path.exists(config['log_dir']):
                    os.mkdir(config['log_dir'])
            option = 'test_static_dir'
            result = _get_dir_option(parser, _SECTION_RESOURCE, option)
            if result is None:
                msg = 'Metarelate Configuration - Missing test static data ' \
                    'directory for the Apache Jena database.' \
                    'Section {!r}, option {!r}.'
                warnings.warn(msg.format(_SECTION_RESOURCE, option))
            else:
                config[option] = result

            option = 'test_tdb_dir'
            result = _get_dir_option(parser, _SECTION_RESOURCE, option)
            if result is None:
                msg = 'Metarelate Configuration - Missing Apache Jena test ' \
                    'triple store database directory. ' \
                    'Section {!r}, option {!r}.'
                warnings.warn(msg.format(_SECTION_RESOURCE, option))
            else:
                config[option] = result

            option = 'port'
            result = _get_option(parser, _SECTION_FUSEKI, option,
                                 _DEFAULT_FUSEKI_PORT)
            try:
                config[option] = int(result)
            except ValueError:
                msg = 'Metarelate Configuration - Ignoring invalid port for ' \
                    'Apache Fuseki server. Section {!r}, option {!r}. ' \
                    'Defaulting to port {}.'
                warnings.warn(msg.format(_SECTION_FUSEKI, option,
                                         _DEFAULT_FUSEKI_PORT))
                config[option] = _DEFAULT_FUSEKI_PORT

            option = 'test_port'
            result = _get_option(parser, _SECTION_FUSEKI, option,
                                 _DEFAULT_FUSEKI_TEST_PORT)
            try:
                config[option] = int(result)
            except ValueError:
                msg = 'Metarelate Configuration - Ignoring invalid test port ' \
                    'for Apache Fuseki server. Section {!r}, option {!r}. ' \
                    'Defaulting to port {}.'
                warnings.warn(msg.format(_SECTION_FUSEKI, option,
                                         _DEFAULT_FUSEKI_TEST_PORT))
                config[option] = _DEFAULT_FUSEKI_TEST_PORT

            option = 'timeout_sleep'
            result = _get_option(parser, _SECTION_FUSEKI, option,
                                 _DEFAULT_FUSEKI_TIMEOUT_SLEEP)
            try:
                config[option] = float(result)
            except ValueError:
                msg = 'Metarelate Configuration - Ignoring invalid timeout ' \
                    'sleep for Apache Fuseki server. Section {!r}, ' \
                    'option {!r}. Defaulting to {} seconds.'
                warnings.warn(msg.format(_SECTION_FUSEKI, option,
                                         _DEFAULT_FUSEKI_TIMEOUT_SLEEP))
                config[option] = _DEFAULT_FUSEKI_TIMEOUT_SLEEP

            option = 'timeout_attempts'
            result = _get_option(parser, _SECTION_FUSEKI, option,
                                 _DEFAULT_FUSEKI_TIMEOUT_ATTEMPTS)
            try:
                config[option] = int(result)
            except ValueError:
                msg = 'Metarelate Configuration - Ignoring invalid timeout ' \
                    'cycle for Apache Fuseki server. Section {!r}, ' \
                    'option {!r}. Defaulting to {} attempts.'
                warnings.warn(msg.format(_SECTION_FUSEKI, option,
                                         _DEFAULT_FUSEKI_TIMEOUT_ATTEMPTS))
                config[option] = _DEFAULT_FUSEKI_TIMEOUT_ATTEMPTS

            option = 'num_workers'
            result = _get_option(parser, _SECTION_THREADING, option)
            try:
                config[option] = int(result)
            except ValueError:
                msg = ('Metarelate Configuration - Ignoring invalid num_workers '
                       'for threadin. Section {!r}, '
                       'option {!r}. Defaulting to {} attempts.')
                warnings.warn(msg.format(_SECTION_THREADING, option,
                                         _DEFAULT_WORKERS))
                config[option] = _DEFAULT_WORKERS
                
            
        else:
            msg = 'Metarelate Configuration - Missing configuration file {!r}'
            warnings.warn(msg.format(config_file))
    else:
        msg = 'Metarelate Configuration - Missing configuration directory {!r}'
        warnings.warn(msg.format(config_dir))
