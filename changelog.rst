================
 fpnd Changelog
================


0.9.10 (2020-11-20)
-------------------
- Bump version 0.9.9 -> 0.9.10. [Stephen L Arnold]
- Merge pull request #97 from freepn/systemd-fixes. [Steve Arnold]
- Add init fixes for ip6_tables to systemd/openrc and update release notes.

  * closes issue #95 and removes cfg file install


0.9.9 (2020-11-19)
------------------
- Bump version 0.9.8 -> 0.9.9 (fixes python dep resolution in deb pkg) [Stephen L Arnold]
- Merge pull request #96 from freepn/check-deps. [Steve Arnold]

  * setup.py: restore old requires urls, keep appdirs version
  * Add bdist build/deploy check as final step.
  * Run CI tests on both ubuntu targets.
  * Setup.py: restore old requires urls, keep appdirs version.


0.9.8 (2020-11-16)
------------------
- update appdirs version and install coverage for ci
- README.rst: update build status for github ci. [Stephen L Arnold]
- Merge pull request #94 from freepn/exp-init. [Steve Arnold]
- systemd service refactor and misc fixes [Steve Arnold]

  - More logging cleanup, info/debug vs warning.
  - Update packaging files and requires, switch CI to github.
  - Bump version 0.9.7 -> 0.9.8 and update readme/release notes.
  - fpnd.service: refactor systemd service options so stop actually works.
  - Update msg_responder logging and minor doc fixes.


0.9.7 (2020-11-03)
------------------
- Update readme docs, add "breaking feature" note and fix overlay name. [Stephen L Arnold]
- Merge pull request #92 from freepn/chk-version. [Steve Arnold]

  - Add version checking/messages and shutdown for incompatible versions.
  - Cleanup net scripts, switch to MASQ, remove extraneous ip cmd, fix verbose.
  - Complete version check with do_shutdown, cleanup net scripts/msg daemons.
  - Wire up version handling and reply for new announce msg format.
  - README.rst: add install/upgrade notes and link to issue #88.
  - README_release-notes_latest.rst: remove version number from filename.


0.9.6 (2020-10-25)
------------------
- Merge pull request #90 from freepn/wait-states. [Steve Arnold]
- Fix: use max_timeout to wait before setting route to False. [Steve Arnold]
    
  * add wait_cache using max_timeout to fpn0 UP handler
  * make route check wait for max_timeout before setting route false
    
Fixes de-wedging nodes who never route and makes us a little more tolerant
of transient lookup errors (since route check relies on dns/https lookups
over fpn0 tunnel).


0.9.5 (2020-10-23)
------------------
- Merge pull request #86 from freepn/addr-filter. [Steve Arnold]
- Add handler to reset wedge state variables on fpn0 UP event. [Steve Arnold]
- Fix: extend nanoservice msg timeout and filter IPv6 from peer cache. [Steve Arnold]

  * Increase node message handler timeout from 1 second to 3 seconds
    (allow for more crufty internet latency).
  * Add proper filter for IPv6 addresses in (ZT) peer list
    (only cache IPv4 addresses).


0.9.4p1 (2020-10-20)
--------------------
- Merge pull request #84 from freepn/recache. [Steve Arnold]
    
  * helper_funcs.py: slight refactor in get_cachedir for Ubuntu/systemd


0.9.4 (2020-10-20)
------------------
- Merge pull request #82 from freepn/retests. [Steve Arnold]
- Fixes for github issues #78 # 79 and #80
- re-integrate/refactor get_cachdir/wait_cache and related tests

  * fix pytest.raises context for different OS/python envs
  * update tests for newer python/pytest
  * make sure ttl value is always an int
  * add modules.conf to load ip6tables core module before startup


0.9.3 (2020-10-02)
------------------
- Merge pull request #77 from freepn/tighter-rules. [Steve Arnold]
- Tighten/fix network route rules, update release notes. [Stephen Arnold]

  * fix missing (plain-text) dns routing rules
  * add src-net input allow/drop for udp traffic
  * add icmp limiting between peers


0.9.2 (2020-09-25)
------------------
- Merge pull request #76 from freepn/drop-ip6-cfg. [Steve Arnold]
- Finish drop IPv6 config, allow only localhost and zerotier ports.

  * fix default_iface test in do_net_cmd

- Add cfg option to set all IPv6 policies to DROP (default is true)


0.9.1 (2020-09-24)
------------------
- Merge pull request #75 from freepn/still-more-docs. [Steve Arnold]

  * Update release doc version/links, prep changelog, fix stubby example cfg.
  * Add domain-s port to optional routing, fix dnsmasq.conf, doc updates.

- Merge pull request #74 from freepn/leak-patch. [Steve Arnold]

  * Remove deprecated parameter from run_until_success decorator.
  * Add a new README_examples.rst doc, plus more doc updates.
  * Test/test_mock_api_get.py: fix silly N rules test.
  * Fix route check so it doesn't leak before the routes are configured.
  * examples: add dnsmasq cfg, update stubby resolver list
  * fix rules (allow encrypted DNS), update doc


0.9.0 (2020-09-22)
------------------
- Bump version for alpha release and update changelog. [Stephen Arnold]
- Merge pull request #73 from freepn/doc-updates. [Steve Arnold]

  * Add more-or-less complete draft of DNS setup doc.
  * Add Mate desktop graphic (uses default icons instead of installed icons)
  * Shrink screenshots (since github apparently ignores rst scaling)
  * Shrink images and check github rendering.
  * More README/DNS doc updates, one more screenshot.
  * More DNS doc and screenshot updates.
  * Stretch route_check timeout just a little bit and update DNS setup doc
  * README_DNS_setup.rst: add draft-in-progress.
  * Add some fixes and get rid of symlink.
  * Start docs refactor, add first screenshot, update some comments.


