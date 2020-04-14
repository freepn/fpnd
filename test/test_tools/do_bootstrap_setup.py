#!/usr/bin/env python3

"""Get data from local ZT node API."""
import json
import time
import datetime
import string

import asyncio
import aiohttp

from diskcache import Index
from ztcli_api import ZeroTier
from ztcli_api import ZeroTierConnectionError as ZeroTierConnectionError

from node_tools.async_funcs import add_network_object
from node_tools.async_funcs import get_network_object_data
from node_tools.async_funcs import get_network_object_ids
from node_tools.cache_funcs import handle_node_status
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
            await client.get_data('status')
            print('Controller ID:')
            # pprint(client.data)
            node_id = handle_node_status(client.data, cache)
            print(node_id)

            # get/display all available network data
            await get_network_object_ids(client)
            print('{} networks found'.format(len(client.data)))
            if len(client.data) == 0:
                await add_network_object(client, ctlr_id=node_id)
                await get_network_object_ids(client)
            net_list = client.data
            net_data = []
            for net_id in net_list:
                print(net_id)
                # Get details about each network
                await get_network_object_data(client, net_id)
                pprint(client.data)
                net_data.append(client.data)
                await get_network_object_ids(client, net_id)
                # pprint(client.data)
                print('{} members found'.format(len(client.data)))
                if len(client.data) == 0:
                    await add_network_object(client, net_id, exit_node)
                    await get_network_object_ids(client, net_id)
                member_dict = client.data
                for mbr_id in member_dict.keys():
                    await get_network_object_data(client, net_id, mbr_id)
                    pprint(client.data)

        except Exception as exc:
            # print(str(exc))
            raise exc

exit_node = 'ddfd7368e6'
cache = Index(get_cachedir())
loop = asyncio.get_event_loop()
loop.run_until_complete(main())
