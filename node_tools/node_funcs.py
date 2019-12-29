# coding: utf-8

"""Node-specific fpn helper functions."""
from __future__ import print_function

import logging

from node_tools.cache_funcs import find_keys
from node_tools.cache_funcs import load_cache_by_type


logger = logging.getLogger(__name__)

FPN_MOONS = ['4f4114472a']  # list of fpn moons to orbiit


def get_moon_data():
    import subprocess
    cmd = ['zerotier-cli', 'listmoons']
    res = subprocess.run(cmd,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT,
                         universal_newlines=True,
                         shell=False)
    # always return a list (empty if no moons)
    if res.returncode == 0:
        result = res
    else:
        result = []
    return result


# we need to enforce a timeout for now
def load_moon_data(cache, timeout=9):
    import time
    moon_data = get_moon_data()
    key_list = find_keys(cache, 'moon')
    while not moon_data:
        for s in range(timeout):
            moon_data = get_moon_data()
            time.sleep(1)
        break
    if moon_data:
        load_cache_by_type(cache, moon_data, 'moon')
        return True
    else:
        logger.debug('No moon data after {} seconds')
        return False


def orbit_moon(moon_id):
    import subprocess
    cmd = ['zerotier-cli', 'orbit', moon_id, moon_id]
    if not get_moon_data():
        res = subprocess.run(cmd,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT,
                             universal_newlines=True,
                             shell=False)
        if 'OK' in res.stdout:
            logger.debug('Orbit moon id {} result was OK'.format(moon_id))
            return True
        else:
            logger.error('Could not orbit moon id {}'.format(moon_id))
            return False


def wait_for_moon():
    """Wait for moon data on startup before sending any messages."""
    raise NotImplementedError
