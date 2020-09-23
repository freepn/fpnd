====================================
 DNS-related Configuration Examples
====================================

The fpnd_ package installs several configuration examples to help make the
necessary privacy changes more straight-forward; note these are installed
by default on Ubuntu, but requires enabling the ``examples`` USE flag for
the fpnd ebuild on Gentoo.  Either way, they are installed to the "standard"
location under ``/usr/share/doc/<pkg_name-version>/examples``.

Most of these examples are usable as "drop-in" configuration files, while
others are more configuration snippets rather than a complete config file
(eg, the example ``stubby.yml`` contains only an alternate list of example
secure DNS providers in the proper ``yaml`` format).

Since newer versions of both ``systemd`` and ``NetworkManager`` still have
outstanding bugs in both split DNS and encrypted DNS handling, we need to
have multiple working solutions that avoid relying on these particular
feature implementations.

.. note:: This document assumes you have already read through the other
          DNS docs, mainly the `DNS Privacy`_ and `DNS Setup`_ docs. If
          something doesn't make sense, take a look at the other docs,
          and if you can't find the answer, please file a github issue.


.. _DNS Privacy: README_DNS_privacy.rst
.. _DNS Setup: README_DNS_setup.rst


Current config examples
-----------------------

* ``00-ext-dns.conf`` - drop-in external DNS config file for ``systemd-resolved``
* ``stubby.yml`` - list of tested upstream DNS providers, includes some experimental
  servers running DNS over TLS on port 443 (note this not DoH)
* ``dnsmasq.conf`` - drop-in dnsmasq config file for resolving local LAN DNS and
  forwarding external requests to stubby (tested using ``openrc`` with nfs mounts)
* ``fpnd.sudoers`` - the Ubuntu packages install this to the ``examples``
  directory, but it gets installed directly via USE flag on Gentoo


Example scenarios
-----------------

Scenario 1: configure ``systemd-resolved`` to use external DNS servers.

* This is the minimmum required configuration to enable ``route_dns`` in
  the ``fpnd.ini`` config file if all you have is your local router's
  private IP address for DNS services
* The default configuration uses Cloudflare_ DNS servers, but you can easily
  change it to another provider, as long as they still support plain-text
  DNS (eg, https://docs.nixnet.services/NixNet_DNS)
* This allows fpnd_ routing of plain-text DNS requests so they don't leak
  sideways BUT is still insecure and *not* private

To use the example config, whether you edit the DNS server addresses or
not, all you need to do is make a directory and drop the example file
in the directory you just created (note this will survive package upgrades
just fine).

First create the proper directory::

  $ sudo mkdir -p /etc/systemd/resolved.conf.d

Then copy the example config file; adjust the path as needed for Gentoo::

  $ sudo cp /usr/share/doc/python3-fpnd/examples/00-ext-dns.conf /etc/systemd/resolved.conf.d/

Finally restart ``systemd-resolved``::

  $ systemctl restart systemd-resolved.service

and verify your new DNS servers; they should appear near the top of the
following output under Global::

  $ systemd-resolve --status
  Global
           DNS Servers: 1.1.1.1
                        1.0.0.1
            DNSSEC NTA: 10.in-addr.arpa
                        16.172.in-addr.arpa
  (more output suppressed)


Scenario 2: adding specific/chosen upstream secure DNS resolvers to the
default ``stubby`` configuration.

* This implements your chosen DNS providers based on your privacy needs,
  eg, logging, ad-blocking, etc
* This also assumes you have already installed and setup ``stubby`` as
  documented in the `DNS Setup`_ doc

To use the example config snippet, you'll need to edit the default stubby
configuration file, carefully preserving the existing indentation (this
is very important for files using yaml_ syntax).  Copy the original file
to your $HOME directory first::

  $ cp /etc/stubby/stubby.yml ~/

Append the contents of the example snippet to the end of the copy you
just made::

  $ cat /usr/share/doc/python3-fpnd/examples/stubby.yml >> ~/stubby.yml

Open the stubby configuration file in your favorite editor::

  $ nano ~/stubby.yml

Search (Ctl-W in nano) for the section named ``upstream_recursive_servers``
and comment (or delete) each of the default server entries until only the
ones you want are left un-commented.  You can also back-up the original
file before you apply your changes::

  $ cp /etc/stubby/stubby.yml ~/stubby.yml.orig
  $ sudo cp ~/stubby.yml /etc/stubby/

Then restart the stubby service::

  $ sudo systemctl restart stubby.service

and verify the changes.  First try to resolve something and check the
``flag`` and ``SERVER`` lines::

  $ dig www.gentoo.org

  ; <<>> DiG 9.11.3-1ubuntu1.13-Ubuntu <<>> www.gentoo.org
  ;; global options: +cmd
  ;; Got answer:
  ;; ->>HEADER<<- opcode: QUERY, status: NOERROR, id: 42939
  ;; flags: qr rd ra ad; QUERY: 1, ANSWER: 2, AUTHORITY: 0, ADDITIONAL: 1

  ;; OPT PSEUDOSECTION:
  ; EDNS: version: 0, flags:; udp: 4096
  ; CLIENT-SUBNET: 0.0.0.0/0/0
  ;; QUESTION SECTION:
  ;www.gentoo.org.                        IN      A

  ;; ANSWER SECTION:
  www.gentoo.org.         43199   IN      CNAME   www-bytemark-v4v6.gentoo.org.
  www-bytemark-v4v6.gentoo.org. 43200 IN  A       89.16.167.134

  ;; Query time: 743 msec
  ;; SERVER: 127.0.0.1#53(127.0.0.1)
  ;; WHEN: Tue Sep 22 19:41:50 PDT 2020
  ;; MSG SIZE  rcvd: 151

For an external test, open a browser test your connection with `ipleak.net`_.

.. _ipleak.net: https://ipleak.net/


Scenario 3: configure stubby and dnsmasq for both secure DNS and local name
resolution (for local services *you* control, eg, shared network storage)
when not using ``systemd-resolved``.

* If you're using ``systemd-resolved`` then you should not need this,
  otherwise this is one way to handle it if you don't use systemd
* If you *are* using ``systemd-resolved`` and you need local LAN
  resources, then make sure the ``/etc/resolv.conf`` symlink points
  to ``../run/systemd/resolve/stub-resolv.conf`` and not one of the
  other systemd targets


.. _Cloudflare: https://www.bleepingcomputer.com/news/security/cloudflares-1111-dns-passes-privacy-audit-some-issues-found/
.. _yaml: https://en.wikipedia.org/wiki/YAML
