0.7.2p4 (2020-02-27, pre-Alpha) [Stephen Arnold]
------------------------------------------------

- Pre-test baseline for adhoc mode packages (still somewhat a WIP)
- Merge pull request #17 from freepn/ctlr-funcs.

  * Ctlr funcs and async wrappers, new feature baseline

- Make trie-based netstate runner the default, remove stale code.
- Split out async wrapper funcs, cleanup ctlr funcs, add tests/bootstrap.
- Refactor stored trie funcs, add still more test code.
- Add more ctlr glue, slightly refactor state runners, update tests.
- Setup.py: add datrie dependency and cleanup URLs.
- Test/test_node_tools.py: add new tests to test_cache_loading()
- Save WIP state, pre-removal of orthogonal trie code.
- Update ctlr baseline with new module, add some tests and test tools.
- Merge pull request #14 from freepn/msg_updates.

  * Msg updates for validation, one more state runner for ctlr data.

- Updates for ctlr endpoint data, loads net/mbr data to Index cache
- Add list of leaf nodes to state_data for github issue #13.
- Scripts/msg_responder.py: add syslog/messages logging for valid message.

0.0.2 (2019-12-16) [Stephen L Arnold]
-------------------------------------

- Force new pip version and use github sources in install_requires.
- Fix setup.py dependencies (git only for daemon/ztcli pkgs).

- Add workaround for pytest.mark.pep8 issue, switch back to py.test.
- Re-jigger travis, tox, and pytest configs, add setup.cfg rules.
- Node_tools: cleanup imports, trap connection error in update_state.

  * also update cache_check script to current test version

- Node_tools: add ztcli exceptions subclass, adjust imports, age cache.

  * note cache aging needs to "wrap" the nodestate query so the timestamp
    does not clutter the cached data

- Scripts/fpn_cache_check.py: add manual test script for now.
- Node_tools/nodestate.py: adjust data unavailable handling.

  * keep the cache and dont exit, look at cache data aging

- Node_tools/nodestate.py: add some cache maintenance (no cache.clear)
- Node_tools/nodestate.py: add caching of peers and networks.
- Node_tools: add bonus attributes to cached data (so dot notation works)
- Node_tools: add state updater function to run nodestate from elsewhere.
- Node_tools/nodestate.py: change to full import for external caller.

  * note this seems like a hack since nodestate is being "run" from another
    python script with a different namespace

