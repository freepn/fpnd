#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Target:   Python 3.6

import json

from diskcache import Index
from node_tools import get_cachedir, get_node_status, update_state


def get_node_data(cache, key_str):
    """Get data for first node[type] from cache."""
    from node_tools import find_keys
    if len(cache):
        key_list = find_keys(cache, key_str)
        node_key = key_list[0]
        data = cache[node_key]
        if 'net' in key_str:
            tgt = 'id'
        else:
            tgt = 'address'
        return data.get(tgt), data
    else:
        return None, None


cache = Index(get_cachedir())
# cache.clear()

size = len(cache)
print('{} items currently in cache.'.format(size))
print('Cache items: {}'.format(list(cache)))

try:
    res = update_state()
    size = len(cache)
except:  # noqa: E722
    print('No data available, cache was NOT updated')
else:
    if size < 1:
        print('No data available (live or cached)')
        exit(1)

print('Get data result: {}'.format(res))
node_id, node_data = get_node_data(cache, 'node')

if node_id is not None:
    json_dump = json.dumps(node_data, indent=2, separators=(',', ': '))
    json_load = json.loads(json_dump)

    print('Dump type is: {}'.format(type(json_dump)))
    print('Load type is: {}'.format(type(json_load)))
    print('ID is: {}'.format(node_id))
    print('Payload is: {}'.format(node_data))

if size > 0:
    size = len(cache)
    print('{} items now in cache.'.format(size))
    print('Cache items: {}'.format(list(cache)))
    Node = get_node_status(cache)
    print('Node status: {}'.format(Node))

else:
    print('Cache empty and API returned ENODATA')
