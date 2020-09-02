What is DNS anyway?
===================

A DNS (Domain Name Server) is a computer/device used to translate between
(human-readable) hostnames and their corresponding IP addresses (thus,
without one you would have to know *in advance* the IP address of every
machine you connect to).  Each time you type a name into your browser or
click a link, that action triggers a DNS lookup using your local settings
for DNS nameservers.

Inherent problems with the legacy DNS infrastructure include:

* legacy DNS is *not* encrypted, which leaves it open to snooping,
  hijacking, etc
* even though it supports TCP, it relies largely on UDP, which leaves
  it open to even more attack methods


DNS in its legacy form has been around as long as the Internet, but now
we have both Internet RFCs for encrypted DNS, and a growing population
of alternative DNS providers *using the newer encrypted protocols* that
respect and support online privacy needs.


Terms and Acronyms
==================

:DNSCrypt: This can mean the protocol or an implementation (eg, DNSCrypt-proxy)
:DNS over TLS: DoT is the primary encrypted DNS implementation (TCP over port 853)
:DNS over HTTPS: DoH is an alternate method using the standard (secure) web port
:stub resolver: a local non-recursive DNS "server" that uses DoT and/or DoH


Why you should care about your DNS lookups
==========================================

Mainly because DNS is abused by the same entities who collect your online
data and use it for their own (usually nefarious) purposes.  Your DNS
queries can even be (literally) hijacked before they ever reach the
internet.  These not-so-nice entities may include the following:

* many "public" DNS providers who log personal data
* your internet service and/or phone plan provider
* your hardware and/or OS vendors
* pretty much anyone on the internet who wants to sniff legacy DNS traffic


DNS handling in FreePN
=======================

There are two DNS modes for the fpnd network daemon:

* route your "normal" DNS requests with your web traffic (the default)
* drop all insecure outgoing DNS draffic if you are using a local
  secure stub resolver (optional)

Reasons why the first option is the default:

* we don't know (and will not assume) how your system is setup
* breaking DNS is a *bad* thing
* too many other packages you probably have installed already do this
  (mainly systemd and networkmanager)

So, *if* you want to take back a big chunk of your privacy and you're
using FreePN because you want more privacy, then you really should
consider running a secure stub resolver on your system.  Although both
systemd and networkmanager support DNSCrypt in some fashion, there are
known issues in the implementations, along with open bugs with DNS leaks.

There are many open source examples of DoT/DoH stub resolvers (just try
searching github for `DNSCrypt`).  The `DNS Privacy Project`_ has been
heavily invovled in the development of the `getdnsapi`_ package and the
associated stub resolver called `stubby`_.

The getdnsapi and stubby implementations are full-featured and work very
well, but going back to the github search above reveals many more.  If
you've ever looked at python code, you might enjoy looking at a very
clean/pure python implementation of a local `DoT forwarder`_ that uses
only the built-in python SSL functions.


.. _getdnsapi: https://getdnsapi.net/
.. _stubby: https://github.com/getdnsapi/stubby
.. _DoT forwarder: https://github.com/m3047/tcp_only_forwarder


Setup process for private DNS
=============================



More on the security of DNS
===========================

One broad category of DNS vulnerabilities applies to the inherent design
and architecture of the DNS system, both at the protocol-layer and the
system-layer.

* the `wikipedia article on DNS`_ lists some of the security issues with
  the DNS system
* one commonly exploited architectural vulnerability is `cache poisoning`_
* `DNSSEC`_ came about as a countermeasure against some of the weaknesses
  in the protocol
* `DNSCrypt`_ came about as a countermeasure against even more of those
  weaknesses
* `notes on DNS`_ from a developer that point out several system-level
  weaknesses

DNS is defined and described in numerous Internet RFCs. Modern RFCs now
include a "Security Considerations" section that discusses security
aspects related to the topic of the RFC.  Two of the latest DNSCrypt
protocol specifications can be found in `this DNSCrypt team github repo`_.


.. _wikipedia article on DNS: https://secure.wikimedia.org/wikipedia/en/wiki/Domain_Name_System#Security_issues
.. _cache poisoning: https://secure.wikimedia.org/wikipedia/en/wiki/DNS_cache_poisoning
.. _DNSSEC: https://secure.wikimedia.org/wikipedia/en/wiki/Domain_Name_System_Security_Extensions
.. _DNSCrypt: https://en.wikipedia.org/wiki/DNSCrypt
.. _notes on DNS: http://cr.yp.to/djbdns/notes.html
.. _this DNSCrypt team github repo: https://github.com/DNSCrypt/dnscrypt-protocol


Resources
=========

* the `DNS Privacy Project`_
* short article on `DNS and logging`_
* part of the above comes from `this stackexchange answer`_
* the `DNSCrypt-proxy wiki`_ has lists of DNS providers and other useful
  info (besides the software bits)


.. _DNS Privacy Project: https://dnsprivacy.org/
.. _DNS and logging: https://www.how-to-hide-ip.net/no-logs-dns-server-free-public/
.. _this stackexchange answer: https://security.stackexchange.com/questions/9470/listing-of-dns-vulnerabilities
.. _DNSCrypt-proxy wiki: https://github.com/DNSCrypt/dnscrypt-proxy/wiki
