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


What FreePN is (and is not)
===========================

FreePN is a set of open source (see `FLOSS`_ definition) privacy tools for an
improved online `user experience`_ (and yes, there's even `an ISO standard`_
for that).  The current prototype implementation is mainly this repository.

Yes, it's "free" (as in FLOSS) and it's sort of like a VPN.  FreePN is
essentially an anonymizing p2p internet proxy using a "virtual private
cloud" of peers, and the ``fpnd`` tools are the automation layer on top
of the ZeroTier network virtualization engine that makes it happen.

Freepn is *not* a full VPN solution (eg, openvpn or vpnc) and does not
require setup of any pre-shared keys or certs.  Traffic over Freepn
network links is always encrypted, however, since each network link is
independent, the traffic must be decrypted as it passes through each
peer host.  When running in "peer" mode, each peer is assumed to be an
untrusted host; when running in "adhoc" mode, the hosts can be assumed
to be trusted hosts (as they belong to the user).

.. _FLOSS: https://www.gnu.org/philosophy/floss-and-foss.en.html
.. _user experience: https://en.wikipedia.org/wiki/User_experience
.. _an ISO standard: https://en.wikipedia.org/wiki/ISO_9241#ISO_9241-210


Prototype release targets
-------------------------

The Alpha release target is "peer mode", which puts the above cloud of
peers between you and the internet.  Each peer link provides an isolated,
private, and encrypted path to the internet, with a new/random peer for
each session.

The pre-Alpha release target (starting with 0.7.2.p6) is "adhoc mode",
which addresses a more specific use case for routing (your own) remote
traffic through (your own) trusted internet connection.  In (older) jargon
this may have been called a `kluge`_ or involve some `ad-hockery`_ (or could
even be a `Rube-Goldberg Device`_) but in today's "agile" world this is
called a feature!


.. note:: Adhoc mode requires a one-time `manual setup`_ of your devices and
          a ZeroTier network; be sure and stay tuned for the (fully automated)
          Alpha release!


.. _kluge: https://web.archive.org/web/20130827121341/http://cosman246.com/jargon.html#kluge
.. _ad-hockery: https://web.archive.org/web/20130827121341/http://cosman246.com/jargon.html#ad-hockery
.. _Rube-Goldberg Device: https://en.wikipedia.org/wiki/Rube_Goldberg_machine
.. _manual setup: README_adhoc-mode.rst


What does it do?
----------------

Currently all web traffic (ie, ports 80 and 443) is routed over virtual
network links to an "exit" peer (although other ports may be added/dropped
in future releases).  In adhoc mode, the default network rules allow all
traffic, however, only the ports above are automatically routed over FPN
network links.  In peer mode *no* other TCP/UDP traffic is allowed between
peers *except* the routed ports above.

The general advice is: **do** use ``https`` for everything (*especially* anything
sensitive/private) and **don't** use ``http`` for anything.  At all.  Period.

* adhoc mode - *you* own the network link and the peers
* peer mode - *you* only control your own host (peers are random,
  networks are auto-assigned and configured)


Note about release tags
-----------------------

* current "adhoc mode" release is ``0.7.3``
* any updates to adhoc mode will stay in the ``0.7.x`` series
* peer mode development continues using ``0.8.x`` for pre-release
* current Alpha release target for peer mode is ``0.9.0``


Getting Started
===============

Adhoc mode is now enabled in the current release; at this point we only target
Linux with at least `Python`_ 3.5.  Packages are available for Ubuntu and
Gentoo using the live ebuild in our `python overlay`_ and a `PPA on Launchpad`_.
The PPA sources can also be used to build Debian packages, however, we
don't (yet) support any "official" Debian releases.


.. _PPA on Launchpad: https://launchpad.net/~nerdboy/+archive/ubuntu/embedded
.. _python overlay: https://github.com/freepn/python-overlay


.. note:: This stack depends on both Python and nanomsg and the Ubuntu
          releases are just enough out of sync with Debian, so the PPA
          binaries are not usable directly on any specific Debian version
          (so must be rebuilt from source).


Prerequisites
-------------

A supported linux distribution, mainly something that uses `.ebuilds`
(eg, Gentoo or funtoo) or a supported Ubuntu series, currently bionic
18.0.4 LTS, and focal 20.0.4 LTS (see the above `PPA on Launchpad`_).
Note you can also use the focal PPA series on the latest kali linux.

For all ubuntu series, make sure you have the ``gpg`` and ``add-apt-repository``
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

On kali you will need to edit the file created under ``/etc/apt/sources.list.d``
for the PPA and change the series name to ``focal``.

Finally, install fpnd:

::

  $ sudo apt-get install python3-fpnd


Since the main user daemon ``fpnd.py`` needs to manipulate networks and
routes, it currently must run under either systemd or openrc as a daemon service,
which means you will need root (or sudo) priveleges to start and stop the init
script or service files.  That said, we DO NOT recommend enabling the service
to run on boot (so it *does not* need to be enabled this way).  We DO
recommend using start|stop as needed so it only runs when you want it to.

The fpnd tools require access to the following privileged interfaces on
each peer host:

* zerotier API via access token (requires tun/tap on Linux)
* sysctl, kernel routing, and iptables/netfilter interfaces

