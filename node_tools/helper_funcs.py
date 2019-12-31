# coding: utf-8

"""Miscellaneous helper functions."""
from __future__ import print_function

import logging


logger = logging.getLogger(__name__)


class Constant(tuple):
    "Pretty display of immutable constant."
    def __new__(cls, name):
        return tuple.__new__(cls, (name,))

    def __repr__(self):
        return '%s' % self[0]


ENODATA = Constant('ENODATA')  # error return for async state data updates

NODE_SETTINGS = {
    u'max_cache_age': 300,  # maximum cache age in seconds
    u'moon_list': ['4f4114472a']  # list of fpn moons to orbiit
}


def exec_full(filepath):
    global_namespace = {
        "__file__": filepath,
        "__name__": "__main__",
    }
    with open(filepath, 'rb') as file:
        exec(compile(file.read(), filepath, 'exec'), global_namespace)


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


def update_state():
    import pathlib
    here = pathlib.Path(__file__).parent
    node_scr = here.joinpath("nodestate.py")
    try:
        exec_full(node_scr)
        return 'OK'
    except Exception as exc:
        return ENODATA
        logger.error(str(exc))


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
