=================================================
 Software Version Description for fpnd |Version|
=================================================

.. |Version| replace:: 0.9.3

:date: |date|, |time| PST8PDT
:author: Stephen L Arnold
:tags: system, prototype, version
:category: release
:slug: engineering_process
:summary: Software version/release description and full change history
:asset name: fpnd
:software version: |Version|

.. |date| date::
.. |time| date:: %H:%M

.. contents:: Table of Contents

.. raw:: pdf

   PageBreak

1.0 - Identification and Overview
=================================


The FreePN_ network daemon (fpnd) is a P2P implementation of a distributed virtual
private network (dVPN) that creates an anonymous "cloud" of peers where each
peer is both a client and an exit.  Peers are randomly connected on startup and
reconnected to new (random) peers as needed.

1.1 - System Design
-------------------

The FreePN network daemon uses ZeroTier_ virtual networks to provide enhanced user
privacy, anonymity, and security when accessing the Internet.  The current prototype
design supports these goals in the following ways; planned (future) features include
more granular user controls.

* each peer VPN link is a private ZeroTier network with its own IPv4 address space
* each network link allows only 2 hosts, and only the routed traffic (currently http/https/dns)
* peer links are randomly assigned/reassigned by the network controller as user nodes come and go
* FreePN infrastructure traffic is restricted to only node and network IDs (the minimum required for this stuff to actually work)

.. _FreePN: https://github.com/freepn


1.2 - Required / Optional Software
----------------------------------

FreePN packages are available for Gentoo and Ubuntu using the ebuilds in the
`python-overlay`_ or the ``.deb`` packages hosted on the Embedded device
`PPA on Launchpad`_. The PPA sources can also be used to build Debian packages,
however, we don't (yet) support any "official" Debian releases.

In addition to the existing (FOSS_) package dependencies, there is one primary
package (and related repository on github_) for each of the following two
components:

* the FreePN network daemon - fpnd_
* the FreePN desktop UI (optional) - freepn-gtk3-tray_

The required Linux kernel modules include:

* xt_MASQUERADE, xt_nat, xt_tcpudp, xt_mark
* nf_nat, nf_conntrack, nf_defrag_ipv4
* iptable_filter, iptable_nat, iptable_mangle, bpfilter
* ip6_tables, ip6table_mangle, ip6table_filter, ip6table_nat

The required outgoing network ports for the FreePN user node daemon include:

* allow port 9993/udp (both IPv4 and IPv6 for zerotier)
* allow port 8443/tcp (for fpnd infra messages)
* allow ports 53/udp and 53/tcp (if *not* using encrypted dns)
* allow port 853/tcp (if using encrypted dns)
* allow ports 80/tcp and 443/tcp

.. note:: When using encrypted dns *and* with ``private_dns_only`` set to
          ``True`` local dns queries are only allowed to localhost (but peer
          dns traffic is still routed).

.. _FOSS: https://www.gnu.org/philosophy/floss-and-foss.en.html
.. _github: https://github.com/freepn
.. _fpnd: https://github.com/freepn/fpnd
.. _freepn-gtk3-tray: https://github.com/freepn/freepn-gtk3-tray


2.0 - Referenced Documents
==========================

* ZeroTier Manual - https://www.zerotier.com/manual/
* DI-IPSC-81442 - Software Version Description (SVD) Data Item Description (DID)


3.0 - Version Description
=========================

Prerequisites:

A supported linux distribution, mainly something that uses `.ebuilds`
(eg, Gentoo or funtoo) or a supported Ubuntu series, currently bionic
18.0.4 LTS, or focal 20.0.4 LTS (see the above`PPA on Launchpad`_).
Note you can also use the focal PPA series on the latest kali images,
however, the fpnd.service is broken against the latest systemd upgrade
to 264 or higher (and there is no fix yet).

3.1 - Packages and Source Code
------------------------------

Released packages come in three different formats, which are verified in at
least one or more places.

For supported Linux distributions:

* Ubuntu bionic, focal
* Kali (other ubuntu derivatives should also work)

  + use the `PPA on Launchpad`_

* Gentoo (funtoo, Sabayon)

  + use the `python-overlay`_

