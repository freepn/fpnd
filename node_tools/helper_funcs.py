# coding: utf-8

"""Miscellaneous helper functions."""
from __future__ import print_function

import sys
import logging

from configparser import ConfigParser as SafeConfigParser


logger = logging.getLogger(__name__)


class Constant(tuple):
    "Pretty display of immutable constant."
    def __new__(cls, name):
        return tuple.__new__(cls, (name,))

    def __repr__(self):
        return '%s' % self[0]


ENODATA = Constant('ENODATA')  # error return for async state data updates

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
    u'nwid': None  # adhoc mode network ID goes here
}


def config_from_ini(file_path=None):
    config = SafeConfigParser(allow_no_value=True)
    candidates = ['/etc/fpnd.ini',
                  '/etc/fpnd/fpnd.ini',
                  '/usr/lib/fpnd/fpnd.ini',
                  'test/test_data/settings.ini',
                  ]
    if file_path:
        candidates.append(file_path)
    found = config.read(candidates)

    if not found:
        message = 'No usable cfg found, files in /tmp/ dir.'
        return False, message

    for tgt_ini in found:
        if 'fpnd' in tgt_ini:
            message = 'Found system settings...'
            return config, message
        if 'settings' in tgt_ini and config.has_option('Options', 'prefix'):
            message = 'Found local settings...'
            config['Paths']['log_path'] = ''
            config['Paths']['pid_path'] = ''
            config['Options']['prefix'] = 'local_'
            return config, message


def do_setup():
    import os

    my_conf, msg = config_from_ini()
    if my_conf:
        role = my_conf['Options']['role']
        mode = my_conf['Options']['mode']
        debug = my_conf.getboolean('Options', 'debug')
        home = my_conf['Paths']['home_dir']
        NODE_SETTINGS['mode'] = mode
        NODE_SETTINGS['debug'] = debug
        NODE_SETTINGS['home_dir'] = home
        if 'system' not in msg:
            prefix = my_conf['Options']['prefix']
        else:
            prefix = ''
        pid_path = my_conf['Paths']['pid_path']
        log_path = my_conf['Paths']['log_path']
        pid_file = my_conf['Options']['pid_name']
        log_file = my_conf['Options']['log_name']
        pid = os.path.join(pid_path, prefix, pid_file)
        log = os.path.join(log_path, prefix, log_file)

    else:
        home = None
        debug = False
        pid = '/tmp/fpnd.pid'
        log = '/tmp/fpnd.log'
    return home, pid, log, debug, msg, mode, role


def exec_full(filepath):
    global_namespace = {
        "__file__": filepath,
        "__name__": "__main__",
    }
    with open(filepath, 'rb') as file:
        exec(compile(file.read(), filepath, 'exec'), global_namespace)


def find_ipv4_iface(addr_string, strip=True):
    """
    This is intended mainly for picking the IPv4 address from the list
    of 'assignedAddresses' in the JSON network data payload for a
    single ZT network.
    :param addr_string: IPv4 address in CIDR format
                            eg: 192.168.1.10/24
    :param strip: check addr or return bare addr string
    :return addr: Stripped addr_str if 'strip' return IPv4 addr only, or
    :return boolean: True if not 'strip' or False if addr not valid
    """
    import ipaddress
    try:
        interface = ipaddress.IPv4Interface(addr_string)
        if not strip:
            return True
        else:
            return str(interface.ip)
    except ValueError:
        return False


def get_cachedir(dir_name='fpn_cache'):
    """
    Get temp cachedir according to OS (create it if needed)
    * override the dir_name arg for non-cache data
    """
    import os
    import tempfile
    temp_dir = tempfile.gettempdir()
    cache_dir = os.path.join(temp_dir, dir_name)
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
    return cache_dir


def get_filepath():
    import platform
    """Get default ZeroTier HOME filepath according to OS."""
    if platform.system() == "Linux":
        return "/var/lib/zerotier-one"
    elif platform.system() == "Darwin":
        return "/Library/Application Support/ZeroTier/One"
    elif platform.system() == "FreeBSD" or platform.system() == "OpenBSD":
        return "/var/db/zerotier-one"
    elif platform.system() == "Windows":
        return "C:\\ProgramData\\ZeroTier\\One"


def get_token(zt_home=None):
    """Get ZeroTier authentication token (requires root or user acl)."""
    if not zt_home:
        zt_home = get_filepath()
    with open(zt_home + "/authtoken.secret") as file:
        auth_token = file.read()
    return auth_token


