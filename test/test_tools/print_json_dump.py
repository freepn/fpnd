#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Target:   Python 3.6

import os
import json


data_dir = '/tmp/fpn_data'
endpoints = ['node', 'peers', 'moons', 'nets', 'nstate', 'mstate', 'istate']


# NOTE to use logging instead to pprint more general output
# import pprint/pformat and do something like this:
# from pprint import pprint
# from pprint import pformat
# logger.debug('pretty obj: \n{}'.format(pformat(obj, indent=2)))

# otherwise this works fine for printing json-ish data
def pprint(obj):
    print(json.dumps(obj, indent=4, separators=(',', ': ')))


def json_load_file(endpoint, dirname=None):

    def opener(dirname, flags):
        return os.open(dirname, flags, dir_fd=dir_fd)

    if dirname:
        dir_fd = os.open(dirname, os.O_RDONLY)
    else:
        opener = None

    with open(endpoint + '.json', 'r', opener=opener) as fp:
        data = json.load(fp)
    print('{} data read from {}.json'.format(endpoint, endpoint))
    return data


def dump_endpoint(endpoint, payload):
    """where payload is one data item"""
    json_dump = json.dumps(payload, indent=2, separators=(',', ': '))
    json_load = json.loads(json_dump)

    print('Payload type is: {}'.format(type(payload)))
    print('Dump type is: {}'.format(type(json_dump)))
    print('Load type is: {}'.format(type(json_load)))
    print('{} payload is:'.format(endpoint))
    pprint(payload)


def check_file(endpoint):
    list_data = json_load_file(endpoint, data_dir)

    if isinstance(list_data, dict):
        dump_endpoint(endpoint, list_data)
    else:
        for data in list_data:
            dump_endpoint(endpoint, data)


for endpoint in endpoints:
    print('Checking endpoint: {}'.format(endpoint))
    check_file(endpoint)
