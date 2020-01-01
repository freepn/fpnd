# coding: utf-8

"""Node-specific fpn helper functions."""
from __future__ import print_function

import logging


logger = logging.getLogger(__name__)


def get_moon_data():
    import json
    import subprocess
    cmd = ['zerotier-cli', 'listmoons']

    b = subprocess.Popen(cmd,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE,
                         shell=False)

    out, err = b.communicate()

    # always return a list (empty if no moons)
    if err:
        # out = b'[]'
        res = json.loads(b'[]'.decode().strip())
        logger.error('get_moon_data err result: {}'.format(err.decode().strip()))
    else:
        res = json.loads(out.decode().strip())
        logger.debug('found moon id: {}'.format(res[0]['id']))

    return res


def run_moon_cmd(moon_id, action='orbit'):
    """
    Run moon command via zerotier-cli and trap the output.

    :param action: one of <orbit|deorbit>
    :param moon_id: id of the moon to operate on
    :return true|false: command success
    """
    import subprocess

    result = False

    if action == 'orbit':
        cmd = ['zerotier-cli', action, moon_id, moon_id]
    elif action == 'deorbit':
        cmd = ['zerotier-cli', action, moon_id]
    else:
        logger.error('Invalid action: {}'.format(action))
        return result

    b = subprocess.Popen(cmd,
                         stderr=subprocess.PIPE,
                         stdout=subprocess.PIPE,
                         shell=False)

    out, err = b.communicate()

    res = out.decode().strip()
    logger.debug('run_moon_cmd result: {}'.format(res))

    if 'OK' in res:
        result = True
    else:
        logger.error('run_moon_cmd err result: {}'.format(err.decode().strip()))

    logger.debug('Leaving run_moon_cmd: {}'.format(result))
    return result


def wait_for_moon():
    """Wait for moon data on startup before sending any messages."""
    raise NotImplementedError
