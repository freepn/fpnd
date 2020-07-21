=================================================
 Software Version Description for fpnd |Version|
=================================================

.. |Version| replace:: 0.9.0

:date: |date|, |time| PST8PDT
:author: Stephen L Arnold
:tags: system, prototype, version
:category: release
:slug: engineering_process
:summary: Software version/release description and full change history
:sw version: |Version|

.. |date| date::
.. |time| date:: %H:%M

.. contents:: Table of Contents

.. raw:: pdf

   PageBreak

FreePN Overview
===============


`FreePN`_ is a P2P implementation of a distributed virtual private network (dVPN)
based on ZeroTier to create a network "cloud" where each user is both a client
and an exit.  Peers are randomly connected on startup and reconnected as needed.

System Design
-------------

The FreePN network daemon uses `ZeroTier`_ virtual networks to provide enhanced
privacy, anonymity, and security over the Internet.  The current prototype design
supports these goals in the following ways; planned (future) features include more
granular user controls.

* each peer VPN link is a private ZeroTier network with its own IPv4 address space
* each network link allows only 2 hosts, and only the routed traffic (currently http/https)
* peer links are randomly assigned/reassigned as user nodes come and go
* FreePN infrastructure traffic is restricted to only node and network IDs (the minimum required for this stuff to actually work)

.. _FreePN: https://github.com/freepn
.. _ZeroTier: https://www.zerotier.com

Required / Optional Software
----------------------------

FreePN packages are available for Ubuntu and Gentoo using the live ebuilds in our
`python overlay`_ and a `PPA on Launchpad`_. The PPA sources can also be used
to build Debian packages, however, we don't (yet) support any "official" Debian
releases.

In addition to the existing (`FOSS`_) package dependencies, there is one primary
package (and related repository on `github`_) for each of the following two
components:

* the FreePN network daemon - `fpnd`_
* the FreePN desktop UI (optional) - `freepn-gtk3-tray`_

.. _FOSS: https://www.gnu.org/philosophy/floss-and-foss.en.html
.. _github: https://github.com/freepn
.. _fpnd: https://github.com/freepn/fpnd
.. _freepn-gtk3-tray: https://github.com/freepn/freepn-gtk3-tray


Prerequisites
-------------

A supported linux distribution, mainly something that uses `.ebuilds`
(eg, Gentoo or funtoo) or a supported Ubuntu series, currently xenial
16.0.4 LTS, bionic 18.0.4 LTS, or focal 20.0.4 LTS (see the above
`PPA on Launchpad`_).  Note you can also use the focal PPA series on
the latest kali linux.

Packages and Source Code
------------------------

Released packages come in three different formats, which are verified in at
least one or more places.

For supported Linux distributions:

* Ubuntu xenial, bionic, focal
* Kali rolling (other ubuntu derivatives should also work)

  + use the `Launchpad PPA`_

* Gentoo (funtoo, Sabayon)

  + use the `python-overlay`_

For other distributions:

* debian-ish

  + use the `Launchpad PPA`_ (source build)

* Other:

  + use the latest `fpnd source release on github`_


.. _Launchpad PPA: https://launchpad.net/~nerdboy/+archive/ubuntu/embedded
.. _python-overlay: https://github.com/freepn/python-overlay
.. _fpnd source release on github: https://github.com/freepn/fpnd/releases


Install Instructions
--------------------

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
this PPA to your system", eg, ``41113ed57774ed19`` for `Embedded device ppa`_.


.. _Embedded device ppa: https://launchpad.net/~nerdboy/+archive/ubuntu/embedded

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

  # emaint sync --repo python-overlay

Once the overlay is synced, install the daemon and/or UI package::

  $ sudo emerge fpnd

Or::

  $ sudo emerge freepn-gtk3-tray


.. note:: In either case, installing the UI package will pull the daemon package
          as one of the dependencies, so you do not need to manually install both
          packages (ie, choose one or the other).

Portage notes
-------------

* almost nothing in the overlay is keyworded stable yet; use your preferred
  method to accept ``~`` packages
* depending on your license settings, you may need to allow the new zerotier
  license (BSL-1.1) in your make.conf file
* ``freepn-gtk3-tray`` requires an XDG-compliant desktop with policykit installed,
  so you'll need to enable the "polkit" USE flag on ``net-misc/fpnd``


.. _Portage: https://wiki.gentoo.org/wiki/Portage

Build Instructions
------------------



Data integrity
--------------

The canonical source code repositories are maintained on `github`_ and verified
by both github keys (for pull requests) and developer keys are used to sign
releases (tags and ``tar.gz`` archives).  Note this also includes the
``.ebuild`` packages in the `python-overlay`_.

For the ``.deb`` package format:

* all ``.deb`` "source" packages are signed with the developer's PPA key prior
  to uploading to the PPA builder
* signatures are verified using the package manager via the ubuntu key server


Dependencies
------------

Core dependencies for the FreePN network daemon are shown below.  Dependency
resolution is handled by the respective package managers and test tools. The
run-time requirements also include a recent Linux kernel with ``bash``,
``iptables``, and ``iproute2`` installed.

* `python`_ - at least version 3.5
* `appdirs`_ - standardized app directories
* `datrie`_ - python interface to libdatrie
* `schedule`_ - python scheduling engine
* `python-diskcache`_ - persistent cache types
* `python-daemon`_ - python daemon class
* `nanoservice`_ - python micro-messaging services
* `nanomsg-python`_ - python interface to nanomsg
* `nanomsg`_ - library for messaging protocols
* `ztcli-async`_ - python async client for zerotier API
* `ZeroTier`_ - network virtualization engine
* `tox`_ and `pytest`_- optional; needed for local testing

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


Known Issues
------------


Resolved Issues
---------------



.. raw:: pdf

    PageBreak


Full Change History
===================

Since there has been no prior Software Version Description published for this
software, this section should contain the `complete change history`_ (see the
git logs for the detailed source code changes).  Sadly github does not render
included ``.rst`` documents.

.. _complete change history: changelog.rst


.. include:: changelog.rst

