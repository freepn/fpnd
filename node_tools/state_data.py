# coding: utf-8

"""
    Default fpn node state data and changes.
    :var fpnState: built from cache data on each cache update
    :var changes: state diff tuple of fpnState changes
    :var fpnRegState: set on startup on successful node registration
"""

defState = dict.fromkeys(['online',
                          'fpn_id',
                          'fallback',
                          'moon_id0',
                          'moon_addr',
                          'fpn0',
                          'fpn1',
                          'fpn_id0',
                          'fpn_id1'])

fpnState = {'online': False,
            'fpn_id': None,
            'fallback': True,
            'moon_id0': None,
            'moon_addr': None,
            'fpn0': False,
            'fpn1': False,
            'fpn_id0': None,
            'fpn_id1': None}

fpnRegState = {'registered': False,
               'moon_result': None,
               'moon_ref': None}

changes = []
