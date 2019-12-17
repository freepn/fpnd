# -*- coding: utf-8 -*-
"""Setup file for fpnd node tools."""
import codecs

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


__version__ = '0.0.4'

FPND_DOWNLOAD_URL = (
    'https://github.com/sarnold/fpnd/tarball/' + __version__
)


def read_file(filename):
    """
    Read a utf8 encoded text file and return its contents.
    """
    with codecs.open(filename, 'r', 'utf8') as f:
        return f.read()


setup(
    name='fpnd',
    packages=['node_tools',],
    data_files=[
        ('sbin', ['bin/fpn0-down',
                  'bin/fpn0-setup',
                  'bin/fpn1-down',
                  'bin/fpn1-setup']),
        ('share/fpnd/etc',  ['etc/fpnd.ini']),
        ('share/fpnd/init', ['etc/fpnd.service',
                             'etc/fpnd.sysvinit',
                             'etc/fpnd.openrc']),
    ],
    scripts=[
        'scripts/fpnd'
    ],
    version=__version__,
    license='AGPL-3.0',
    description='Python fpnd node tools.',
    long_description=read_file('README.rst'),
    url='https://github.com/sarnold/fpnd',
    author='Stephen L Arnold',
    author_email='nerdboy@gentoo.org',
    download_url=FPND_DOWNLOAD_URL,
    keywords=['freepn', 'vpn', 'p2p'],
    install_requires=[
        'ztcli-async @ git+https://github.com/sarnold/ztcli-async',
        'daemon @ git+https://github.com/sarnold/python-daemon',
        'diskcache @ git+https://github.com/grantjenks/python-diskcache@v4.1.0',
    ],
    classifiers=[
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: LGPL-3.0 License',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX',
        'Programming Language :: Python :: 3',
        'Natural Language :: English',
    ],
    python_requires='!=3.0.*,!=3.1.*,!=3.2.*,!=3.3.*,!=3.4.*',
)
