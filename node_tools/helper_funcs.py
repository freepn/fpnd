# coding: utf-8

"""Miscellaneous helper functions."""
from __future__ import print_function

import sys
import logging

if sys.hexversion >= 0x3020000:
    from configparser import ConfigParser as SafeConfigParser
else:
    from configparser import SafeConfigParser


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
    u'moon_list': ['4f4114472a'],  # list of fpn moons to orbiit
    u'home_dir': None,
    u'debug': False
}


def config_from_ini(file_path=None):
    config = SafeConfigParser()
    candidates = ['/etc/fpnd.ini',
                  '/etc/fpnd/fpnd.ini',
                  '/usr/lib/fpnd/fpnd.ini',
                  'member_settings.ini',
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
        if 'member' in tgt_ini and config.has_option('Options', 'prefix'):
            message = 'Found local settings...'
            config['Paths']['log_path'] = ''
            config['Paths']['pid_path'] = ''
            config['Options']['prefix'] = 'local_'
            return config, message


def do_setup():
    import os

    my_conf, msg = config_from_ini()
    if my_conf:
        debug = my_conf.getboolean('Options', 'debug')
        home = my_conf['Paths']['home_dir']
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
    return home, pid, log, debug, msg


def exec_full(filepath):
    global_namespace = {
        "__file__": filepath,
        "__name__": "__main__",
    }
    with open(filepath, 'rb') as file:
        exec(compile(file.read(), filepath, 'exec'), global_namespace)


def find_ipv4_iface(addr_string, strip=True):
    """
    This is intended only for picking the IPv4 address from the list
    of 'assignedAddresses' in the JSON network data payload for a
    single ZT network.
    :param addr_string: IPv4 address in CIDR format
                            eg: 192.168.1.10/24
    :param strip:
    :return stripped addr_str: if 'strip' return IPv4 addr only, or
    :return True: if not 'strip' or False if addr not valid
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
    """Get filepath according to OS"""
    if platform.system() == "Linux":
        return "/var/lib/zerotier-one"
    elif platform.system() == "Darwin":
        return "/Library/Application Support/ZeroTier/One"
    elif platform.system() == "FreeBSD" or platform.system() == "OpenBSD":
        return "/var/db/zerotier-one"
    elif platform.system() == "Windows":
        return "C:\\ProgramData\\ZeroTier\\One"


def get_token():
    """Get authentication token (requires root or user acl)"""
    with open(get_filepath()+"/authtoken.secret") as file:
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


def log_fpn_state():
    from node_tools import state_data as st
    if st.changes:
        for iface, state in st.changes:
            if iface in ['fpn0', 'fpn1']:
                if state:
                    logger.info('{} is UP'.format(iface))
                else:
                    logger.info('{} is DOWN'.format(iface))


def update_state():
    import pathlib
    here = pathlib.Path(__file__).parent
    node_scr = here.joinpath("nodestate.py")
    try:
        exec_full(node_scr)
        return 'OK'
    except Exception as exc:
        logger.error('update_state exception: {}'.format(exc))
        return ENODATA


def xform_state_diff(diff):
    """
    Function to extract and transform state diff type to a new
    dictionary (this means the input must be non-empty). Note the
    object returned is mutable!
    :caveats: if returned k,v are tuples of (old, new) state values
              the returned keys are prefixed with `old_` and `new_`
    :param state_data.changes obj: list of tuples with state changes
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