0.8.34 (2020-09-14)
-------------------
- bump version for packaging/testing cleanup handlers [Steve Arnold]
- Merge pull request #72 from freepn/cleanup_node_list. [Steve Arnold]

  * Add some new cleanup and cfg helpers to the root and ctlr nodes.


0.8.33 (2020-09-13)
-------------------
- Version bump for packaging/testing user configurable timeout. [Stephen Arnold]
- Merge pull request #71 from freepn/cfg_timeout. [Steve Arnold]

  * travis.yml: remove extraneous codecov from post-processing.
  * Cleanup local test output, move codecov processing to .travis.
  * Make net_change timeout value a config option, set default to 75 sec.


0.8.32 (2020-09-12)
-------------------
- Bump version for packaging/testing. [Stephen Arnold]
- Merge pull request #70 from freepn/timeouts. [Steve Arnold]

  * extend net change timeout for high latency/bad connections


0.8.31 (2020-09-11)
-------------------
- Version bump for packaging/testing, minor test update. [Stephen Arnold]
- Merge pull request #69 from freepn/net-chk-retry. [Steve Arnold]

  * update run_until_success decorator with unschedule arg
  * add decorator to net_check command with unschedule=false
  * limit wget args so it can only block up to 3 sec


0.8.30 (2020-09-09)
-------------------
- Add latest avahi issues to release doc, update changelog [Steve Arnold]
- Merge pull request #68 from freepn/docs-and-tweaks. [Steve Arnold]
- Bump version for setup.py packaging/testing.
- Fix leftover curl cruft, limit wget calls, add more doc updates.


0.8.29 (2020-09-07)
-------------------
- Tune some timeouts, use SNAT for postnat dns routing. [Stephen Arnold]
- Merge pull request #66 from freepn/tuning. [Steve Arnold]
- Tune some timeouts, use SNAT for forward routing.


0.8.28 (2020-09-05)
-------------------
- Bump version for packaging/testing. [Stephen Arnold]
- Merge pull request #65 from freepn/route-options. [Steve Arnold]

  dns routing config options (default off)
- Update ScheduleTests::test_run_net_cmd_sdown() for new settings.
- Add dns routing config option (default off) and config, update dns doc.


0.8.27 (2020-09-04)
-------------------
- Bump version for release tag. [Stephen Arnold]
- Merge pull request #64 from freepn/distro-fixes. [Steve Arnold]

  Distro fixes for multiple default routes and network interface names
- Add wiring for default iface, update default/test settings.
- Update netscripts for distro oddities, add config option (still
  unwired)


0.8.26 (2020-09-02)
-------------------
- Merge pull request #63 from freepn/docs-and-fixes. [Steve Arnold]

  Docs and fixes
- Remove silly ubuntu hack, restore sleep, add draft DNS privacy doc.
- Flesh out DNS privacy doc, minor readme updates, reset a log level.


0.8.25 (2020-09-01)
-------------------
- Update route check args, add more temp file cleanup, fix yast. [Stephen Arnold]


0.8.24 (2020-09-01)
-------------------
- Net script updates for multiple interfaces with a default route. [Stephen Arnold]

  * occurs when eth0 and wlan0 are both UP but only one has an address
    (only on ubuntu so far)


0.8.23 (2020-08-30)
-------------------
- Bump version and update deploy/test runners. [Stephen Arnold]
- Merge pull request #61 from freepn/cleanup-dns.
  Cleanup net scripts, keep "mixed" routing as default, switch route check back to wget.
- Use custom chains in net scripts, allow missing down zt interface/network. [Stephen Arnold]
- Update net scripts and route check (tight routing and wget) [Stephen Arnold]

  * remove dnscrypt traffic from routing, go back to snat
  * switch route check from curl back to wget, update return codes
  * update moon list with new moon ID
  * add stunnel.fpnd to needs in openrc init

- Capture current state of dns changes for next testing baseline. [Stephen Arnold]
- Add settings option for private dns only, propagate to net scripts. [Stephen Arnold]
- Switch SNAT to MASQ in net scripts, add node id output to test_tools. [Stephen Arnold]


