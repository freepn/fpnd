#!/usr/bin/env python3

"""Get data from local ZT node API."""
import json
import time
import datetime
import string
import random

import asyncio
import aiohttp

# from diskcache import Index
from ztcli_api import ZeroTier
from ztcli_api import ZeroTierConnectionError as ZeroTierConnectionError

from node_tools.cache_funcs import find_keys
from node_tools.helper_funcs import get_cachedir
from node_tools.helper_funcs import get_token


# time.sleep(1)

def name_generator(size=10, chars=string.ascii_lowercase + string.digits):
    str1 = ''.join(random.choice(chars) for _ in range(size))
    str2 = ''.join(random.choice(chars) for _ in range(size))
    return str1 + '_' + str2


def pprint(obj):
    print(json.dumps(obj, indent=2, separators=(',', ': ')))


async def main():
    """
    Generate a bunch of networks on a ZeroTier controller node.
    """
    async with aiohttp.ClientSession() as session:
        ZT_API = get_token()
        client = ZeroTier(ZT_API, loop, session)

        try:
            await client.get_data('status')
            node_data = client.data
            ctlr_id = node_data.get('address')

            # create some networks
            endpoint = 'controller/network/{}'.format(ctlr_id + '______')
            for N in range(1000):
                net_name = name_generator()
                await client.set_value('name', net_name, endpoint)

            # await client.get_data('network/{}'.format(my_id))
            # print(network.get('allowGlobal'))

            # get/display all available network data
            await client.get_data('controller/network')
            print('{} networks found'.format(len(client.data)))
            # pprint(client.data)

        except ZeroTierConnectionError as exc:
            print(str(exc))
            pass

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
