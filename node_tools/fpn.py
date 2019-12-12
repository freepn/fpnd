#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Target:   Python 3.6

#import asyncio
#import helper_funcs
import json
from diskcache import Index
from node_tools.helper_funcs import update_state, get_cachedir, json_pprint

cache = Index(get_cachedir())

update_state()

node_id, node_status = cache.peekitem(last=False)
print('I am {}'.format(node_id))
print('My online state is: {}'.format(node_status.online))

json_pprint(node_status.config.settings)

print('Data type is: {}'.format(type(node_status)))

json_dump = json.dumps(node_status, indent=2, separators=(',', ': '))
json_load = json.loads(json_dump)

print('Dump type is: {}'.format(type(json_dump)))
print('Load type is: {}'.format(type(json_load)))
print('Format is JSON (python)')

json_pprint(json_load)
