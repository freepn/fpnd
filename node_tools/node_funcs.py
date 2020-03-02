# coding: utf-8

"""Node-specific fpn helper functions."""
from __future__ import print_function

import logging

from node_tools.exceptions import MemberNodeError
from node_tools.helper_funcs import NODE_SETTINGS


logger = logging.getLogger(__name__)


def control_daemon(action, script='msg_responder.py'):
    """
    Controller function for messaging daemon.
    :param action: one of <start|stop|restart>
    """
    import os
    import subprocess

    result = ''
    home = NODE_SETTINGS['home_dir']
    commands = ['start', 'stop', 'restart']
    daemon_file = os.path.join(home, script)

    if not os.path.isfile(daemon_file):
        result = None
    if action not in commands:
        result = False

    try:
        result = subprocess.call([daemon_file, action], shell=False)
        if result < 0:
            logger.error('cmd terminated by signal: {}'.format(result))
        else:
            logger.debug('cmd returned: {}'.format(result))
    except OSError as exc:
        logger.error('cmd exception: {}'.format(exc))
    return result


def run_ztcli_cmd(command='zerotier-cli', action='listmoons', extra=None):
    """
    Command wrapper for zerotier commands ``listmoons``, ``info``, etc,
    where normal output is a text string (some actions such as ``listmoons``
    will return a JSON string).
    :param command: zerotier command to run, eg, ``zerotier-cli``
    :param action: action for command to run, eg, ``info``
    :param extra: extra args for command/action, eg, <network_id>
    :return result: one of ``str``, ``[]``, or None
    """
    import json
    import subprocess

    cmd = [command, action]
    if extra:
        cmd = [command, action, extra]

    result = None
    if action == 'listmoons':
        # always return a list (empty if no moons)
        result = json.loads(b'[]'.decode().strip())

    try:
        b = subprocess.Popen(cmd,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             shell=False)

        out, err = b.communicate()

        if err:
            logger.error('{} {} err result: {}'.format(command,
                                                       action,
                                                       err.decode().strip()))
        else:
            if action == 'listmoons':
                result = json.loads(out.decode().strip())
                logger.info('got moon id: {}'.format(result[0]['id']))
            else:
                result = out.decode().strip()
            logger.debug('got data: {}'.format(result))

    except Exception as exc:
        logger.error('zerotier-cli exception: {}'.format(exc))
        pass

    return result


def parse_moon_data(data):
    """
    Parse moon metadata returned from get_moon_data function so we can
    use the ID and endpoint address during daemon startup.
    """
    import ipaddress
    from node_tools.helper_funcs import AttrDict

    result = []
    for item in data:
        moon_data = AttrDict.from_nested_dict(item)
        moon_id = moon_data.id.replace('000000', '', 1)
        for root in moon_data.roots:
            root_data = AttrDict.from_nested_dict(root)
            for endpoint in root_data.stableEndpoints:
                addr = endpoint.split('/')
                try:
                    addr_obj = ipaddress.ip_address(addr[0])
                except ValueError as exc:
                    logger.error('ipaddress exception: {}'.format(exc))
                if addr_obj.version == 4:
                    moon_addr = addr[0]
                    moon_port = addr[1]
                else:
                    return result
        result.append((moon_id, moon_addr, moon_port))

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


def run_subscriber_daemon(cmd='restart'):
    """
    Command wrapper for msg subscriber daemon to log status.
    :param cmd: command to pass to the msg_subscriber daemon
                <start|stop|restart>
    """

    subscriber = 'msg_subscriber.py'

    logger.debug('Subscribing to node msgs: {}'.format(subscriber))
    res = control_daemon(cmd, script=subscriber)
    logger.debug('sub daemon response: {}'.format(res))

    return res


def wait_for_moon(timeout=15):
    """
    Wait for moon data on startup before sending any messages.
    Update state vars when we get moon data.
    :param timeout: Number of seconds to wait for the ``orbit`` command
                    to settle.  Note that it takes 8 or 9 seconds after
                    orbiting a new moon before moon data is returned.
    :return None:
    """
    import time
    from node_tools import state_data as st

    moons = NODE_SETTINGS['moon_list']
    for moon in moons:
        res = run_moon_cmd(moon, action='orbit')
        if res:
            break

    count = 0
    moon_metadata = run_ztcli_cmd(action='listmoons')

    while not len(moon_metadata) > 0 and count < timeout:
        count += 1
        time.sleep(1)
        moon_metadata = run_ztcli_cmd(action='listmoons')
        logger.debug('Moon data size: {}'.format(len(moon_metadata)))
    logger.debug('Moon sync took {} sec'.format(count))
    logger.debug('Moon data: {}'.format(moon_metadata))

    result = parse_moon_data(moon_metadata)
    logger.debug('Parse data returned: {}'.format(result))
    # logger.debug('st.fpnState data is: {}'.format(st.fpnState))

    if len(result) == 0:
        # raise an exception?
        raise MemberNodeError('moon result should not be empty!')
        # logger.error('moon result should not be empty: {}'.format(result))
    else:
        ident, addr, port = result[0]
        st.fpnState.update(moon_id0=ident, moon_addr=addr)
        logger.debug('moon state has id {} addr {}'.format(st.fpnState['moon_id0'],
                                                           st.fpnState['moon_addr']))
