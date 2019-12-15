# coding: utf-8

"""Miscellaneous helper functions."""
from __future__ import print_function

import ztcli_api
from ztcli_api import ZeroTierConnectionError as ZeroTierConnectionError


class Constant(tuple):
    "Pretty display of immutable constant."
    def __new__(cls, name):
        return tuple.__new__(cls, (name,))

    def __repr__(self):
        return '%s' % self[0]

# error return for async state data updates
ENODATA = Constant('ENODATA')

NODE_SETTINGS = {
    u'max_cache_age': 300,  # maximum cache age in seconds
}

def exec_full(filepath):
    import os
    global_namespace = {
        "__file__": filepath,
        "__name__": "__main__",
    }
    with open(filepath, 'rb') as file:
        exec(compile(file.read(), filepath, 'exec'), global_namespace)

def get_cachedir():
    """Get state cachedir according to OS (creates it if needed)"""
    import os
    import tempfile
    temp_dir = tempfile.gettempdir()
    cache_dir = os.path.join(temp_dir,'fpn_state')
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
        return "C:\ProgramData\ZeroTier\One"


def get_token():
    """Get authentication token (requires root or user acl)"""
    with open(get_filepath()+"/authtoken.secret") as file:
        auth_token = file.read()
    return auth_token


def json_check(data):
    import json
    print('Data type is: {}'.format(type(data)))

    json_dump = json.dumps(data, indent=4, separators=(',', ': '))
    json_load = json.loads(json_dump)
    assert data == json_load
    print('Dump type is: {}'.format(type(json_dump)))
    print('Load type is: {}'.format(type(json_load)))
    print('Format is JSON:')
    json_pprint(json_load)


def json_pprint(obj):
    import json
    print(json.dumps(obj, indent=2, separators=(',', ': ')))


def json_to_obj(data):
    import json

    try:
        from types import SimpleNamespace as Namespace
    except ImportError:
        from argparse import Namespace

    return json.loads(data, object_hook=lambda d: Namespace(**d))


def update_state():
    import pathlib
    here = pathlib.Path(__file__).parent
    node_scr = here.joinpath("nodestate.py")
    try:
        exec_full(node_scr)
        return 'OK'
    except ZeroTierConnectionError as exc:
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
