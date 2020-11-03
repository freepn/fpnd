Setup process for adhoc mode
============================

* requires 2 (two) Linux hosts (Gentoo or Ubuntu bionic/focal LTS)
* one "mobile" host and one "exit" host

  + "mobile" host can be any Linux desktop (pkgs for arm, arm64, x86, x86_64)
  + "exit" host can be any (Linux) hardware/VM with decent gigabit ethernet


Note about network configuration
--------------------------------

The requirement for two hosts (as well as the steps that follow) is based
on the smallest possible private subnet, with only two free IPv4 addresses.
In `CIDR notation`_ this is a ``/30`` subnet, but you are free to add more
of your own hosts and use a different config.  But *don't worry*, this is
simple in python. Try this at a python prompt:

::

  Python 3.6.10 (default, Dec  6 2019, 21:16:24)
  [GCC 9.2.0] on linux
  Type "help", "copyright", "credits" or "license" for more information.
  >>> import ipaddress
  >>> netobj = ipaddress.ip_network('172.16.0.241/30', strict=False)
  >>> netobj
  IPv4Network('172.16.0.240/30')
  >>> list(netobj)
  [IPv4Address('172.16.0.240'), IPv4Address('172.16.0.241'), IPv4Address('172.16.0.242'),
      IPv4Address('172.16.0.243')]
  >>> list(netobj.hosts())
  [IPv4Address('172.16.0.241'), IPv4Address('172.16.0.242')]


The above demonstrates how Python "calculates" IPv4 subnets for the
(very) private 2-host network configured below.  Since every IPv4 subnet
needs both a network address and a broadcast address, this leaves only
two addresses for actual host addresses on the network.  If you want more
hosts on your adhoc network, simply use a larger subnet (eg, a ``/28``).
Keep in mind each mobile node on your adhoc network will all use the
same exit node; also note that a ``/28`` allows 14 host addresses:

::

  >>> netobj = ipaddress.ip_network('172.16.0.30/28', strict=False)
  >>> list(netobj)
  [IPv4Address('172.16.0.16'), IPv4Address('172.16.0.17'), IPv4Address('172.16.0.18'),
      IPv4Address('172.16.0.19'), IPv4Address('172.16.0.20'), IPv4Address('172.16.0.21'),
      IPv4Address('172.16.0.22'), IPv4Address('172.16.0.23'), IPv4Address('172.16.0.24'),
      IPv4Address('172.16.0.25'), IPv4Address('172.16.0.26'), IPv4Address('172.16.0.27'),
      IPv4Address('172.16.0.28'), IPv4Address('172.16.0.29'), IPv4Address('172.16.0.30'),
      IPv4Address('172.16.0.31')]
  >>> len(list(netobj.hosts()))
  14


.. _CIDR notation: https://en.wikipedia.org/wiki/CIDR_notation


Configuration steps
-------------------

The following steps are for a "personal" network (single "mobile" node).

* install fpnd, set adhoc mode (both hosts)

  + gentoo: `add the overlay`_ and ``emerge fpnd`` (``USE="adhoc"`` should be enabled by default)
  + ubuntu: `add the PPA`_ and ``apt-get install fpnd``

    - edit ``/etc/fpnd.ini`` and change ``mode = peer`` to ``mode = adhoc``

* stop ``fpnd`` and start/restart ``zerotier|zerotier-one`` (both hosts)
* get the zerotier node ID from each host

  + run ``sudo zerotier-cli info``
  + output should look something like:

    - ``200 info <YOUR_ID> 1.4.6 ONLINE``
    - where ``<YOUR_ID>`` is a 10-digit hex string
    - it may show ``OFFLINE`` after the first startup, this is normal

  + have each id ready for the next step

* create/configure a network on `my.zerotier.com`_

  + login with Google or make an account
  + select the **Free** option (read the terms of service)
  + click on the *networks* menu item and create a network
  + click on the network you just created
  + go to the **Members** section

    - in the field below *Manually Add Member*:

      * paste the **exit** node ID and click Add New Member
      * wait for the node ID to appear and give it a name/desc
      * repeat the above steps with your **mobile** node ID


.. _add the PPA: https://github.com/freepn/fpnd/blob/master/README.rst#getting-started
.. _add the overlay: https://github.com/freepn/freepn-overlay/blob/master/README.rst
.. _my.zerotier.com: https://my.zerotier.com/

.. note:: The above network Members will continue to show **Never** in the
          Last Seen column until after the final steps below are complete
          and fpnd is running on each node.


* configure the network for maximum privacy

  + scroll up to the Settings section
  + confirm Access Control is set to PRIVATE
  + scroll down to the Advanced section
  + under Managed Routes

    - delete the existing route by clicking the trashcan
    - under Add Routes

      * enter ``172.16.0.240/30`` in the Destination, click Submit
      * wait, then enter ``0.0.0.0/0`` in the Destination. **and**
      * enter ``172.16.0.241`` in (Via) and click submit

  + under IPv4 Auto-Assign

    - disable auto-assign by **un-checking** the box

  + under IPv6 Auto-Assign

    - make sure all three options are *disabled*

  + go back to the Members section under Managed IPs

    - for the **exit** node, enter ``172.16.0.241`` in the address field and click
      the **+** sign
    - for the **source** node, enter ``172.16.0.242`` in the address field and click
      the **+** sign


