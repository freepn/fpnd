# coding: utf-8

"""Get data from local ZeroTier node using async client session."""
import asyncio
import aiohttp
import logging

import diskcache as dc

from ztcli_api import ZeroTier
from ztcli_api import ZeroTierConnectionError

from node_tools.cache_funcs import find_keys
from node_tools.cache_funcs import get_net_status
from node_tools.cache_funcs import get_node_status
from node_tools.cache_funcs import get_peer_status
from node_tools.cache_funcs import load_cache_by_type
from node_tools.helper_funcs import get_cachedir
from node_tools.helper_funcs import get_token
from node_tools.msg_queues import handle_node_queues


logger = logging.getLogger('netstate')


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
            node_key = find_keys(cache, 'node')
            logger.debug('Returned {} key is: {}'.format('node', node_key))
            load_cache_by_type(cache, node_data, 'node')
            nodeStatus = get_node_status(cache)
            logger.debug('Got ctlr state: {}'.format(nodeStatus))
            load_cache_by_type(cache, nodeStatus, 'nstate')

            # get all available ctlr network data
            await client.get_data('controller/network')
            logger.debug('{} networks found'.format(len(client.data)))
            net_list = client.data
            net_data = []
            mbr_data = []
            for net_id in net_list:
                # Get details about each network
                await client.get_data('controller/network/{}'.format(net_id))
                net_data.append(client.data)
                await client.get_data('controller/network/{}/member'.format(net_id))
                # logger.debug('{} members found'.format(len(client.data)))
                member_dict = client.data
                for mbr_id in member_dict.keys():
                    # get details about each network member
                    await client.get_data('controller/network/{}/member/{}'.format(net_id, mbr_id))
                    mbr_data.append(client.data)

            load_cache_by_type(cache, net_data, 'net')
            net_keys = find_keys(cache, 'net')
            logger.debug('{} network keys found'.format(len(net_keys)))
            load_cache_by_type(cache, mbr_data, 'mbr')
            mbr_keys = find_keys(cache, 'mbr')
            logger.debug('{} member keys found'.format(len(mbr_keys)))

            logger.debug('{} nodes in node queue: {}'.format(len(node_q),
                                                             list(node_q)))
            if len(node_q) > 0:
                handle_node_queues(node_q, staging_q)
                logger.debug('{} nodes in node queue: {}'.format(len(node_q),
                                                                 list(node_q)))
            logger.debug('{} nodes in staging queue: {}'.format(len(staging_q),
                                                                list(staging_q)))

        except Exception as exc:
            logger.error('netstate exception was: {}'.format(exc))
            raise exc


cache = dc.Index(get_cachedir())
node_q = dc.Deque(directory=get_cachedir('node_queue'))
staging_q = dc.Deque(directory=get_cachedir('staging_queue'))
loop = asyncio.get_event_loop()
loop.run_until_complete(main())
