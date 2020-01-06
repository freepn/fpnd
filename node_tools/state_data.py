# coding: utf-8

"""Default fpn node state data and changes."""

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

changes = []
