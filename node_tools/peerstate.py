# coding: utf-8

"""Get data from local ZeroTier node using async client session."""
import asyncio
import aiohttp
import logging

import diskcache as dc

from ztcli_api import ZeroTier
from ztcli_api import ZeroTierConnectionError

from node_tools import state_data as st

from node_tools.cache_funcs import find_keys
from node_tools.cache_funcs import get_peer_status
from node_tools.cache_funcs import handle_node_status
from node_tools.cache_funcs import load_cache_by_type
from node_tools.helper_funcs import get_cachedir
from node_tools.helper_funcs import get_token
from node_tools.msg_queues import manage_incoming_nodes
from node_tools.msg_queues import populate_leaf_list
from node_tools.network_funcs import drain_msg_queue


logger = logging.getLogger('peerstate')


async def main():
    """State cache updater to retrieve data from a local ZeroTier node."""
    async with aiohttp.ClientSession() as session:
        ZT_API = get_token()
        client = ZeroTier(ZT_API, loop, session)

        try:
            logger.debug('{} node(s) in reg queue: {}'.format(len(off_q), list(off_q)))
            if len(off_q) > 0:
                drain_msg_queue(off_q, addr='127.0.0.1', method='offline')

            logger.debug('{} node(s) in reg queue: {}'.format(len(reg_q), list(reg_q)))
            logger.debug('{} node(s) in wait queue: {}'.format(len(wait_q), list(wait_q)))
            manage_incoming_nodes(node_q, reg_q, wait_q)
            if len(reg_q) > 0:
                drain_msg_queue(reg_q, pub_q, addr='127.0.0.1')

            # get status details of the local node and update state
            await client.get_data('status')
            node_id = handle_node_status(client.data, cache)

            # get status details of the node peers
            await client.get_data('peer')
            peer_data = client.data
            logger.info('Found {} peers'.format(len(peer_data)))
            peer_keys = find_keys(cache, 'peer')
            logger.debug('Returned peer keys: {}'.format(peer_keys))
            load_cache_by_type(cache, peer_data, 'peer')

            num_leaves = 0
            peerStatus = get_peer_status(cache)
            for peer in peerStatus:
                if peer['role'] == 'LEAF':
                    if peer['identity'] not in reg_q:
                        if peer['identity'] not in node_q:
                            node_q.append(peer['identity'])
                            logger.debug('Adding LEAF node id: {}'.format(peer['identity']))
                    populate_leaf_list(node_q, wait_q, peer)
                    num_leaves = num_leaves + 1
            if num_leaves == 0 and st.leaf_nodes != []:
                st.leaf_nodes = []
            if st.leaf_nodes != []:
                logger.debug('Found leaf node(s): {}'.format(st.leaf_nodes))
            logger.debug('{} node(s) in node queue: {}'.format(len(node_q), list(node_q)))

            logger.debug('{} node(s) in reg queue: {}'.format(len(reg_q), list(reg_q)))
            logger.debug('{} node(s) in wait queue: {}'.format(len(wait_q), list(wait_q)))
            manage_incoming_nodes(node_q, reg_q, wait_q)
            if len(reg_q) > 0:
                drain_msg_queue(reg_q, pub_q, addr='127.0.0.1')

            logger.debug('{} node(s) in node queue: {}'.format(len(node_q), list(node_q)))
            logger.debug('{} node(s) in pub queue: {}'.format(len(pub_q), list(pub_q)))
            logger.debug('{} node(s) in active queue: {}'.format(len(cfg_q), list(cfg_q)))

        except Exception as exc:
            logger.error('peerstate exception was: {}'.format(exc))
            raise exc


cache = dc.Index(get_cachedir())
cfg_q = dc.Deque(directory=get_cachedir('cfg_queue'))
node_q = dc.Deque(directory=get_cachedir('node_queue'))
off_q = dc.Deque(directory=get_cachedir('off_queue'))
pub_q = dc.Deque(directory=get_cachedir('pub_queue'))
reg_q = dc.Deque(directory=get_cachedir('reg_queue'))
wait_q = dc.Deque(directory=get_cachedir('wait_queue'))
loop = asyncio.get_event_loop()
loop.run_until_complete(main())