0.8.22 (2020-08-16)
-------------------
- etc/fpnd.service: fix service deps for stunnel, cleanup docs/test config. [St$

  * remove python 3.5 from CI build/test
  * remove xenial from supported ubuntu series


0.8.21 (2020-08-11)
-------------------
- Merge pull request #60 from freepn/tls-msgs. [Steve Arnold]
  TLS msgs using stunnel (new testing baseline)

  * Add missing test and fix yet another typo.
  * Bin/fpn0-down.sh: cleanup any stale rules found on shutdown.
  * Node_tools/node_funcs.py: fix addr fallback and typo, update tests.
  * Make PKI the default config for ubuntu packages.
  * Add tls msg changes and new/updated config files, update test scripts.
  * Update test drivers with new node names, rename pkg build script.


0.8.20 (2020-08-02)
-------------------
- Merge pull request #55 from freepn/more-test. [Steve Arnold]
  More test and integration fixes.

  * Remove NONE msg on startup, bump version for packaging. [Stephen Arnold]
  * Node_tools: fix edge state detection, set mbr node wait_cache to 65 sec. [Stephen Arnold]


0.8.19 (2020-07-28)
-------------------
- Update tox/travis python versions, remove pep8/flake8 bits. [Stephen Arnold]
- Bump version for packaging/testing. [Stephen Arnold]
- Merge pull request #53 from freepn/state-testing. [Steve Arnold]
  collect post-test state fixes/cleanup, push out new pkgs for testing

  * Test/test_mock_api_get.py: fix expected exception in do_cleanup() [Stephen Arnold]
  * Reduce message retrys, update initial NONE state. [Stephen Arnold]
  * Nodestate: remove trailing cfg handler, fix test cleanup. [Stephen Arnold]
  * Node_tools/nodestate.py: fix error state (and msgs) [Stephen Arnold]


0.8.18 (2020-07-25)
-------------------
- Version bump for tag/packaging [Steve Arnold]
- Merge pull request #52 from freepn/nets-and-docs. [Steve Arnold]
- Refactor netstate/nodestate and orphan cleanup, update tests/test tools. [Stephen Arnold]

  * added update_mbr_data func to bootstrap, removed timing hacks
  * updated find/clean orphans, moved to exception handler
  * cleanup stale cfg msgs and refactor some msg queues
  * revert and refactor nodestate, update tests

- Misc fixes for netstate, test tools, and release doc. [Stephen Arnold]
- README_0.9.0-release-notes_DRAFT.rst: flesh out the rest of the draft. [Stephen Arnold]
- Release-notes: cleanup links, limit includes to changelog only. [Stephen Arnold]
- Update new docs, provide a link to changelog.rst (include not rendered) [Stephen Arnold]
- Handle netstate trie exception, update netstate node_list comparisons. [Stephen Arnold]

  * remove exit node from node list, update tests


0.8.17 (2020-07-17)
-------------------
- Merge pull request #51 from freepn/reconnect. [Steve Arnold]
- Reconnect user node on hard network error

  * Initial implementation of reconnect after error (and some initial tuning) [Stephen Arnold]


0.8.16 (2020-07-16)
-------------------
- Merge pull request #50 from freepn/net-scripts. [Steve Arnold]
- Net-scripts: check interfaces that are up against default route. [Stephen Arnold]


0.8.15 (2020-07-14)
-------------------
- Node_tools/__init__.py: version bump for packaging. [Stephen Arnold]
- Merge pull request #48 from freepn/state-msgs. [Steve Arnold]
- State msgs for gui status, switched from msg socket to state file.

  * Flesh out state msgs and cleanup tests.
  * Add state msg handler and tests, update changelog, add draft SVD doc.
  * Add publisher for state msgs, update tests/logging, cleanup doc strings.


0.8.14 (2020-07-12)
-------------------
- Merge pull request #47 from freepn/netstate-ref. [Steve Arnold]
- Netstate refactor, nodestate cleanup:

  * allow bad nets in netStatus so they can be removed
  * check for orphans and cleanup after wait_cache timeout

- Add some missing test bits for updated trie and cache funcs. [Stephen Arnold]
- Add netstate orphan cleanup and some wait_cache handling of nodes. [Stephen Arnold]

  * allow bad nets in netStatus so they can be removed
  * add 10 msec sleep to bootstrap/close to let things catch up
  * check for orphans and cleanup after wait_cache timeout
  * fix missing import, add more tests

- Add missing test plus more cleanup in trie_funcs. [Stephen Arnold]
- Revert "netstate tries: add prune option to remove stale net IDs" [Stephen Arnold]

  * This reverts commit 8f9bdf4e830368b7abbf99d576fae368b8dc29e0.

- Cleanup for new testing baseline, add some test tools and data. [Stephen Arnold]


0.8.13 (2020-07-06)
-------------------
- Netstate tries: add prune option to remove stale net IDs. [Stephen Arnold]
- Openrc config: add check func to also stop zerotier on shutdown. [Stephen Arnold]
- Add logrotate section for private fpnd log dir, cleanup rules. [Stephen Arnold]


0.8.12 (2020-06-29)
-------------------
- Cfg/: fix polkit fpnd policy and add rules file (for multiple ubuntus)
  [Stephen Arnold]
- Make sure polkit systemd1 local auth rules are set to active desktop.
  [Stephen Arnold]


0.8.11 (2020-06-24)
-------------------
- Merge pull request #43 from freepn/usr-cfg. [Steve Arnold]

  * Deploy and document some user convenience tweaks for polkit and sudo (needs testing on various targets)

- Update readme and permission configs, bump version and wrap ipnet
  queue. [Stephen Arnold]
- README.rst: add section on convenience configuration with examples.
  [Stephen Arnold]


0.8.10 (2020-06-20)
-------------------
- Merge pull request #42 from freepn/systemd. [Steve Arnold]

  * Systemd and openrc updates for (missing) site_state_dir on Linux (see PR #150 https://github.com/ActiveState/appdirs/pull/150)

- etc/fpnd.openrc: updates for appdirs/path integration. [Stephen
  Arnold]
- Bump version for next pre-release, try to avoid patch collision.
  [Stephen Arnold]
- Update systemd settings and ini defaults, set static site_state_dir.
  [Stephen Arnold]


0.8.9 (2020-06-17)
------------------
- Merge pull request #40 from freepn/appdirs. [Steve Arnold]

  * Add appdirs integration with fallback to system tempdir.

- node_tools/__init__.py: bump version for new pre-release tag. [Stephen
  Arnold]
- Add fallback directory, both as last resort and to make pytest
  happier. [Stephen Arnold]
- Use appdirs to set local directory paths and set user_dirs false for
  now. [Stephen Arnold]
- Bump version to non-patch release for packaging/deployment. [Stephen
  Arnold]

  * also contains some extra filtering for link-local addrs/routes but is
    not a complete fix


0.8.8 (2020-06-11)
------------------
- (hopefully) mitigate avahi/zeroconf link-local routes and addrs.
  [Stephen Arnold]
- Still more workarounds for net script cleanliness in multiple distros.
  [Stephen Arnold]
- Add missing unittest for job-cancel decorator (should improve this...)
  [Stephen Arnold]
- Add workarounds to remove non-zero return status from crippled
  /bin/sh. [Stephen Arnold]


0.8.7 (2020-06-10)
------------------
- Merge pull request #38 from freepn/netstate-refactor. [Steve Arnold]

  * Net state refactoring and network closure, some new helper funcs and unit-test updates, bump version for packaging.

- Add part 2 (unwrap) of network closure and enable it with min=3.
  [Stephen Arnold]

  * also bump the version so we can push some pkgs

- Add close_mbr_net() and a helper func, update tests. [Stephen Arnold]
- Update cleanup_state_tries test to pick up last change. [Stephen
  Arnold]
- Add get)target_node_id() plus a test, and update some docstrings.
  [Stephen Arnold]
- Tighten up netstate runner; ensure tries are updated after state
  changes. [Stephen Arnold]


0.8.6 (2020-06-05)
------------------
- Setup.py: bump version for release tag. [Stephen Arnold]
- Merge pull request #37 from freepn/issue-fixes. [Steve Arnold]

  * fixes for iptables/nf_tables and systemd execstop craziness

- Fixes for github issues #35 and #36 plus a cleanup logging change.
  [Stephen Arnold]

  * check for iptables-legacy and use it if found
  * stop letting systemd kill anything and manually send the TERM signal


0.8.5 (2020-06-01)
------------------
- Setup.py: bump version for packaging. [Stephen Arnold]
- Merge pull request #34 from freepn/new-rules. [Steve Arnold]
- Add network rules, update tests and docstrings. [Stephen Arnold]


0.8.4 (2020-05-28)
------------------
- Merge pull request #33 from freepn/test-options. [Steve Arnold]

  * Test options incorporated, push out for live integration testing.

- Setup.py: bump version for packaging. [Stephen Arnold]
- Add cfg cleanup, fix decorator, adjust params and doc strings.
  [Stephen Arnold]
- Scripts/msg_responder.py: fix missing semicolons. [Stephen Arnold]
- Update msg daemon logging, add/update queue handling funcs and tests.
  [Stephen Arnold]
- Allow re-connect to existing config if still present. [Stephen Arnold]


0.8.3 (2020-05-23)
------------------
- Update version in setup.py. [Stephen Arnold]
- Add sleep to force wait cache to expire. [Stephen Arnold]
- Fix the cause of sporadic travis-ci failures. [Stephen Arnold]

  * note this works fine on the desktop, go figure


0.8.2 (2020-05-23)
------------------
- Re-enable wedged msgs and update nodestate to allow only the first
  msg. [Stephen Arnold]
- Merge pull request #32 from freepn/state-checks. [Steve Arnold]

  * State checks and unittests (and time for deployment/testing).

- Version bump for pkging. [Stephen Arnold]
- Add ctlr wait cache and bootstrap funcs, update unittests. [Stephen
  Arnold]
- Add host_check func and unittest, post-test adjustment for offline
  wait. [Stephen Arnold]
- Post-integration state check updates, add more unit tests. [Stephen
  Arnold]
- Net state check updates/refactoring (still missing new unit tests)
  [Stephen Arnold]
- Add health_check for exit net status, still needs msging. [Stephen
  Arnold]
- Update version and add network health status checking (still WIP)
  [Stephen Arnold]


0.8.1 (2020-05-10)
------------------
- Post-test minor refactoring/abstraction, extend timeout. [Stephen
  Arnold]

  * abstract out connect_mbr_node() from offline function
  * extend moon data timeout for first-time startup

- Merge pull request #29 from freepn/refactor-state. [Steve Arnold]

  * more state handling for new nodes, refactor logging in subdaemons, fix net scripts, improve unit tests

- Test/test_node_tools.py: add one missing test, cleanup output/asserts.
  [Stephen Arnold]
- Clean up (and really fix) net scripts so they find the right ZT net.
  [Stephen Arnold]
- Update bootstrap/offline queues and msging, improve tests and test
  data. [Stephen Arnold]

  * this commit passes initial bootstrap/reconnect
  * still troubleshooting one test device kernel (5.6.3) that does not
    route (its own) outgoing traffic to the right interface

- Add ctlr state funcs for node bootstrapping, regen test data. [Stephen
  Arnold]
- Override drain_reg_queue, add offline msg processing, update tests.
  [Stephen Arnold]

  * adjust timing of daemon status checks
  * set max_hold parameter to 3

- More state handling for new nodes, refactor logging in subdaemons.
  [Stephen Arnold]
- Merge pull request #26 from freepn/more-msgs. [Steve Arnold]

  * Net state and msging updates

- Add new funcs to test_run_event_handler (really needs better tests)
  [Stephen Arnold]
- Some initial event handling, stale net cleanup, refactoring, and
  tests. [Stephen Arnold]

  * add net_q for handling active net IDs, including startup/shutdown
  * refactor validation funcs to remove assert statements
  * update/add tests, still needs more of these

- Add explicit logging error message for fallback mode (ZT network
  error) [Stephen Arnold]
- Fix mbr node bootstrap, refactor a bit, update tests. [Stephen Arnold]
- Complete (simple) node bootstrap, add more tests and test data.
  [Stephen Arnold]
- Partial bootstrap links, needs a bit of bisecting. [Stephen Arnold]
- Refactor msg handling and add state check/deorbit for mbr node
  startup. [Stephen Arnold]

  * relax msg queues (allow duplicates in root node queues)
  * add mbr node startup state check and test functions
  * propagate net script updates

- Fixes for LEAF node issue #27 and more ethernet device names. [Stephen
  Arnold]
