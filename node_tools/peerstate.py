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
from node_tools.cache_funcs import get_node_status
from node_tools.cache_funcs import get_peer_status
from node_tools.cache_funcs import load_cache_by_type
from node_tools.helper_funcs import get_cachedir
from node_tools.helper_funcs import get_token
from node_tools.msg_queues import manage_incoming_nodes
from node_tools.msg_queues import populate_leaf_list
from node_tools.network_funcs import drain_reg_queue
from node_tools.node_funcs import control_daemon


logger = logging.getLogger('peerstate')


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

            # get status details of the node peers
            await client.get_data('peer')
            peer_data = client.data
            logger.info('Found {} peers'.format(len(peer_data)))
            peer_keys = find_keys(cache, 'peer')
            logger.debug('Returned peer keys: {}'.format(peer_keys))
            load_cache_by_type(cache, peer_data, 'peer')

            # if we get here, we can update our state objects
            nodeStatus = get_node_status(cache)
            logger.debug('Got node state: {}'.format(nodeStatus))
            load_cache_by_type(cache, nodeStatus, 'nstate')
            peerStatus = get_peer_status(cache)

            manage_incoming_nodes(node_q, reg_q, wait_q)
            logger.debug('{} nodes in reg queue: {}'.format(len(reg_q), list(reg_q)))
            logger.debug('{} nodes in wait queue: {}'.format(len(wait_q), list(wait_q)))
            if len(reg_q) > 0:
                drain_reg_queue(reg_q, addr='127.0.0.1')

            for peer in peerStatus:
                if peer['role'] == 'LEAF':
                    if peer['identity'] not in reg_q:
                        if peer['identity'] not in node_q:
                            node_q.append(peer['identity'])
                            logger.debug('Adding LEAF node id: {}'.format(peer['identity']))
                    populate_leaf_list(node_q, wait_q, peer)
            logger.debug('Collected leaf nodes: {}'.format(st.leaf_nodes))
            logger.debug('{} nodes in node queue: {}'.format(len(node_q), list(node_q)))

            if len(node_q) > 0:
                res = control_daemon('restart')
                logger.debug('Listening for peer msg')
            else:
                logger.debug('Stopping msg responder')
                res = control_daemon('stop')
            logger.debug('msg daemon response: {}'.format(res))

        except Exception as exc:
            logger.error(str(exc))
            raise exc


cache = dc.Index(get_cachedir())
node_q = dc.Deque(directory=get_cachedir('node_queue'))
reg_q = dc.Deque(directory=get_cachedir('reg_queue'))
wait_q = dc.Deque(directory=get_cachedir('wait_queue'))
loop = asyncio.get_event_loop()
loop.run_until_complete(main())
