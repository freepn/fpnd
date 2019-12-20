# coding: utf-8

"""Get data from local ZeroTier node using async client session."""
import asyncio
import aiohttp
import logging

from diskcache import Index
from ztcli_api import ZeroTier
from ztcli_api import ZeroTierConnectionError
from node_tools.cache_funcs import update_node_data, update_peer_data
from node_tools.cache_funcs import find_key
from node_tools.helper_funcs import get_token, get_cachedir, AttrDict


logger = logging.getLogger(__name__)


async def main():
    """State cache updater to retrieve data from a local ZeroTier node."""
    async with aiohttp.ClientSession() as session:
        ZT_API = get_token()
        client = ZeroTier(ZT_API, loop, session)

        try:
            # get status details of the local node
            await client.get_data('status')
            node_data = client.data
            node_id = node_data.get('address')
            logger.info('Found node: {}'.format(node_id))
            # status = AttrDict.from_nested_dict(node_data)
            update_node_data(cache, node_data)
            node_key = find_key(cache, 'node')
            print('Returned node key is: {}'.format(node_key))

            # get status details of the node peers
            await client.get_data('peer')
            peer_data = client.data
            logger.info('Found {} peers'.format(len(peer_data)))
            update_peer_data(cache, peer_data)
            active_peers = (peer for peer in peer_data)
            cached_peers = (peer for peer in list(cache))
            active_list = []
            for peer in active_peers:
                peer_status = AttrDict.from_nested_dict(peer)
                peer_id = peer.get('address')
                active_list.append(peer_id)
                if peer_id in cache:
                    logger.info('Updating peer {}'.format(peer_id))
                    cache.update([(peer_id, peer_status)])
                elif peer_id not in cache:
                    logger.info('Adding peer {}'.format(peer_id))
                    cache.update([(peer_id, peer_status)])
            for peer_id in cached_peers:
                if (peer_id != node_id and len(peer_id) == 10 and peer_id not in active_list):
                    logger.info('Removing peer: {}'.format(peer_id))
                    try:
                        del cache[peer_id]
                    except KeyError:
                        logger.error('Key {} not found'.format(peer_id))

            # get all available network data
            await client.get_data('network')
            active_nets = (net for net in client.data)
            cached_nets = (net for net in list(cache))
            active_nets = []
            for net in active_nets:
                net_status = AttrDict.from_nested_dict(net)
                net_id = net.get('id')
                active_nets.append(net_id)
                if net_id in cache:
                    logger.info('Updating network: {}'.format(net_id))
                    cache.update([(net_id, net_status)])
                elif net_id not in cache:
                    logger.info('Adding network: {}'.format(net_id))
                    cache.update([(net_id, net_status)])
            for net_id in cached_nets:
                if (len(net_id) == 16 and net_id not in active_nets):
                    logger.info('Removing net: {}'.format(net_id))
                    try:
                        del cache[net_id]
                    except KeyError:
                        logger.error('Key {} not found'.format(net_id))

        except ZeroTierConnectionError as exc:
            logger.error(str(exc))
            raise exc


cache = Index(get_cachedir())
loop = asyncio.get_event_loop()
loop.run_until_complete(main())