On each adhoc node:

* get the network ID of the network you just created (at the very top of the page)
* edit the ``helper_funcs.py`` source file

  - near the top of the source file, look for the NODE_SETTINGS dictionary:

.. code:: python

  NODE_SETTINGS = {
      u'max_cache_age': 60,  # maximum cache age in seconds
      u'use_localhost': False,  # messaging interface to use
      u'node_role': None,  # role this node will run as
      u'ctlr_list': ['edf70dc89a'],  # list of fpn controller nodes
      u'moon_list': ['9790eaaea1'],  # list of fpn moons to orbiit
      u'home_dir': None,
      u'debug': False,
      u'node_runner': 'nodestate.py',
      u'mode': 'peer',
      u'use_exitnode': [],  # edit to populate with ID: ['exitnode']
      u'nwid': None  # edit to populate with network ID
  }

* find the above file using Ubuntu pkg tools:

::

  $ dpkg -L python3-fpnd | grep helper_funcs


* find the above file using Gentoo pkg tools:

::

  $ qlist fpnd | grep helper_funcs


Using a text editor (not a word processor) carefully edit the following
item:

* ``u'nwid': None`` => replace ``None`` with the network ID string in single quotes

The last two items in ``NODE_SETTINGS`` should look something like this:

.. code:: python

    u'use_exitnode': [],  # edit to populate with ID: ['exitnode']
    u'nwid': 'b6079f73c63cea42'  # edit to populate with network ID


.. note:: Your 16-digit network ID will be different than the example shown
          above.  Also note the comment does *not* apply to the current
          0.7.2p6 release.

Once all of the above steps are complete, start the fpnd service on each
node.

On Gentoo with openrc:

::

  # /etc/init.d/fpnd start


On Gentoo or Ubuntu with systemd:

::

  # service fpnd start


Troubleshooting adhoc mode
==========================

Once configured as above, everything else is automated so as long as the
required commands are available the main thing you can do from the user
end is stop/start the service and check the log file (and since debug is
enabled there should be plenty of log output :)

.. note:: If you're already running a local firewall (eg, iptables or ufw)
          you should make sure that port ``9993/UDP`` is allowed out.


For adhoc mode, you should *not* use the ``restart`` command; the fpnd
service does a (network) ``join`` command on startup and the corresponding
``leave`` command on shutdown and the network needs a few seconds to process
the latter for a clean startup.

The ``fpnd`` log file is written to ``/var/log/fpnd.log`` and will show
the status of the (internal) zerotier API calls and processing of network
scripts, etc.

Use the above init/service commands via sudo, and wait at least 5-10
seconds between ``stop`` and ``start``:

::

  $ sudo service fpnd stop  # pause 5+ sec
  $ tail -f /var/log/fpnd.log
  $ sudo service fpnd start
  $ tail -f /var/log/fpnd.log

Verify the pre-shutdown commands after ``stop`` then after startup look
for ``Success`` for both the initial setup command and the gateway check.
You should see something like this after startup on both peers:

::

  INFO [13086] Running job Job(interval=1, unit=seconds, do=run_net_cmd,
        args=(['/usr/lib/fpnd/fpn1-setup.sh'],), kwargs={})
  INFO [13086] net cmd fpn1-setup.sh result: Success
  DEBUG [13086] JOB: Job(interval=1, unit=seconds, do=run_net_cmd,
        args=(['/usr/lib/fpnd/fpn1-setup.sh'],), kwargs={})
        claims success: (True, b'Success\n', 0)


Note the lines above are truncated/wrapped for readability ;)

Lastly, you can verify the command results using the ``iptables`` command.

Once you see the above log message on the "exit" node, run the following
command from a terminal prompt::

  $ sudo iptables -L -t nat

and check the ``POSTROUTING`` chain; you should see one ``SNAT`` rule:

::

  Chain POSTROUTING (policy ACCEPT)
  target     prot opt source               destination
  SNAT       all  --  172.16.0.240/28      anywhere      to:<exit IP>


Similarly on the "mobile" node, run the same command::

  $ sudo iptables -L -t nat

and check the ``POSTROUTING`` chain; you should see two ``SNAT`` rules
for http/https:

::

  Chain POSTROUTING (policy ACCEPT)
  target     prot opt source               destination
  SNAT       tcp  --  <your host>  anywhere    tcp dpt:https to:172.16.0.242
  SNAT       tcp  --  <your host>  anywhere    tcp dpt:http to:172.16.0.242


What we test on
===============

* various x86_64 instances (both hardware and virtual machines)
  some with resources as low as 1 GB of ram
* several embedded arm/arm64 devices, mainly chromebooks and
  (better than rpi) clones, eg, nanopi-k2 and rockchip/allwinner devices

For chromebooks we use mainly Gentoo and Ubuntu on bootable media
built using `this chromebook build script`_ for developer mode.

.. _this chromebook build script: https://github.com/sarnold/chromebooks
