# coding: utf-8

"""Get data from a given node."""
import asyncio
import aiohttp
import logging

from diskcache import Index
from ztcli_api import ZeroTier
from ztcli_api import exceptions
from node_tools.helper_funcs import get_token, get_cachedir, AttrDict

logger = logging.getLogger(__name__)


async def main():
    """Example code to retrieve data from a ZeroTier node using tasks."""
    async with aiohttp.ClientSession() as session:
        ZT_API = get_token()
        client = ZeroTier(ZT_API, loop, session)
        #cache.clear()

        try:
            # get status details of the local node
            await client.get_data('status')
            status_data = AttrDict.from_nested_dict(client.data)
            node_id = client.data.get('address')
            logger.info('Found node: {}'.format(node_id))
            cache.update([(node_id, status_data)])

            # get status details of the node peers
            await client.get_data('peer')
            active_peers = ( peer for peer in client.data )
            cached_peers = ( peer for peer in list(cache) )
            active_list = []
            for peer in active_peers:
                peer_status = AttrDict.from_nested_dict(peer)
                peer_id = peer.get('address')
                active_list.append(peer_id)
                if peer_id in cache:
                    print('Updating peer {}'.format(peer_id))
                    cache.update([(peer_id, peer_status)])
                elif peer_id not in cache:
                    print('Adding peer {}'.format(peer_id))
                    cache.update([(peer_id, peer_status)])
            for peer_id in cached_peers:
                if ( peer_id != node_id and len(peer_id) == 10 and peer_id not in active_list ):
                    print('Removing peer: {}'.format(peer_id))
                    try:
                        del cache[peer_id]
                    except KeyError:
                        print('Key {} not found'.format(peer_id))

            # get/display all available network data
            await client.get_data('network')
            active_nets = ( net for net in client.data )
            cached_nets = ( net for net in list(cache) if len(net) == 16 )
            net_list = []
            for network in active_nets:
                net_status = AttrDict.from_nested_dict(network)
                net_id = network.get('id')
                net_list.append(net_id)
                if net_id in cache:
                    print('Updating network: {}'.format(net_id))
                    cache.update([(net_id, net_status)])
                elif net_id not in cache:
                    print('Adding network: {}'.format(net_id))
                    cache.update([(net_id, net_status)])
            for net_id in cached_nets:
                if ( net_id not in net_list ):
                    print('Removing net: {}'.format(net_id))
                    try:
                        del cache[net_id]
                    except KeyError:
                        print('Key {} not found'.format(net_id))


        except exceptions.ZeroTierConnectionError:
            pass

cache = Index(get_cachedir())
loop = asyncio.get_event_loop()
loop.run_until_complete(main())