For other distributions:

* debian-ish

  + use the `PPA on Launchpad`_ (source build)

* Other:

  + use the latest `fpnd source release on github`_


.. _PPA on Launchpad: https://launchpad.net/~nerdboy/+archive/ubuntu/embedded
.. _python-overlay: https://github.com/freepn/python-overlay
.. _fpnd source release on github: https://github.com/freepn/fpnd/releases


3.2 - Install Instructions
--------------------------

Before you can install any Freepn packages, you'll need to add the required
package repository or overlay.

For all ubuntu series, make sure you have the ``gpg`` and ``add-apt-repository``
commands installed and then add the PPA:

::

  $ sudo apt-get install -y software-properties-common
  $ sudo add-apt-repository -y -s ppa:nerdboy/embedded

If you get a key error you will also need to manually import the PPA
signing key like so:

::

  $ sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys <PPA_KEY>

where <PPA_KEY> is the key shown in the launchpad PPA page under "Adding
this PPA to your system", eg, ``41113ed57774ed19`` for the Embedded device PPA.


On kali you will need to edit the file created under ``/etc/apt/sources.list.d``
for the PPA and change the series name to ``focal``, then run the above
``apt-key`` command, and finally a manual update.

Then install ``fpnd`` (for console only) or ``freepn-gtk3-indicator`` for
the desktop GUI:

::

  $ sudo apt-get install python3-fpnd

Or::

  $ sudo apt-get install freepn-gtk3-indicator

For Gentoo or derivatives based on `Portage`_, first install the portage overlay.

Create a repos.conf file for the overlay and place the file in the
``/etc/portage/repos.conf`` directory.  Run::

  $ sudo nano -w /etc/portage/repos.conf/python-overlay.conf

and add the following content to the new file::

  [python-overlay]

  # Various python ebuilds for FreePN
  # Maintainer: nerdboy (nerdboy@gentoo.org)

  location = /var/db/repos/python-overlay
  sync-type = git
  sync-uri = https://github.com/freepn/python-overlay.git
  priority = 50
  auto-sync = yes

Adjust the path in the ``location`` field as needed, then save and exit nano.

Run the following command to sync the repo::

  $ sudo emaint sync --repo python-overlay

Once the overlay is synced, install the daemon and/or UI package::

  $ sudo emerge fpnd

Or::

  $ sudo emerge freepn-gtk3-tray


.. note:: In either case, installing the UI package will pull the daemon package
          as one of the dependencies, so you do not need to manually install both
          packages (ie, choose one or the other).

Portage notes:

* almost nothing in the overlay is keyworded stable yet; use your preferred
  method to accept ``~`` packages
* depending on your license settings, you may need to allow the new zerotier
  license (BSL-1.1) in your make.conf file
* ``freepn-gtk3-tray`` requires an XDG-compliant desktop with policykit installed,
  so you'll need to enable the "polkit" USE flag on ``net-misc/fpnd``


.. _Portage: https://wiki.gentoo.org/wiki/Portage

3.3 - Build Instructions
------------------------

For Gentoo and related derivatives, all packages are built from source by design,
while ``.deb`` packages are built automatically by the PPA tools.

The Gentoo ebuilds generally enable only the package tests (without any extras
like code coverage, linting, etc) so you'll need to manually install those if
desired. You can find the additional test packages in the package-specific
requirements*.txt files (for python packages) and ``.travis.yml`` files (and
sometimes as comments in the ebuilds).  You can start by installing ``fpnd``
with ``test`` in both FEATURES and USE.

If you're on Ubuntu you can make a local build directory and ``cd`` into it,
then issue the following commands to get started::

  $ sudo apt-get build-dep python3-fpnd
  $ sudo apt-get install tox
  $ git clone https://github.com/freepn/fpnd

Using the Debian developer/packaging tools is beyond the scope of this document.

3.4 - Data integrity
--------------------

The canonical source code repositories are maintained on github_ and verified
by both github keys (for pull requests) and developer keys; the latter are used
to sign releases (both tags and ``tar.gz`` archives).  Note this also includes
the ``.ebuild`` packages in the `python-overlay`_.

