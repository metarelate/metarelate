from distutils.core import setup, Command
import os
import sys

import nose

class TestRunner(Command):
    description = 'Run the metOcean unit tests'
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        lib_dir = os.path.join(sys.path[0], 'lib')
        modules = []
        for module in os.listdir(lib_dir):
            path = os.path.join(lib_dir, module)
            tests_path = os.path.join(path, 'tests')
            if path not in ['.git', '.svn'] and os.path.exists(tests_path):
                modules.append('{}.tests'.format(module))

        if not modules:
            raise ValueError('No tests were found to run.')

        n_processors = 1
        args = ['', 'module', '--processes={}'.format(n_processors),
                '--verbosity=2']

        success = True
        for module in modules:
            args[1] = module
            msg = 'Running test discovery on module {!r} with {} processor{}.'
            print(msg.format(module, n_processors,
                             's' if n_processors > 1 else ''))
            success &= nose.run(argv=args)
        if not success:
            exit(1)


setup(
    name='metarelate',
    version='1.0',
    description='Python packages for working with MetaRelate data',
    url='http://metarelate.net',
    package_dir={'': 'lib'},
    packages=['metarelate', 'metarelate.editor', 'metarelate.editor.app', 'metarelate.tests'],
    package_data={'metarelate': ['etc/site.cfg'],
                  'metarelate.editor': ['metarelate_editor.sh'],
                  'metarelate.editor.app': ['static/main.css', 'static/styles.css',
                                            'static/tmp_images/*', 'templates/*', 'templatetags/*',
                                            'static/img/*', 'static/js/*'],
                  'metarelate.tests': ['results/*/*', 'static/*/*', 'tdb/tdb']},
    data_files=[('lib/python2.7/site-packages/metarelate', ['COPYING', 'COPYING.LESSER']),
                ('bin', ['lib/run_mr_editor.py'])],
    author='marqh',
    author_email='markh@metarelate.net',
    cmdclass={'test': TestRunner},
    )