def json_dump_file(endpoint, data, dirname=None):
    import os
    import json

    def opener(dirname, flags):
        return os.open(dirname, flags, mode=0o600, dir_fd=dir_fd)

    if dirname:
        dir_fd = os.open(dirname, os.O_RDONLY)
    else:
        opener = None

    with open(endpoint + '.json', 'w', opener=opener) as fp:
        json.dump(data, fp)
    logger.debug('{} data in {}.json'.format(endpoint, endpoint))


def json_load_file(endpoint, dirname=None):
    import os
    import json

    def opener(dirname, flags):
        return os.open(dirname, flags, dir_fd=dir_fd)

    if dirname:
        dir_fd = os.open(dirname, os.O_RDONLY)
    else:
        opener = None

    with open(endpoint + '.json', 'r', opener=opener) as fp:
        data = json.load(fp)
    logger.debug('{} data read from {}.json'.format(endpoint, endpoint))
    return data


def log_fpn_state(diff=None):
    if diff is None:
        from node_tools import state_data as st
        diff = st.changes

    if diff:
        for iface, state in diff:
            if iface in ['fpn0', 'fpn1']:
                if state:
                    logger.info('{} is UP'.format(iface))
                else:
                    logger.info('{} is DOWN'.format(iface))


def net_change_handler(iface, state):
    """
    Net change event handler for configuring fpn network devices
    (calls net cmds for a given interface/state).  Schedules a new
    run_net_cmd() job for each change event.
    :param iface: <'fpn0'|'fpn1'> fpn interface to act on
    :param state: <True|False> new iface state, ie, up|down
    """
    import schedule
    from node_tools.network_funcs import get_net_cmds
    from node_tools.network_funcs import run_net_cmd

    fpn_home = NODE_SETTINGS['home_dir']
    cmd = get_net_cmds(fpn_home, iface, state)

    if cmd:
        if NODE_SETTINGS['mode'] == 'adhoc' and NODE_SETTINGS['nwid']:
            cmd.append(NODE_SETTINGS['nwid'])
        logger.debug('run_net_cmd using cmd: {}'.format(cmd))
        schedule.every(1).seconds.do(run_net_cmd, cmd).tag('net-change')
    else:
        logger.error('get_net_cmds returned None')
        # raise Exception('Missing command return from get_net_cmds()!')


def run_event_handlers(diff=None):
    """
    Run state change event handlers (currently just the net handler)
    :param diff: State change diff, ie, st.changes
    """
    if diff is None:
        from node_tools import state_data as st
        diff = st.changes

    if diff:
        for iface, state in diff:
            if iface in ['fpn0', 'fpn1']:
                logger.debug('running net_change_handler for iface {} and state {}'.format(iface, state))
                net_change_handler(iface, state)


def send_announce_msg(fpn_id, addr, send_cfg=False):
    """
    Send node announcement message (hey, this is my id).
    """
    import schedule
    from node_tools.network_funcs import echo_client

    if fpn_id:
        if send_cfg:
            logger.debug('CFG: Sending cfg msg: {} to addr {}'.format(fpn_id, addr))
            schedule.every(3).seconds.do(echo_client, fpn_id, addr, send_cfg=True).tag('need-net')
        else:
            logger.debug('MSG: Sending msg: {} to addr {}'.format(fpn_id, addr))
            schedule.every(1).seconds.do(echo_client, fpn_id, addr).tag('hey-moon')


def send_cfg_handler():
    """
    Event handler for cfg request message (somewhat analogous to the
    startup_handlers func).  Runs *after* the announce msg succeeds.
    """
    from node_tools import state_data as st

    nsState = AttrDict.from_nested_dict(st.fpnState)
    addr = nsState.moon_addr

    if NODE_SETTINGS['use_localhost'] or not addr:
        addr = '127.0.0.1'

    if nsState.msg_ref:
        try:
            send_announce_msg(nsState.fpn_id, addr, send_cfg=True)
        except Exception as exc:
            logger.warning('send_cfg_msg exception: {}'.format(exc))
    else:
        logger.error('CFG: missing msg ref for {}'.format(nsState.fpn_id))