For the ``.deb`` package format:

* all ``.deb`` "source" packages are signed with the developer's PPA key prior
  to uploading to the PPA builder
* signatures are verified using the package manager via the ubuntu key server


3.5 - Dependencies
------------------

Core dependencies for the FreePN network daemon are shown below.  Dependency
resolution is handled by the respective package managers and test tools. The
run-time requirements also include a recent Linux kernel with ``bash``,
``iptables`` (legacy), and ``iproute2`` installed.

* python_ - at least version 3.6
* appdirs_ - standardized app directories
* datrie_ - python interface to libdatrie
* libdatrie_ - a Double-Array Trie library
* schedule_ - python scheduling engine
* python-diskcache_ - persistent cache types
* python-daemon_ - python daemon class
* nanoservice_ - python micro-messaging services
* nanomsg-python_ - python interface to nanomsg
* nanomsg_ - library for messaging protocols
* ztcli-async_ - python async client for zerotier API
* ZeroTier_ - network virtualization engine
* stunnel_ - TLS encrypted proxy (uses openssl)
* tox_ and pytest_- optional; needed for local testing

.. _python: https://docs.python.org/3.5/index.html
.. _appdirs: https://github.com/ActiveState/appdirs
.. _datrie: https://github.com/pytries/datrie
.. _libdatrie: https://github.com/tlwg/libdatrie
.. _schedule: https://github.com/freepn/schedule
.. _python-diskcache: https://github.com/grantjenks/python-diskcache
.. _python-daemon: https://github.com/freepn/python-daemon
.. _nanoservice: https://github.com/freepn/nanoservice
.. _nanomsg-python: https://github.com/freepn/nanomsg-python
.. _nanomsg: https://github.com/nanomsg/nanomsg
.. _ztcli-async: https://github.com/freepn/ztcli-async
.. _ZeroTier: https://www.zerotier.com/
.. _stunnel: https://www.stunnel.org/
.. _tox: https://github.com/tox-dev/tox
.. _pytest: https://github.com/pytest-dev/pytest


3.6 - Known Issues
------------------

* Erratic service file behavior with systemd >= 246

This essentially breaks correct shutdown and associated cleanup functions
(no fixes yet) on ubuntu groovy and kali.

* avahi-autoipd link-local conflicts with zerotier interfaces

  - avahi-daemon.conf requires interface whitelisting to ignore vpn interfaces

These are both open "watch items" (see `issue 39`_ and `issue 67`_) for Linux hosts
running the avahi daemon.  Using autoipd is incompatible with both fpnd and
ZeroTier (see the first github issue for details) so you must disable the autoipd
daemon before running fpnd. The second issue addresses the default avahi config
listening on *all* the interfaces it finds and recommends options to address
both issues.

* missing kernel module(s) cause net script failures

This is also an open "watch item" issue (see `issue 30`_) and is mainly a potential
issue with user-configured/custom kernels; currently the standard kernel packages
on Ubuntu and Kali have the required modules enabled (on Gentoo this is handled
by checking for the required modules when building the package and issuing a
warning to the user if necessary).

.. _issue 39: https://github.com/freepn/fpnd/issues/39
.. _issue 67: https://github.com/freepn/fpnd/issues/67
.. _issue 30: https://github.com/freepn/fpnd/issues/30


3.7 - Resolved Issues
---------------------

See the `closed issues list`_ on github for details.


.. _closed issues list: https://github.com/freepn/fpnd/issues?q=is%3Aissue+is%3Aclosed


.. raw:: pdf

    PageBreak


Appendix A - Full Change History
================================

Since there has been no prior Software Version Description published for this
software, this section should contain the `complete change history`_ (see the
git logs for the detailed source code changes).  Sadly github does not render
included ``.rst`` documents.

.. _complete change history: changelog.rst


.. note:: You can build a (complete) PDF version of this document using the
          ``rst2pdf`` tool.  After cloning this repository, cd into the top
          level directory and run the following command::

            $ rst2pdf README_0.9.0-release-notes.rst -o README_0.9.0-release-notes.pdf


.. include:: changelog.rst
