# coding: utf-8

"""Node-specific fpn helper functions."""
from __future__ import print_function

import logging

from node_tools.exceptions import MemberNodeError
from node_tools.helper_funcs import NODE_SETTINGS


logger = logging.getLogger(__name__)


def check_daemon(script=None):
    """
    Check status of a messaging daemon script
    :param script: daemon script (defaults to msg_responder.py)
    :return: boolean result or None for unknown status
    """

    if not script:
        cmd = control_daemon('status')
    else:
        cmd = control_daemon('status', script)

    res = cmd

    if 'False' in res.stdout:
        result = False
    elif 'True' in res.stdout:
        result = True
    else:
        result = None
        logger.error('ERROR: bad status result is'.format(res.stdout))
    return result


def control_daemon(action='status', script='msg_responder.py'):
    """
    Controller function for messaging daemon.
    :param action: one of <start|stop|restart>
    :param script: daemon script to control
    :return result: command result|False|None
    """
    import os
    import subprocess

    result = ''
    home = NODE_SETTINGS['home_dir']
    commands = ['start', 'stop', 'restart', 'status']
    daemon_file = os.path.join(home, script)

    if not os.path.isfile(daemon_file):
        result = None
    if action not in commands:
        result = False

    logger.debug('sending action {} to script: {}'.format(action, daemon_file))

    try:
        result = subprocess.run([daemon_file, action],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT,
                                universal_newlines=True,
                                check=True,
                                shell=False)
    except Exception as exc:
        logger.error('cmd exception: {}'.format(exc))
    # logger.debug('cmd {} got result: {}'.format(action, result.stdout))
    return result


def cycle_adhoc_net(nwid, nap=5):
    """
    Run the leave/join cycle on adhoc network ID
    """
    import time

    actions = ['leave', 'join']

    for act in actions:
        res = run_ztcli_cmd(action=act, extra=nwid)
        logger.debug('action {} returned: {}'.format(act, res))
        time.sleep(nap)


def do_cleanup(path=None):
    """
    Run network cleanup commands via daemon cleanup hook.
    :param path: path to scripts dir
    """
    from node_tools.helper_funcs import AttrDict
    from node_tools.network_funcs import do_net_cmd
    from node_tools.network_funcs import get_net_cmds

    from node_tools import state_data as st

    state = AttrDict.from_nested_dict(st.fpnState)
    moon_id = state.moon_id0
    if not path:
        path = NODE_SETTINGS['home_dir']
    nets = ['fpn_id0', 'fpn_id1']
    ifaces = ['fpn0', 'fpn1']

    for iface, net in zip(ifaces, nets):
        if state[iface]:
            logger.debug('CLEANUP: shutting down {}'.format(iface))
            cmd = get_net_cmds(path, iface)
            res = do_net_cmd(cmd)
            logger.debug('CLEANUP: leaving network ID: {}'.format(net))
            res = run_ztcli_cmd(action='leave', extra=state[net])
            logger.debug('CLEANUP: action leave returned: {}'.format(res))

    if moon_id is not None:
        run_moon_cmd(moon_id, action='deorbit')


def do_startup(nwid):
    """
    Run network startup command once before the state runner is
    available (if we have a network and interface up).
    """
    import time

    from node_tools.helper_funcs import AttrDict
    from node_tools.network_funcs import do_net_cmd
    from node_tools.network_funcs import get_net_cmds

    from node_tools import state_data as st

    run_ztcli_cmd(action='join', extra=nwid)
    # time.sleep(1)

    state = AttrDict.from_nested_dict(st.fpnState)
    fpn_home = NODE_SETTINGS['home_dir']
    nets = ['fpn_id0', 'fpn_id1']
    ifaces = ['fpn0', 'fpn1']

    for iface, net in zip(ifaces, nets):
        if st.fpnState[iface] and net == nwid:
            logger.debug('STARTUP: running setup on {}'.format(iface))
            cmd = get_net_cmds(fpn_home, iface, True)
            logger.debug('run_net_cmd using cmd: {}'.format(cmd))
            schedule.every(1).seconds.do(run_net_cmd, cmd).tag('net-change')


def handle_moon_data(data):
    """
    Handle moon data from wait_for_moon() and update state vars.
    :param data: list of moon data (one tuple per moon)
    """
    import time
    from node_tools import state_data as st

    moons = NODE_SETTINGS['moon_list']
    if len(data) == 0:
        # raise an exception?
        raise MemberNodeError('moon result should not be empty!')
        # logger.error('moon result should not be empty: {}'.format(result))
    elif len(data) > 0:
        for moon in data:
            ident, addr, port = moon
            if ident not in moons:
                res = run_moon_cmd(ident, action='deorbit')
                logger.debug('deorbit cmd returned: {}'.format(res))

    # time.sleep(2)

    for moon in data:
        ident, addr, port = moon
        if ident in moons:
            st.fpnState.update(moon_id0=ident, moon_addr=addr)
            logger.debug('moon state has id {} addr {}'.format(st.fpnState['moon_id0'],
                                                               st.fpnState['moon_addr']))


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
                # filter out IPv6 addresses for now
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
            logger.debug('{} on {} result: {}'.format(action, moon_id, out.decode().strip()))

    except Exception as exc:
        logger.error('zerotier-cli exception: {}'.format(exc))
        pass

    return result


def run_subscriber_daemon(cmd='start'):
    """
    Command wrapper for msg subscriber daemon to log status.
    :param cmd: command to pass to the msg_subscriber daemon
                <start|stop|restart>
    """

    subscriber = 'msg_subscriber.py'

    # logger.debug('Subscribing to node msgs: {}'.format(subscriber))
    res = control_daemon(cmd, script=subscriber)
    logger.debug('sub daemon retcode was: {}'.format(res.returncode))

    return res


def wait_for_moon(timeout=15):
    """
    Wait for moon data on startup before sending any messages.
    Update state vars when we get moon data.
    :param timeout: Number of seconds to wait for the ``orbit`` command
                    to settle.  Note that it takes 8 or 9 seconds after
                    orbiting a new moon before moon data is returned.
    :return data: parsed moon data (list of one tuple per moon)
    """
    import time

    moons = NODE_SETTINGS['moon_list']
    for moon in moons:
        res = run_moon_cmd(moon, action='orbit')
        if res:
            break
    time.sleep(2)

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
    return result
    # logger.debug('st.fpnState data is: {}'.format(st.fpnState))
