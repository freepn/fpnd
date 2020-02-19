# coding: utf-8

"""Get data from local ZeroTier node using async client session."""
import asyncio
import aiohttp
import logging

import datrie as dt
import diskcache as dc

from ztcli_api import ZeroTier
from ztcli_api import ZeroTierConnectionError

from node_tools.cache_funcs import find_keys
from node_tools.cache_funcs import get_net_status
from node_tools.ctlr_funcs import handle_node_status
from node_tools.ctlr_funcs import load_state_trie
from node_tools.helper_funcs import get_cachedir
from node_tools.helper_funcs import get_token
from node_tools.msg_queues import handle_node_queues


logger = logging.getLogger('netstate2')


async def main():
    """State cache updater to retrieve data from a local ZeroTier node."""
    async with aiohttp.ClientSession() as session:
        ZT_API = get_token()
        client = ZeroTier(ZT_API, loop, session)

        try:
            # get status details of the local node
            await client.get_data('status')
            ctlr_id = handle_node_status(client.data, cache)

            # get all available ctlr network data
            await client.get_data('controller/network')
            logger.debug('{} networks found'.format(len(client.data)))
            net_list = client.data
            mbrs = []
            mbr_list = []
            for net_id in net_list:
                # Get details about each network
                await client.get_data('controller/network/{}'.format(net_id))
                net_trie[net_id] = client.data
                await client.get_data('controller/network/{}/member'.format(net_id))
                logger.debug('{} members found'.format(len(client.data)))
                member_dict = client.data
                for mbr_id in member_dict.keys():
                    mbr_list.append(mbr_id)
                    # get details about each network member
                    await client.get_data('controller/network/{}/member/{}'.format(net_id, mbr_id))
                    net_trie[mbr_id + net_id] = client.data
            logger.debug('State trie has {} networks with ctlr_id prefix:'.format(len(net_trie.items(ctlr_id))))
            logger.debug('State trie has network keys: {}'.format(net_trie.keys(ctlr_id)))
            logger.debug('{} members in member list: {}'.format(len(mbr_list), mbr_list))
            for mbr in mbr_list:
                if net_trie.has_keys_with_prefix(mbr):
                    logger.debug('has_keys_with_prefix {} says {}'.format(mbr, net_trie.has_keys_with_prefix(mbr)))
                    logger.debug('keys for {} returns {}'.format(mbr, net_trie.keys(mbr)))
                    mbrs.append(net_trie.keys(mbr)[0])
            logger.debug('State trie has {} members with mbr_id prefix'.format(len(mbrs)))
            logger.debug('State trie has member keys: {}'.format(mbrs))

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
            logger.error('netstate2 exception was: {}'.format(exc))
            raise exc


cache = dc.Index(get_cachedir())
net_trie = load_state_trie(directory=get_cachedir('state_trie'))
node_q = dc.Deque(directory=get_cachedir('node_queue'))
staging_q = dc.Deque(directory=get_cachedir('staging_queue'))
loop = asyncio.get_event_loop()
loop.run_until_complete(main())
