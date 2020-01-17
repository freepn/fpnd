# coding: utf-8

"""Node-specific fpn helper functions."""
from __future__ import print_function

import logging

from node_tools.helper_funcs import NODE_SETTINGS


logger = logging.getLogger(__name__)


def control_daemon(action):
    """
    Controller function for msg_responder daemon.
    :param action: one of <start|stop|restart>
    """
    import os
    import sys

    result = ''
    home = NODE_SETTINGS['home_dir']
    commands = ['start', 'stop', 'restart']
    daemon_file = os.path.join(home, 'msg_responder.py')

    if not os.path.isfile(daemon_file):
        result = None
    if action not in commands:
        result = False

    try:
        os.system(" ".join((sys.executable, daemon_file, action)))
        result = True
    except Exception as exc:
        logger.error('msg_responder exception: {}'.format(exc))
        pass
    return result


def get_moon_data():
    import json
    import subprocess

    cmd = ['zerotier-cli', 'listmoons']
    # always return a list (empty if no moons)
    result = json.loads(b'[]'.decode().strip())

    try:
        b = subprocess.Popen(cmd,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             shell=False)

        out, err = b.communicate()

        if err:
            logger.error('get_moon_data err result: {}'.format(err.decode().strip()))
        else:
            result = json.loads(out.decode().strip())
            logger.info('found moon id: {}'.format(result[0]['id']))
            logger.debug('Moon data type is: {}'.format(type(result)))

    except Exception as exc:
        logger.error('zerotier-cli exception: {}'.format(exc))
        pass

    return result


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

    try:
        b = subprocess.Popen(cmd,
                             stderr=subprocess.PIPE,
                             stdout=subprocess.PIPE,
                             shell=False)

        out, err = b.communicate()

        if err:
            logger.error('run_moon_cmd err result: {}'.format(err.decode().strip()))
        elif 'OK' in out.decode().strip():
            result = True
            logger.debug('run_moon_cmd result: {}'.format(out.decode().strip()))

    except Exception as exc:
        logger.error('zerotier-cli exception: {}'.format(exc))
        pass

    return result


def wait_for_moon():
    """
    Wait for moon data on startup before sending any messages.
    """
    pass
