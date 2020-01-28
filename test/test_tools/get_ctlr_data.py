#!/usr/bin/env python3

"""Get data from local ZT node API."""
import json
import time
import datetime
import string
import random

import asyncio
import aiohttp

from diskcache import Index
from ztcli_api import ZeroTier
from ztcli_api import ZeroTierConnectionError as ZeroTierConnectionError

from node_tools.cache_funcs import find_keys
from node_tools.cache_funcs import load_cache_by_type
from node_tools.helper_funcs import get_cachedir
from node_tools.helper_funcs import get_token


# time.sleep(1)

def timerfunc(func):
    """
    A timer decorator
    """
    def function_timer(*args, **kwargs):
        """
        A nested function for timing other functions
        """
        start = time.process_time()
        value = func(*args, **kwargs)
        end = time.process_time()
        runtime = end - start
        msg = "The runtime for {func} took {time} sec to complete"
        print(msg.format(func=func.__name__,
                         time=runtime))
        return value
    return function_timer


def name_generator(size=10, chars=string.ascii_lowercase + string.digits):
    str1 = ''.join(random.choice(chars) for _ in range(size))
    str2 = ''.join(random.choice(chars) for _ in range(size))
    return str1 + '_' + str2


def pprint(obj):
    print(json.dumps(obj, indent=2, separators=(',', ': ')))


# @timerfunc
async def main():
    """Retrieve data from and manipulate a ZeroTier controller node."""
    async with aiohttp.ClientSession() as session:
        ZT_API = get_token()
        client = ZeroTier(ZT_API, loop, session)

        try:
            # get status details of the controller node
            # await client.get_data('controller')
            # print('Controller status:')
            # pprint(client.data)
            # print(client.data.get('controller'))

            # get status details of the node peers
            await client.get_data('peer')
            # print('Peers found:')
            # pprint(client.data)
            peer_data = client.data
            peer_keys = find_keys(cache, 'peer')
            print('Returned peer keys: {}'.format(peer_keys))
            load_cache_by_type(cache, peer_data, 'peer')

            # get/display all available network data
            await client.get_data('controller/network')
            print('{} networks found'.format(len(client.data)))
            net_list = client.data
            net_data = []
            for net_id in net_list:
                # print(net_id)
                # Get details about each network
                await client.get_data('controller/network/{}'.format(net_id))
                # pprint(client.data)
                net_data.append(client.data)

            # load_cache_by_type(cache, net_data, 'net')
            # net_keys = find_keys(cache, 'net')
            # print('{} network keys found'.format(len(net_list)))
            # pprint(net_data)

        except Exception as exc:
            # print(str(exc))
            raise exc

cache = Index(get_cachedir(dir_name='ctlr_data'))
# cache.clear()
loop = asyncio.get_event_loop()
loop.run_until_complete(main())