When running under systemd we can take advantage of some of the isolation
features and allow the daemon to run as a non-priveleged user (``fpnd``)
using linux capabilities to gain the required priveleges.  The alternative
option of running under openrc requires running with full root priveleges.

Please choose one of the following user config options for starting and
stopping the ``fpnd`` Systemd service:

* use ``sudo systemctl start|stop fpnd`` with your current setup
* install the fpnd.sudoers file to allow ``sudo`` with no password prompt
  for only the above ``fpnd`` service commands
* install the polkit rule file ``org.freedesktop.systemd1.pkla`` for polkit
  versions 0.105 or lower
* install the polkit rule file ``55-fpnd-systemd.rules`` for newer polkit versions

The available options depend on whether you use systemd, openrc, or something else:

1. Using systemd: sudo or polkit rules
2. Using openrc: sudo or polkit/pkexec
3. Anything else: sudo

Use one of the following:

* to use your current ``sudo`` config as-is, do nothing
* to use the sudoers file, rename it just ``fpnd`` and drop it in the
  ``/etc/sudoers.d/`` directory (perms must be 0440 root:root)
* to use the older polkit rule, drop the file in the directory
  ``/etc/polkit-1/localauthority/50-local.d/``
* to use the newer polkit rule, drop the file in the directory
  ``/etc/polkit-1/rules.d/``

Note to use any other method besides "do nothing" you must first add your
user to the ``fpnd`` group for the required priveleges, eg:
``usermod -aG fpnd <user>``

If you are running Openrc as your init system, we have the following
config options for running the Openrc init script:

* use the usual ``sudo`` prefix and run the init script
* install the fpnd.sudoers file to allow ``sudo`` with no password prompt
  for only the openrc ``fpnd`` service commands
* use a polkit rule to allow the ``/sbin/openrc`` command without a password
  using ``pkexec``

The last option above is somewhat klunky but is more restrictive than using
the ``sudoers`` file with ``NOPASSWD``.  If you want to use this rule, then
drop the rules file ``55-fpnd-openrc.rules`` into ``/etc/polkit-1/rules.d/``
and use the following command / args as your normal user::

  $ pkexec /sbin/openrc -s fpnd start|stop

Using the sudo rules instead of ``pkexec``::

  $ sudo openrc -s fpnd start


Dev Install
-----------

As long as you have git and at least Python 3.5, then the "easy" dev
install is to clone this repository and install `tox`_ (optional) and the
`nanomsg`_ and `datrie`_ libraries (required).

`Install the overlay`_ and do the usual install dance; add ``FEATURES=test``
if you want the pytest deps::

  # FEATURES=test emerge net-misc/fpnd

or on Ubuntu::

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

See the `Prerequisites`_ above.


Software Stack and Tool Dependencies
====================================

* `python`_ - at least version 3.5
* `appdirs`_ - standardized app directories
* `datrie`_ - python interface to libdatrie
* `schedule`_ - python scheduling engine
* `python-diskcache`_ - various cache types
* `python-daemon`_ - python daemon class
* `nanoservice`_ - python micro-messaging services
* `nanomsg-python`_ - python interface to nanomsg
* `nanomsg`_ - library for messaging protocols
* `ztcli-async`_ - python async client for zerotier API
* `ZeroTier`_ - network virtualization engine
* `tox`_ and `pytest`_- needed for local testing

.. _Python: https://docs.python.org/3.5/index.html
.. _appdirs: https://github.com/ActiveState/appdirs
.. _datrie: https://github.com/pytries/datrie
.. _schedule: https://github.com/freepn/schedule
.. _python-diskcache: https://github.com/grantjenks/python-diskcache
.. _python-daemon: https://github.com/freepn/python-daemon
.. _nanoservice: https://github.com/freepn/nanoservice
.. _nanomsg-python: https://github.com/freepn/nanomsg-python
.. _nanomsg: https://github.com/nanomsg/nanomsg
.. _ztcli-async: https://github.com/freepn/ztcli-async
.. _ZeroTier: https://www.zerotier.com/
.. _tox: https://github.com/tox-dev/tox
.. _pytest: https://github.com/pytest-dev/pytest


Currently we also require a recent Linux kernel with ``iptables`` and
``iproute2`` installed (host requirements will be updated as we add
new platform support).

For the required kernel support, your kernel module listing should include
something like this::

    $ sudo lsmod

    iptable_filter         16384  1
    iptable_nat            16384  1
    xt_nat                 16384  10
    nf_nat                 36864  2 xt_nat,iptable_nat
    nf_conntrack          102400  2 xt_nat,nf_nat
    nf_defrag_ipv6         20480  1 nf_conntrack
    nf_defrag_ipv4         16384  1 nf_conntrack
    libcrc32c              16384  2 nf_conntrack,nf_nat
    iptable_mangle         16384  1
    xt_mark                16384  6
    xt_tcpudp              16384  34
    bpfilter               24576  0
    ip_tables              24576  3 iptable_mangle,iptable_filter,iptable_nat
    x_tables               24576  6 xt_nat,iptable_mangle,ip_tables,iptable_filter,xt_mark,xt_tcpudp
    tun                    45056  0


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