def set_initial_role():
    """
    Set initial node role from node ID if ID is a known infra node.
    """
    from node_tools.node_funcs import run_ztcli_cmd

    try:
        res = run_ztcli_cmd(action='info')
        if res:
            node_data = res.split()
            logger.debug('INITNODE: node data is {}'.format(node_data))

            if NODE_SETTINGS['mode'] == 'peer':
                node_id = node_data[2]
                if node_id in NODE_SETTINGS['moon_list']:
                    NODE_SETTINGS['node_role'] = 'moon'
                elif node_id in NODE_SETTINGS['ctlr_list']:
                    NODE_SETTINGS['node_role'] = 'controller'
            logger.debug('INITROLE: role is {}'.format(NODE_SETTINGS['node_role']))
            logger.debug('INITMODE: mode is {}'.format(NODE_SETTINGS['mode']))

    except Exception as exc:
        logger.warning('run_ztcli_cmd exception: {}'.format(exc))


def startup_handlers():
    """
    Event handlers that need to run at, well, startup (currently only
    the node announcement message).
    """
    from node_tools import state_data as st

    addr = None
    nsState = AttrDict.from_nested_dict(st.fpnState)

    if nsState.moon_id0 in NODE_SETTINGS['moon_list']:
        addr = nsState.moon_addr
    if NODE_SETTINGS['use_localhost'] or not addr:
        addr = '127.0.0.1'

    try:
        send_announce_msg(nsState.fpn_id, addr)
    except Exception as exc:
        logger.warning('send_announce_msg exception: {}'.format(exc))


def update_state(scr=None):
    import pathlib

    if not scr:
        scr = NODE_SETTINGS['node_runner']

    here = pathlib.Path(__file__).parent
    node_scr = here.joinpath(scr)

    try:
        exec_full(node_scr)
        return 'OK'
    except Exception as exc:
        logger.warning('{} exception: {}'.format(scr, exc))
        return ENODATA


def validate_role():
    """
    Validate and set initial role with state data from the cache.
    """
    from node_tools import state_data as st
    nodeState = AttrDict.from_nested_dict(st.fpnState)

    if NODE_SETTINGS['mode'] == 'peer':
        if nodeState.fpn_id in NODE_SETTINGS['moon_list']:
            NODE_SETTINGS['node_role'] = 'moon'
            NODE_SETTINGS['node_runner'] = 'peerstate.py'
        elif nodeState.fpn_id in NODE_SETTINGS['ctlr_list']:
            NODE_SETTINGS['node_role'] = 'controller'
            NODE_SETTINGS['node_runner'] = 'netstate.py'
        else:
            NODE_SETTINGS['node_role'] = None
    elif NODE_SETTINGS['mode'] == 'adhoc':
        NODE_SETTINGS['node_role'] = None
        if NODE_SETTINGS['use_exitnode'] == []:
            logger.warning('No adhoc node IDs found in NODE_SETTINGS.')
            logger.warning('Follow the initial setup docs for adhoc mode.')
    st.fpnState['fpn_role'] = NODE_SETTINGS['node_role']
    logger.debug('ROLE: validated role is {}'.format(st.fpnState['fpn_role']))


def xform_state_diff(diff):
    """
    Function to extract and transform state diff type to a new
    dictionary (this means the input must be non-empty). Note the
    object returned is mutable!
    :caveats: if returned k,v are tuples of (old, new) state values
              the returned keys are prefixed with `old_` and `new_`
    :param diff: state_data.changes obj (list of tuples with state changes)
    :return AttrDict: dict with state changes (with attribute access)
    """

    d = {}
    if not diff:
        return d

    for item in diff:
        if isinstance(item, tuple) or isinstance(item, list):
            if isinstance(item[0], str):
                d[item[0]] = item[1]
            elif isinstance(item[0], tuple):
                # we know we have duplicate keys so make new ones
                # using 'old_' and 'new_' prefix
                old_key = 'old_' + item[0][0]
                d[old_key] = item[0][1]
                new_key = 'new_' + item[1][0]
                d[new_key] = item[1][1]

    return AttrDict.from_nested_dict(d)


class AttrDict(dict):
    """ Dictionary subclass whose entries can be accessed by attributes
        (as well as normally).
    """
    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self

    @staticmethod
    def from_nested_dict(data):
        """ Construct nested AttrDicts from nested dictionaries. """
        if not isinstance(data, dict):
            return data
        else:
            return AttrDict({key: AttrDict.from_nested_dict(data[key])
                             for key in data})
