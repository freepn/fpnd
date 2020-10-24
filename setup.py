# -*- coding: utf-8 -*-
"""Setup file for fpnd node tools."""
import ast
import codecs

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


def read_file(filename):
    """
    Read a utf8 encoded text file and return its contents.
    """
    with codecs.open(filename, 'r', 'utf8') as f:
        return f.read()


for line in read_file('node_tools/__init__.py').splitlines():
    if line.startswith('__version__'):
        version = ast.literal_eval(line.split('=', 1)[1].strip())
        break

# make setuptools happy with PEP 440-compliant post version
# (enable this for patch releases using n.n.n-n)
FPND_VERSION = version
REL_TAG = FPND_VERSION.replace('-', 'p')

FPND_DOWNLOAD_URL = (
    'https://github.com/sarnold/fpnd/tarball/' + REL_TAG
)

setup(
    name='fpnd',
    packages=['node_tools',],
    data_files=[
        ('lib/fpnd', ['bin/fpn0-down.sh',
                      'bin/fpn0-setup.sh',
                      'bin/fpn1-down.sh',
                      'bin/fpn1-setup.sh',
                      'bin/show-geoip.sh',
                      'bin/ping_google.sh',
                      'bin/ping_gateway.sh',
                      'etc/fpnd.ini',
                      'scripts/fpnd.py',
                      'scripts/msg_responder.py',
                      'scripts/msg_subscriber.py']),
    ],
    version=FPND_VERSION,
    license='AGPL-3.0',
    description='Python and shell fpnd node tools.',
    long_description=read_file('README.rst'),
    url='https://github.com/freepn/fpnd',
    author='Stephen L Arnold',
    author_email='nerdboy@gentoo.org',
    download_url=FPND_DOWNLOAD_URL,
    keywords=['freepn', 'vpn', 'p2p'],
    install_requires=[
        'appdirs @ git+https://github.com/ActiveState/appdirs@1.4.1',
        'datrie @ git+https://github.com/freepn/datrie@0.8.1',
        'diskcache @ git+https://github.com/grantjenks/python-diskcache@v4.1.0',
        'nanoservice @ git+https://github.com/freepn/nanoservice@0.7.2p1',
        'python-daemon @ git+https://github.com/freepn/python-daemon@0.2.3',
        'schedule @ git+https://github.com/freepn/schedule@0.6.0p2',
        'ztcli-async @ git+https://github.com/freepn/ztcli-async@0.0.7',
    ],
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: Console',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3',
        'Natural Language :: English',
        "Topic :: System :: Operating System Kernels :: Linux",
        "Topic :: System :: Networking",
        'Topic :: Security',
    ],
)
