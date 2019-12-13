#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Target:   Python 3.6

#import asyncio
#import helper_funcs
import json

from diskcache import Index

from ztcli_api import exceptions
from node_tools.helper_funcs import update_state, get_cachedir, json_pprint

cache = Index(get_cachedir())
size = len(cache)
print('{} items currently in cache.'.format(size))
#print('{}'.format(list(cache)))

try:
    update_state()
except exceptions.ZeroTierNoDataAvailable:
    print('No data available, cache was NOT updated')
    #exit(0)

size = len(cache)
print('{} items now in cache.'.format(size))
#print(list(cache))

node_id, node_status = cache.peekitem(last=False)
print('My ID is: {}'.format(node_id))
print('My online state is: {}'.format(node_status.online))

#json_pprint(node_status.config.settings)

#print('Data type is: {}'.format(type(node_status)))

#json_dump = json.dumps(node_status, indent=2, separators=(',', ': '))
#json_load = json.loads(json_dump)

#print('Dump type is: {}'.format(type(json_dump)))
#print('Load type is: {}'.format(type(json_load)))
#print('Format is JSON (python)')

#json_pprint(json_load)

id, status = cache.peekitem(last=True)

if len(str(id)) == 10 and id != node_id:
    print('I have a peer {}'.format(id))
    print('Peer role is: {}'.format(status.role))
    peer_addr = status.paths[0]['address'].split('/', maxsplit=1)
    print('Peer endpoint is: {}'.format(peer_addr[0]))
    print('I have no networks  :(')
    #json_pprint(status.paths)
else:
    print('Net ID: {}'.format(id))
    print('Status: {}'.format(status.status))
    print('Device: {}'.format(status.portDeviceName))
    zt_addr = status.assignedAddresses[1].split('/', maxsplit=1)
    print('Address: {}'.format(zt_addr[0]))
    #json_pprint(status.routes)
