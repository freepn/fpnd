=====================================
 fpnd - FreePN Node Daemon and Tools
=====================================

.. image:: https://img.shields.io/github/license/freepn/fpnd
    :target: https://github.com/freepn/fpnd/blob/master/LICENSE

.. image:: https://img.shields.io/github/v/tag/freepn/fpnd?color=green&include_prereleases&label=latest%20release
    :target: https://github.com/freepn/fpnd/releases
    :alt: GitHub tag (latest SemVer, including pre-release)

.. image:: https://travis-ci.org/freepn/fpnd.svg?branch=master
    :target: https://travis-ci.org/freepn/fpnd

.. image:: https://img.shields.io/codecov/c/github/freepn/fpnd
    :target: https://codecov.io/gh/freepn/fpnd
    :alt: Codecov

.. image:: https://img.shields.io/codeclimate/maintainability/freepn/fpnd
    :target: https://codeclimate.com/github/freepn/fpnd


What is FreePN?  FreePN is aiming to be the first free, fast, anonymous,
unlimited-bandwidth peer-to-peer proxy application.

Yes, it's "free" (as in FOSS) and it's sort of like a VPN (except p2p).
FreePN is essentially an anonymizing p2p internet proxy using a "virtual
private cloud" of peers.


.. note:: This project is currently in a pre-Alpha state, with the
          requisite level of churn.  Stay tuned for the Alpha release!


Getting Started
===============

Not much to see here yet except test output; at this point we only target
Linux with at least `Python`_ 3.5.  Packages are available for Ubuntu and
Gentoo using the live ebuild in our `python overlay`_ and a `PPA on Launchpad`_.
The PPA sources can also be used to build Debian packages, however, we
don't (yet) support any "official" Debian packages.


.. _PPA on Launchpad: https://launchpad.net/~nerdboy/+archive/ubuntu/embedded
.. _python overlay: https://github.com/freepn/python-overlay


.. note:: This stack depends on both Python and nanomsg and the Ubuntu
          releases are just enough out of sync with Debian, so the PPA
          binaries are not usable directly on any specific Debian version
          (so must be rebuilt from source).


Prerequisites
-------------

A supported linux distribution, mainly something that uses `.ebuilds`
(eg, Gentoo or funtoo) or a supported Ubuntu series, currently xenial
16.0.4 LTS and bionic 18.0.4 LTS (see the above `PPA on Launchpad`_).

For the latter, make sure you have the ``gpg`` and ``add-apt-repository``
commands installed and then add the PPA:

::

  $ sudo apt-get install -y software-properties-common
  $ sudo add-apt-repository -y -s ppa:nerdboy/embedded

If the second command above does not run ``apt-get update`` automatically,
then you'll need to run it manually:

::

  $ sudo apt-get update

If you get a key error you will also need to manually import the PPA
signing key like so:

::

  $ sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys <PPA_KEY>

where <PPA_KEY> is the key shown in the launchpad PPA page under "Adding
this PPA to your system", eg, ``41113ed57774ed19`` for `Embedded device ppa`_.


.. _Embedded device ppa: https://launchpad.net/~nerdboy/+archive/ubuntu/embedded


Dev Install
-----------

As long as you have git and at least Python 3.5, then the "easy" dev
install is to clone this repository and install `tox`_ (optional) and the
`nanomsg`_ library (required).

`Install the overlay`_ and do the usual install dance; add ``FEATURES=test``
if you want the pytest deps::

  # FEATURES=test emerge net-misc/fpnd

or::

  $ sudo apt-get build-dep python3-fpnd
  $ sudo apt-get install tox

After cloning the repository, you can run the current tests with the
``tox`` command.  It will build a virtual python environment for each
installed version of python with all the python dependencies and run
the tests (including style checkers and test coverage).

::

  $ git clone https://github.com/freepn/fpnd
  $ cd fpnd
  $ tox

If you're on Ubuntu and you want to experiment with the current state
of fpnd, then just install the package after doing the above:

::

  $ sudo apt-get install python3-fpnd


.. _Install the overlay: https://github.com/freepn/python-overlay/blob/master/README.rst

Standards and Coding Style
--------------------------

Both pep8 and flake8 are part of the above test suite.  There are also
some CI code analysis checks for complexity and security issues (we try
to keep the "cognitive complexity" low when possible).


User Install / Deployment
=========================

Use the latest package for your Linux distro and hardware architecture;
all arch-specific packages should support at least the following:

* armhf/arm
* aarch64/arm64
* x86_64/amd64
* i686/x86


Software Stack and Tool Dependencies
====================================

* `python`_ - at least version 3.5
* `schedule`_ - scheduling engine
* `python-diskcache`_ - various cache types
* `python-daemon`_ - python daemon class
* `nanoservice`_ - python micro-messaging services
* `nanomsg-python`_ - python interface to nanomsg
* `nanomsg`_ - library for messaging protocols
* `ztcli-async`_ - python async client for zerotier API
* `ZeroTier`_ - network virtualization engine
* `tox`_ - needed for local testing

.. _Python: https://docs.python.org/3.5/index.html
.. _schedule: https://github.com/sarnold/schedule
.. _python-diskcache: https://github.com/grantjenks/python-diskcache
.. _python-daemon: https://github.com/sarnold/python-daemon
.. _nanoservice: https://github.com/freepn/nanoservice
.. _nanomsg-python: https://github.com/freepn/nanomsg-python
.. _nanomsg: https://github.com/nanomsg/nanomsg
.. _ztcli-async: https://github.com/freepn/ztcli-async
.. _ZeroTier: https://www.zerotier.com/
.. _tox: https://github.com/tox-dev/tox


Currently we also require a recent Linux kernel with ``iptables`` and
``iproute2`` installed (host requirements will be updated as we add
new platform support).


Versioning
==========

We use `SemVer`_ for versioning. For the versions available, see the
`releases on this repository`_.

.. _SemVer: http://semver.org/
.. _releases on this repository: https://github.com/freepn/fpnd/releases


Contributing
============

Please read `CONTRIBUTING.rst`_ for details on our code of conduct, and the
process for submitting pull requests to us.

.. _CONTRIBUTING.rst: https://github.com/freepn/fpnd/CONTRIBUTING.rst


Authors
=======

* **Stephen Arnold** - *Design, implementation, tests, and packaging* - `FreePN`_

.. _FreePN: https://github.com/freepn


License
=======

This project is licensed under the AGPL-3.0 License - see the
 `LICENSE file`_ for details.

.. _LICENSE file: https://github.com/freepn/fpnd/blob/master/LICENSE


Acknowledgments
===============

* Thanks to the ZeroTier devs for providing the network virtualization
  engine
* Thanks to all the upstream Python and other project authors so we
  don't have to re-invent fire...
