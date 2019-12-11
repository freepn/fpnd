# coding: utf-8

"""Get data from a given node."""
import json
import platform

import asyncio
import aiohttp

from ztcli_api import ZeroTier
from ztcli_api import exceptions
from helper_funcs import get_token


async def main():
    """Example code to retrieve data from a ZeroTier node using tasks."""
    async with aiohttp.ClientSession() as session:
        ZT_API = get_token()
        client = ZeroTier(ZT_API, loop, session)

        try:
            # get status details of the local node
            await client.get_data('status')
            status_data = client.data
            print('Node: {}'.format(status_data.get('address')))

            # get status details of the node peers
            await client.get_data('peer')
            peer_data = client.data
            for peer in peer_data:
                print('Peer: {}'.format(peer.get('address')))

            # get/display all available network data
            await client.get_data('network')
            network_data = client.data
            for network in network_data:
                print('Network: {}'.format(network.get('id')))

        except exceptions.ZeroTierConnectionError:
            pass

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
