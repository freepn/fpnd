# coding: utf-8

"""
    Default fpn node state data and changes.
    :var fpnState: built from cache data on each cache update
    :var changes: state diff tuple of fpnState changes
"""

defState = dict.fromkeys(['online',
                          'fpn_id',
                          'fpn_role',
                          'fallback',
                          'moon_id0',
                          'moon_addr',
                          'moon_ref0',
                          'fpn0',
                          'fpn1',
                          'fpn_id0',
                          'fpn_id1'])

fpnState = {'online': False,
            'fpn_id': None,
            'fpn_role': None,
            'fallback': True,
            'moon_id0': None,
            'moon_addr': None,
            'moon_ref0': None,
            'fpn0': False,
            'fpn1': False,
            'fpn_id0': None,
            'fpn_id1': None}

changes = []