- Add handle_net_cfg and test functions. [Stephen Arnold]
- Post-integration-test: remove/cleanup test cruft, simplify daemon
  check. [Stephen Arnold]
- Save working state (round-trip messages and tests, still WIP) [Stephen
  Arnold]
- Move bootstrap_mbr func to async (still no async tests yet) [Stephen
  Arnold]
- Add state trie and update mk_msg handling, add/fix tests. [Stephen
  Arnold]
- Split out bootstrap func, remove cruft, add test data, update tests.
  [Stephen Arnold]
- Test: minor test cleanup. [Stephen Arnold]
- Initial bootstrap of exit node, still needs cfg msg. [Stephen Arnold]
- Merge pull request #25 from freepn/new-msging. [Steve Arnold]

  * New msging funcs and refactoring plus test updates.

- Some refactoring, add req/sub daemon shutdown, fix trie tests.
  [Stephen Arnold]
- Node_tools/node_funcs.py: fix logging and add small adhoc test.
  [Stephen Arnold]
- Refactor msg daemons and cmds, wire up cfg_msg and ensure failure.
  [Stephen Arnold]
- Test: add test updates/fixes for latest. [Stephen Arnold]
- Add cfg_msg func and tests, load cfg_msg state, update trie checking.
  [Stephen Arnold]
