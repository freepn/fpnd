0.0.2 (2019-12-16)
------------------
- Force new pip version and use github sources in install_requires. [Stephen L Arnold]
- Fix setup.py dependencies (git only for daemon/ztcli pkgs) [Stephen Arnold]

- Add workaround for pytest.mark.pep8 issue, switch back to py.test. [Stephen Arnold]
- Re-jigger travis, tox, and pytest configs, add setup.cfg rules. [Stephen Arnold]
- Node_tools: cleanup imports, trap connection error in update_state. [Stephen L Arnold]

  * also update cache_check script to current test version

- Node_tools: add ztcli exceptions subclass, adjust imports, age cache. [Stephen L Arnold]

  * note cache aging needs to "wrap" the nodestate query so the timestamp
    does not clutter the cached data

- Scripts/fpn_cache_check.py: add manual test script for now. [Stephen L Arnold]
- Node_tools/nodestate.py: adjust data unavailable handling. [Stephen L Arnold]

  * keep the cache and dont exit, look at cache data aging

- Node_tools/nodestate.py: add some cache maintenance (no cache.clear) [Stephen L Arnold]
- Node_tools/nodestate.py: add caching of peers and networks. [Stephen L Arnold]
- Node_tools: add bonus attributes to cached data (so dot notation works) [Stephen L Arnold]
- Node_tools: add state updater function to run nodestate from elsewhere. [Stephen L Arnold]
- Node_tools/nodestate.py: change to full import for external caller. [Stephen L Arnold]

  * note this seems like a hack since nodestate is being "run" from another
    python script with a different namespace

