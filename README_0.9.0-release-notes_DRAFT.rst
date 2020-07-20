=================================================
 Software Version Description for fpnd |Version|
=================================================

.. |Version| replace:: 0.9.0

:date: |date|, |time| PST8PDT
:author: SLA
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
* FreePN infrastructure/user node traffic is restricted to only node and network IDs (the minimum required for this stuff to actually work)

.. _FreePN: https://github.com/freepn
.. _ZeroTier: https://www.zerotier.com

Required / Optional Software
----------------------------

In addition to the existing (FOSS) package dependencies, there is one primary
package (and related repository on `github`_) for each of the following two
components:

* the FreePN network daemon - `fpnd`_
* the FreePN desktop UI (optional) - `freepn-gtk3-tray`_

.. _github: https://github.com/freepn
.. _fpnd: https://github.com/freepn/fpnd
.. _freepn-gtk3-tray: https://github.com/freepn/freepn-gtk3-tray


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


Build Instructions
------------------


Data integrity
--------------

checks for the executable object code and source code

Dependencies
------------

any files needed to install, build, operate, and maintain the software

Known Issues
------------

Resolved Issues
---------------


Full Change History
===================

Since there has been no prior Software Version Description published for this
software, this section contains the complete change history (see the git logs
for the detailed source code changes).


.. raw:: pdf

    PageBreak

.. include:: changelog.rst