- Node_tools: refactor cfg msg overrides and update msg validation.
  [Stephen Arnold]

  * include both msg refs in state data
  * update tests

- Fix tests after revert of msg func signature. [Stephen Arnold]
- Revert overrides to msg client and sched wrapper (WIP test) [Stephen
  Arnold]
- Node_tools/msg_queues.py: make wait_for_cfg_msg/tests match design
  doc. [Stephen Arnold]
- Override msg handling funcs, add cfg handling to rsp daemon, add
  tests. [Stephen Arnold]
- Test/test_node_msgs.py: add pub_q to msg tests. [Stephen Arnold]
- Update/add queue for published node IDs, add stub, update doc strings.
  [Stephen Arnold]


0.8.0 (2020-03-17)
------------------
- README_adhoc-mode.rst: fix missing edit in example comment. [Stephen
  Arnold]
- Merge pull request #23 from freepn/cfg-msgs. [Steve Arnold]

  * peer mode cfg message baseline with datrie fixes

- Update setup.py for datrie fixes and add more README notes. [Stephen
  Arnold]
- Adjust member node startup (timing/moons) and improve tests. [Stephen
  Arnold]

  * split moon wait function into two (improve testability)
  * adjust startup timing and moon handling
  * update existing test, add new unittest
  * update member node startup in fpnd

- Some refactoring and cleanup, update tests and default mode. [Stephen
  Arnold]


0.7.3 (2020-03-10)
------------------
- Setup.py: version bump for new (non-patch) release. [Stephen Arnold]

  * includes adhoc mode with setup doc

- README.rst: fix silly typos...  (alertly noticed ny steev) [Stephen
  Arnold]
- README docs: expand, incorporate feedback, update changelog. [Stephen
  Arnold]
- README_adhoc-mode.rst: add links for PPA/overlay install steps.
  [Stephen Arnold]
- Update and add more documentation (README, README_adhoc-mode,
  comments) [Stephen Arnold]
- Merge pull request #20 from freepn/adhoc-testing. [Steve Arnold]

  * Adhoc testing updates, still needs a new doc and more tests.

- Rev-bump patch release version in setup.py. [Stephen Arnold]
- .travis.yml: install datrie build deps (should fix nightly fail)
  [Stephen Arnold]
- Node_tools/nodestate.py: update input addr for new do_peer_check()
  [Stephen Arnold]
- Setup.py: add new bin/ scripts (and re-gen patch for ebuild) [Stephen
  Arnold]
- Adhooc mode testing updates, including update/add netscript
  tools/tests. [Stephen Arnold]
- Add list of service ports to bin/fpn* (pre-test WIP) [Stephen Arnold]
- Update geoip script and add to setup.py (and re-gen patch for ebuild)
  [Stephen Arnold]
- Add tests, update test data and versions in setup.py. [Stephen Arnold]
- Update/rename get_ztcli_data and allow "extra" args, eg, <nwid>
  [Stephen Arnold]
- Bin/fpn1-geoip.sh: add script to check geoip via https. [Stephen
  Arnold]
- Add nwid arg for adhoc mode and clean up netscripts. [Stephen Arnold]
- Update setup.py and changelog.rst (really need to do that more
  often...) [Stephen Arnold]
- Pre-test baseline for adhoc mode packages (still somewhat a WIP)
  [Stephen Arnold]
- Merge pull request #17 from freepn/ctlr-funcs. [Steve Arnold]

  * Ctlr funcs and async wrappers, new feature baseline

- Make trie-based netstate runner the default, remove stale code.
  [Stephen Arnold]
- Test/test_node_tools.py: cleanup stray print cmd. [Stephen Arnold]
- Split out async wrapper funcs, cleanup ctlr funcs, add
  tests/bootstrap. [Stephen Arnold]
- Update/add more ctlr funcs and tests, split large test file. [Stephen
  Arnold]
- Add another test version of netstate API runner (pre-cleanup, still
  WIP) [Stephen Arnold]
- Refactor stored trie funcs, add still more test code. [Stephen Arnold]
- Add more ctlr glue, slightly refactor state runners, update tests.
  [Stephen Arnold]
- Setup.py: add datrie dependency and cleanup URLs. [Stephen Arnold]
- Move function wrapper, remove stale code, update tests (still WIP)
  [Stephen Arnold]
- Test/test_node_tools.py: add new tests to test_cache_loading()
  [Stephen Arnold]
