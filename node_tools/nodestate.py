# coding: utf-8

"""Get data from local ZeroTier node using async client session."""
import asyncio
import aiohttp
import logging

from diskcache import Index
from ztcli_api import ZeroTier
from ztcli_api import ZeroTierConnectionError

from node_tools.cache_funcs import find_keys
from node_tools.cache_funcs import get_net_status
from node_tools.cache_funcs import get_node_status
from node_tools.cache_funcs import get_peer_status
from node_tools.cache_funcs import load_cache_by_type
from node_tools.helper_funcs import get_cachedir
from node_tools.helper_funcs import get_token
from node_tools.node_funcs import get_moon_data
# from node_tools.helper_funcs import json_dump_file
# from node_tools.helper_funcs import json_load_file


logger = logging.getLogger('nodestate')


async def main():
    """State cache updater to retrieve data from a local ZeroTier node."""
    async with aiohttp.ClientSession() as session:
        ZT_API = get_token()
        client = ZeroTier(ZT_API, loop, session)
        # data_dir = get_cachedir(dir_name='fpn_data')

        try:
            # get status details of the local node
            await client.get_data('status')
            node_data = client.data
            node_id = node_data.get('address')
            logger.info('Found node: {}'.format(node_id))
            node_key = find_keys(cache, 'node')
            logger.debug('Returned {} key is: {}'.format('node', node_key))
            load_cache_by_type(cache, node_data, 'node')

            # get status details of the node peers
            await client.get_data('peer')
            peer_data = client.data
            logger.info('Found {} peers'.format(len(peer_data)))
            peer_keys = find_keys(cache, 'peer')
            logger.debug('Returned peer keys: {}'.format(peer_keys))
            load_cache_by_type(cache, peer_data, 'peer')

            # check for moon data (only exists for moons we orbit)
            moon_data = get_moon_data()
            if moon_data:
                load_cache_by_type(cache, moon_data, 'moon')

            # get all available network data
            await client.get_data('network')
            net_data = client.data
            logger.info('Found {} networks'.format(len(net_data)))
            net_keys = find_keys(cache, 'net')
            logger.debug('Returned network keys: {}'.format(net_keys))
            load_cache_by_type(cache, net_data, 'net')

            # if we get here, we can update our state objects
            nodeStatus = get_node_status(cache)
            logger.debug('Got node state: {}'.format(nodeStatus))
            load_cache_by_type(cache, nodeStatus, 'nstate')
            moonStatus = []
            peerStatus = get_peer_status(cache)
            for peer in peerStatus:
                if peer['role'] == 'MOON':
                    moonStatus.append(peer)
                    break
            logger.debug('Got moon state: {}'.format(moonStatus))
            load_cache_by_type(cache, moonStatus, 'mstate')
            netStatus = get_net_status(cache)
            logger.debug('Got net state: {}'.format(netStatus))
            load_cache_by_type(cache, netStatus, 'istate')

        except ZeroTierConnectionError as exc:
            logger.error(str(exc))
            raise exc


cache = Index(get_cachedir())
loop = asyncio.get_event_loop()
loop.run_until_complete(main())
