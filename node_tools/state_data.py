# coding: utf-8

"""
    Default fpn node state data and changes.
    :var fpnState: built from cache data on each cache update
    :var changes: state diff tuple of fpnState changes
    :val route: state of outbound route to the internet
"""
from node_tools.timing_funcs import Cache as waitCache


# avoid repeatedly hammering infra nodes with wedged node msgs
wait_cache = waitCache()

defState = dict.fromkeys(['online',
                          'fpn_id',
                          'fpn_role',
                          'fallback',
                          'moon_id0',
                          'moon_addr',
                          'msg_ref',
                          'cfg_ref',
                          'fpn0',
                          'fpn1',
                          'fpn_id0',
                          'fpn_id1',
                          'route',
                          'wdg_ref'])

fpnState = {'online': False,
            'fpn_id': None,
            'fpn_role': None,
            'fallback': True,
            'moon_id0': None,
            'moon_addr': None,
            'msg_ref': None,
            'cfg_ref': None,
            'fpn0': False,
            'fpn1': False,
            'fpn_id0': None,
            'fpn_id1': None,
            'route': None,
            'wdg_ref': None}

leaf_nodes = []

cfg_msgs = {}

changes = []