- Save WIP state, pre-removal of orthogonal trie code. [Stephen Arnold]
- Update ctlr baseline with new module, add some tests and test toiols.
  [Stephen Arnold]
- Merge pull request #14 from freepn/msg_updates. [Steve Arnold]

  * Msg updates for validation, one more state runner for ctlr data.

- Updates for ctlr endpoint data, loads net/mbr data to Index cache
  (WIP) [Stephen Arnold]
- Test/test_node_tools.py: add one more test, tweak test data. [Stephen
  Arnold]
- Add list of leaf nodes to state_data for github issue #13. [Stephen
  Arnold]
- Scripts/msg_responder.py: add syslog/messages logging for valid
  message. [Stephen Arnold]
- README.rst: update readme after test-drive feedback. [Stephen Arnold]
- Update setup.py/defaults and add/tweak some msg test tools. [Stephen
  Arnold]
- Setup.py: use PEP 440 version for 0.7.2 post-release tag. [Stephen
  Arnold]
- Post-test systemd init fixes from buster/bionic, fix func scope.
  [Stephen Arnold]
- .codeclimate.yml: exclude "scripts/" since default only has "script/"
  [Stephen Arnold]


0.7.2 (2020-02-07)
------------------
- Setup.py: python pkg version bump for next release. [Stephen Arnold]
- Merge pull request #12 from freepn/msg-queues. [Steve Arnold]

  * Msg queues and test updates (baseline for next phase)

- Add/update node msg/queue handling and add more tests. [Stephen
  Arnold]

  * new ctlr function handle_node_queues and a staging queue
  * transaction contexts to node queue handling funcs
  * new tests for pub and queue funcs

- Add/update baseline ctlr files, update pkg data install. [Stephen
  Arnold]
- Next leg of node messaging plus test tools (still WIP) [Stephen
  Arnold]

  * note this requires some infra deployment/configuration of the backend
    nodes

- Move msg validation, refactor zerotier-cli cmds, add more tests.
  [Stephen Arnold]

  * refactored two zerotier-cli commands into one
  * moved msg validation to msg_queues.py, added tests
  * more testing of node registration msgs

- Scripts/msg_responder.py: add msg format and type checking to
  responder. [Stephen Arnold]
- Add tests for queue and msg handling. [Stephen Arnold]
- Node_tools/msg_queues.py: process incoming messages and msg queues.
  [Stephen Arnold]

  * update exports, move processing to msg_queues.py
  * adds queues for incoming and registered nodes
  * adds wait queue for holding and expiring if no msg
  * processing stops at reg_queue (nothing to drain it yet)

- Create FUNDING.yml. [Ian H. Bateman]
- Pluck fix for test/test_node_tools.py changes from another branch.
  [Stephen Arnold]

  * This reverts commit 33f6aaca73196baa3cfcbfe1469ac76c764eb2d6.

- Merge pull request #11 from freepn/base-test. [Steve Arnold]

  * initial infra baseline for roles and announce msg

- Cleanup and add more tests for new code, remove some unused code.
  [Stephen Arnold]
- Fix role-based startup, add data parsing in wait_for_moon (needs
  tests) [Stephen Arnold]
- Scripts/fpnd.py: enable early role check for infra nodes. [Stephen
  Arnold]
- Revert test/test_node_tools.py changes. [Stephen Arnold]

  * This reverts commit 33f6aaca73196baa3cfcbfe1469ac76c764eb2d6.

- Fix get_state() and reverse default setting for localhost. [Stephen
  Arnold]
- Test/test_node_tools.py: adjust test assert for tighter moon reqs.
  [Stephen Arnold]
- Add try/except block to send_message, open listen address. [Stephen
  Arnold]
- Test/test_node_tools.py: adjust test assert for tighter moon reqs.
  [Stephen Arnold]
- Merge pull request #10 from freepn/role-tests. [Steve Arnold]

  * update modules, scripts, and tests for initial role-based features

- Post-local testing updates, baseline for new role funcs. [Stephen
  Arnold]

  * note there is still no state runner for the controller yet

- Update modules, scripts, and tests for initial role-based features.
  [Stephen Arnold]
- Cleanup after removing regState, switch to a single field. [Stephen
  Arnold]
- Node_tools and document cleanup, add more ad-hoc test runners.
  [Stephen Arnold]
- README.rst: update for new overlay pointer/name. [Stephen Arnold]
- Merge pull request #9 from freepn/messaging. [Steve Arnold]

  * Messaging and roles plus project doc updates

- README.rst: fix silly formatting typo. [Stephen Arnold]
- README.rst: flesh out readme using new template, add CONTRIBUTING.rst.
  [Stephen Arnold]
- More test cleanup, remove experimental cruft. [Stephen Arnold]
- Flesh out role funcs, cleanup test state (make tests more unit-y)
  [Stephen Arnold]
- Remove cruft, minor test updates, msg tests need more work. [Stephen
  Arnold]
- Finish tests for control_daemon (see comments, yet another corner
  case) [Stephen Arnold]
- Update setup.py to install msg_responder script. [Stephen Arnold]
- Complete role checking and update tests, add to fpnd before moon
  setup. [Stephen Arnold]

  * note we don't use the early role checking until more testing
    with non-default roles

- Add role checking and tests (moon integration WIP) [Stephen Arnold]
- Scripts/msg_responder.py: fix crufty comments. [Stephen Arnold]
- Add more messaging flavor, tests, and updated codecov config. [Stephen
  Arnold]
- Remove p27 and py32 import conditionals (we only support 3.5 and up)
  [Stephen Arnold]

  * also try a different (and validated) codecov config

- Update path check, add one more test for net commands. [Stephen
  Arnold]
