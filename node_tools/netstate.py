# coding: utf-8

"""Get data from local ZeroTier node using async client session."""
import asyncio
import aiohttp
import logging

import diskcache as dc

from ztcli_api import ZeroTier
from ztcli_api import ZeroTierConnectionError

from node_tools import ctlr_data as ct

from node_tools.async_funcs import add_network_object
from node_tools.async_funcs import bootstrap_mbr_node
from node_tools.async_funcs import get_network_object_data
from node_tools.async_funcs import get_network_object_ids
from node_tools.cache_funcs import find_keys
from node_tools.cache_funcs import handle_node_status
from node_tools.helper_funcs import AttrDict
from node_tools.helper_funcs import NODE_SETTINGS
from node_tools.helper_funcs import get_cachedir
from node_tools.helper_funcs import get_token
from node_tools.msg_queues import handle_node_queues
from node_tools.trie_funcs import update_id_trie

logger = logging.getLogger('netstate')


async def main():
    """State cache updater to retrieve data from a local ZeroTier node."""
    async with aiohttp.ClientSession() as session:
        ZT_API = get_token()
        client = ZeroTier(ZT_API, loop, session)

        try:
            # get status details of the local node
            await client.get_data('status')
            ctlr_id = handle_node_status(client.data, cache)

            # get/display data for available networks
            await get_network_object_ids(client)
            logger.debug('{} networks found'.format(len(client.data)))
            if len(client.data) == 0 and NODE_SETTINGS['use_exitnode'] != []:
                for exit_id in NODE_SETTINGS['use_exitnode']:
                    await bootstrap_mbr_node(client, ctlr_id, exit_id, ex=True)

            # get/display data for available networks
            await get_network_object_ids(client)
            net_list = client.data
            for net_id in net_list:
                # Get details about each network
                await get_network_object_data(client, net_id)
                ct.net_trie[net_id] = client.data
                await get_network_object_ids(client, net_id)
                logger.debug('network {} has {} member(s)'.format(net_id, len(client.data)))
                member_dict = client.data
                for mbr_id in member_dict.keys():
                    # get details about each network member
                    await get_network_object_data(client, net_id, mbr_id)
                    logger.debug('adding member: {}'.format(mbr_id))
                    ct.net_trie[net_id + mbr_id] = client.data

            logger.debug('TRIE: net_trie has keys: {}'.format(list(ct.net_trie)))
            logger.debug('TRIE: id_trie has keys: {}'.format(list(ct.id_trie)))

            # handle node queues
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
netobj_q = dc.Deque(directory=get_cachedir('netobj_queue'))
staging_q = dc.Deque(directory=get_cachedir('staging_queue'))
loop = asyncio.get_event_loop()
loop.run_until_complete(main())