- Codecov.yml: try adding sample config (borrowed from pyparsing)
  [Stephen Arnold]
- See what happens with this coverage graph... [Stephen Arnold]
- Install missing codecov dep (doh!) [Stephen Arnold]
- Merge pull request #8 from freepn/node_reg. [Steve Arnold]

  * Node reg message using local socket

- Update readme and tox/travis configs for codecov. [Stephen Arnold]
- .travis.yml: update before_install with new and moved deps. [Stephen
  Arnold]
- Replace raise with a warning, make tests better, update pkg deps,
  readme. [Stephen Arnold]
- Add nanoservice dep and echo test handlers, update tests. [Stephen
  Arnold]
- Test/test_node_tools.py: use test cache dir for tests and update
  sizes. [Stephen Arnold]
- One more check threshold test, make it just a bit less tolerant.
  [Stephen Arnold]
- .codeclimate.yml: test smaller adjustments for returns/nested.
  [Stephen Arnold]
- .codeclimate.yml: add checks section, set max complexity to 15.
  [Stephen Arnold]
- README.rst: switch to more tolerant (shields.io) tag-based version
  badge. [Stephen Arnold]
- Merge pull request #7 from freepn/net-conf. [Steve Arnold]

  * Update net config tests and test tools

- Setup.py: remove check script from data_files (moved to test_tools
  dir) [Stephen Arnold]
- Update classifiers in setup.py, add .codeclimate.yml, move test tools.
  [Stephen Arnold]
- Setup.py: fix install_requires after github move. [Stephen Arnold]
- Stimm more test updates and some minor refactoring. [Stephen Arnold]

  * make sure the state changes diff is a tuple
  * update log_fpn_state/run_event_handlers with optional diff arg
  * add test settings config discovery to config_from_ini
  * simplify show_job_tags decorator and add to tests
  * cleanup in both test files

- Post-integration and unit test updates with extra test stubs and cfg.
  [Stephen Arnold]
- Merge pull request #6 from sarnold/net-conf. [Steve Arnold]

  * Add state change triggers for fpn network config via job scheduler

- Remove extra logging and update travis notify config. [Stephen Arnold]
- Add triggered event handling for fpn net configuration cmds. [Stephen
  Arnold]

  * add net_change_handler and run_event_handlers functions
  * add imports and call event handler from end of cache wrapper
  * move get_state_values to avoid stale state-change on startup
  * update get_net_cmds so it always returns a list (or None)
  * add/update logging, adjust get_net_cmds tests

- Scripts/fpnd.py: minor cleanup, remove extraneous logger call.
  [Stephen Arnold]
- Merge pull request #5 from sarnold/shared-vars. [Steve Arnold]

  * Shared state vars and job decorators

- Finish up xform_state_diff() using ``old_/new_`` prefix for duplicate
  keys. [Stephen Arnold]
- Still working on state data changes dict and tests (WIP) [Stephen
  Arnold]
- Add more tests and more post-test fixes, update test deps/cfg.
  [Stephen Arnold]

  * decorated run_net_cmd and started adding tests for sched_funcs.py
  * fixed check_return_status based on unit tests
  * update test deps/cfg to include mock and coverage plugin
  * move run_net_cmd tests to separate test file, mark xfail (bullet 1)
  * use borrowed schedule test mocks to bootstrap decorator tests

- Add sched_funcs (with test driver but no unit tests) and update deps.
  [Stephen Arnold]
- Cleanup net cmds and add more tests, move config/setup funcs from
  fpnd. [Stephen Arnold]

  * refactored/robustified net cmds
  * moved config/setup functions to helper_funcs
  * added 'home' and 'debug' to NODE_SETTINGS (loaded from config)

- Move state check log msg to end of decorator. [Stephen Arnold]
- Add shared state vars for change events, refactor and add more tests.
  [Stephen Arnold]
- Testing shared state vars (probably not what we want...) [Stephen
  Arnold]
- Add get_state_values function plus some tests (part 1 of 2) [Stephen
  Arnold]
- Add get_state dict builder and allow substrings in find_keys. [Stephen
  Arnold]
- Add network state helper function with tests, update docstrings.
  [Stephen Arnold]
- Node_tools/data_funcs.py: update docstrings for clarity. [Stephen
  Arnold]
- Merge pull request #2 from sarnold/moon-base. [Steve Arnold]

  * Moon base - baseline for adding event hooks

- Remove extra logging trace calls, default to new logging format.
  [Stephen Arnold]
- Post runtime testing updates and fixes (includes fix for issue #3)
  [Stephen Arnold]

  * cache_funcs.py: handle condition for missing routes
  * logger_config.py: add local logger config
  * nodestate.py: handle generic exception
  * fpnd.py: switch logger, remove cruft, shorten cycle time
  * add more tests

- Test/test_node_tools.py: fix one and add more tests. [Stephen Arnold]
- Add state data to cache (node, moons, nets) and update tests. [Stephen
  Arnold]
- Add scheduler helpers, fix some nits, cleanup logging. [Stephen
  Arnold]
- Post-test logging cleanup, switch to generic Exception. [Stephen
  Arnold]
- Add exception handlers for missing cli, fix crufty import in fpnd.py.
  [Stephen Arnold]
- Remove load_moon_data and add moon data after peers are updated (test)
  [Stephen Arnold]
- Test/test_node_tools.py: fix expected result (post test data update)
  [Stephen Arnold]
- Collect baseline updates and minor fixes. [Stephen Arnold]
- Refactor moon commands and tests, add fpn moons to settings (test on
  arm) [Stephen Arnold]
- Add test functions and start fleshing out node_funcs.py. [Stephen
  Arnold]
- Scripts/fpnd.py: fix crash-y (but still silly) typo. [Stephen Arnold]
- Respin tests and add json test data files, add more functions.
  [Stephen Arnold]
- README.rst: add badge for some codeclimate workout. [Stephen L Arnold]
- Still more refactoring and related test updates. [Stephen L Arnold]
- Add namedtuple data types and test functions for endpoints. [Stephen L
  Arnold]
- Remove bin data and generate some json instead. [Stephen Arnold]
- Experiment with tests (and functions under test; needs refactoring)
  [Stephen Arnold]
- Tox.ini: get more coverage details. [Stephen Arnold]
- Use test cache file for testing simple get_status function. [Stephen
  Arnold]
- Fix local variable in cache aging wrapper and .isoformat args on py35.
  [Stephen Arnold]
- Optimize basic tests, add test coverage/report. [Stephen L Arnold]
- Use full imports and start adding (really basic) tests. [Stephen L
  Arnold]
- Fix node data update and cache timestamp. [Stephen Arnold]
- Add some test funcs, update check scripts. [Stephen L Arnold]
- Merge pull request #1 from sarnold/use_prefix. [Steve Arnold]

  * Use prefix for primary key types

- Node_tools/data_funcs.py: add closing logstamp and default logrotate
  cfg. [Stephen Arnold]
- After debug logging on armv7: post-test adjustments/cleanup. [Stephen
  Arnold]
- Add another helper module and schedule one (1) update job at max/2.
  [Stephen Arnold]
- Bin: make shell script VERBOSE flag all-or-nothing (still trap errors)
  [Stephen Arnold]
- Node_tools/cache_funcs.py: make delete atomic. [Stephen Arnold]
- Refactoring of cache_check using cache_funcs. [Stephen L Arnold]
- Add cache and network support modules, start fleshing (still WIP)
  [Stephen Arnold]
- Etc/fpnd.openrc: simplify and check for config file (gentoo only)
  [Stephen Arnold]
- Post-integration testing init fixes and cleanup (ditch bin wrapper)
  [Stephen Arnold]


0.7.1 (2019-12-19)
------------------
- New pkg changes: update setup.py install paths, cleanup shebangs.
  [Stephen Arnold]


0.7.0 (2019-12-19)
------------------
- Scripts/fpnd.py: pep8 cleanup, add irc notifies to .travis.yml.
  [Stephen Arnold]


0.0.6 (2019-12-18)
------------------
- Post-integration testing (using gentoo patch for python-exec) fixes.
  [Stephen Arnold]
- Rename scripts one more time, add bin wrapper to make dh/setup.py
  happy. [Stephen Arnold]


0.0.5 (2019-12-17)
------------------
- Scripts/fpnd.py: revert pre-install name change, update setup.py.
  [Stephen Arnold]
- Setup.py: update for previous qa fixes. [Stephen Arnold]


0.0.4 (2019-12-17)
------------------
- Remove filename extensions from "bin" files, set perms on init
  scripts. [Stephen Arnold]


0.0.3 (2019-12-17)
------------------
- Setup.py: mv installed files out of debian dir to etc dir (in src
  tree) [Stephen Arnold]
- Workaround for setup.py: adjust payload paths for data_files and
  scripts. [Stephen Arnold]
- Update ini file handling, add network scripts, update setup.py.
  [Stephen Arnold]
- LICENSE: fix license. [Stephen Arnold]
- Changelog.rst: add changlelog with 0.0.1..0.0.2 commit info. [Stephen
  Arnold]


0.0.2 (2019-12-16)
------------------
- README.rst: add some badges. [Stephen Arnold]
- Force new pip version and use github sources in install_requires.
  [Stephen L Arnold]
- Fix setup.py dependencies (git only for daemon/ztcli pkgs) [Stephen
  Arnold]

  - try tox one more time

- Add workaround for pytest.mark.pep8 issue, switch back to py.test.
  [Stephen Arnold]
- Re-jigger travis, tox, and pytest configs, add setup.cfg rules.
  [Stephen Arnold]
- .travis.yml: use tox as test driver (allow longer lines) [Stephen
  Arnold]
- .travis.yml: add basic travis config (only pep8 and flake8 for now)
  [Stephen Arnold]
- Mainly flake8 and tox cleanup. [Stephen L Arnold]
- Node_tools: cleanup imports, trap connection error in update_state.
  [Stephen L Arnold]

  * also update cache_check script to current test version

- Node_tools: add ztcli exceptions subclass, adjust imports, age cache.
  [Stephen L Arnold]

  * note cache aging needs to "wrap" the nodestate query so the timestamp
    does not clutter the cached data

- Scripts/fpn_cache_check.py: add manual test script for now. [Stephen L
  Arnold]
- Node_tools/nodestate.py: adjust data unavailable handling. [Stephen L
  Arnold]

  * keep the cache and dont exit, look at cache data aging

- Node_tools/nodestate.py: add some cache maintenance (no cache.clear)
  [Stephen L Arnold]
- Node_tools/nodestate.py: add caching of peers and networks. [Stephen L
  Arnold]
- Node_tools: add bonus attributes to cached data (so dot notation
  works) [Stephen L Arnold]
- Node_tools: add state updater finction to run nodestate from
  elsewhere. [Stephen L Arnold]
- Node_tools/nodestate.py: change to full import for external caller.
  [Stephen L Arnold]

  * note this seems like a hack since nodestate is being "run" from another
    python script with a different namespace

- Setup.py: fix silly typo... [Stephen Arnold]


0.0.1 (2019-12-11)
------------------
- New package for fpnd tools (uses module import for now) [Stephen
  Arnold]
- Initial commit. [Steve Arnold]
