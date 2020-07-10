# coding: utf-8

"""Get data from local ZeroTier node using async client session."""
import asyncio
import aiohttp
import logging

import diskcache as dc

from ztcli_api import ZeroTier
from ztcli_api import ZeroTierConnectionError

from node_tools import ctlr_data as ct

from node_tools.async_funcs import bootstrap_mbr_node
from node_tools.async_funcs import close_mbr_net
from node_tools.async_funcs import offline_mbr_node
from node_tools.async_funcs import unwrap_mbr_net
from node_tools.async_funcs import update_state_tries
from node_tools.cache_funcs import handle_node_status
from node_tools.ctlr_funcs import is_exit_node
from node_tools.helper_funcs import AttrDict
from node_tools.helper_funcs import NODE_SETTINGS
from node_tools.helper_funcs import get_cachedir
from node_tools.helper_funcs import get_token
from node_tools.msg_queues import handle_node_queues
from node_tools.msg_queues import handle_wedged_nodes
from node_tools.network_funcs import publish_cfg_msg
from node_tools.trie_funcs import get_active_nodes
from node_tools.trie_funcs import get_bootstrap_list


logger = logging.getLogger('netstate')


async def main():
    """State cache updater to retrieve data from a local ZeroTier node."""
    async with aiohttp.ClientSession() as session:
        ZT_API = get_token()
        client = ZeroTier(ZT_API, loop, session)

        try:
            # handle offline/wedged nodes
            handle_wedged_nodes(ct.net_trie, wdg_q, off_q)
            pre_off = list(off_q)
            logger.debug('{} nodes in offline queue: {}'.format(len(pre_off), pre_off))
            for node_id in pre_off:
                await offline_mbr_node(client, node_id)
            for node_id in [x for x in off_q if x in pre_off]:
                off_q.remove(node_id)
            logger.debug('{} nodes in offline queue: {}'.format(len(off_q), list(off_q)))

            # get ID and status details of ctlr node
            await client.get_data('status')
            ctlr_id = handle_node_status(client.data, cache)

            # update ctlr state tries
            await update_state_tries(client, ct.net_trie, ct.id_trie)
            logger.debug('net_trie has keys: {}'.format(list(ct.net_trie)))
            # for key in list(ct.net_trie):
            #     logger.debug('net key {} has paylod: {}'.format(key, ct.net_trie[key]))
            # for key in list(ct.id_trie):
            #     logger.debug('id key {} has payload: {}'.format(key, ct.id_trie[key]))
            logger.debug('id_trie has keys: {}'.format(list(ct.id_trie)))

            # handle node queues and publish messages
            logger.debug('{} nodes in node queue: {}'.format(len(node_q),
                                                             list(node_q)))
            if len(node_q) > 0:
                handle_node_queues(node_q, staging_q)
                logger.debug('{} nodes in node queue: {}'.format(len(node_q),
                                                                 list(node_q)))
            logger.debug('{} nodes in staging queue: {}'.format(len(staging_q),
                                                                list(staging_q)))

            for mbr_id in staging_q:
                if mbr_id not in list(ct.id_trie):
                    if is_exit_node(mbr_id):
                        await bootstrap_mbr_node(client, ctlr_id, mbr_id, netobj_q, ex=True)
                    else:
                        await bootstrap_mbr_node(client, ctlr_id, mbr_id, netobj_q)
                publish_cfg_msg(ct.id_trie, mbr_id, addr='127.0.0.1')

            for mbr_id in [x for x in staging_q if x in list(ct.id_trie)]:
                staging_q.remove(mbr_id)
            logger.debug('{} nodes in staging queue: {}'.format(len(staging_q),
                                                                list(staging_q)))

            # refresh ctlr state tries again
            await update_state_tries(client, ct.net_trie, ct.id_trie)

            node_list = get_active_nodes(ct.id_trie)
            logger.debug('{} nodes in node_list: {}'.format(len(node_list), node_list))
            if len(node_list) > 0:
                boot_list = get_bootstrap_list(ct.net_trie, ct.id_trie)
                logger.debug('{} nodes in boot_list: {}'.format(len(boot_list), boot_list))

                if len(boot_list) != 0:
                    await close_mbr_net(client, node_list, boot_list, min_nodes=3)
                elif len(boot_list) == 0 and len(node_list) > 1:
                    await unwrap_mbr_net(client, node_list, boot_list, min_nodes=3)

        except Exception as exc:
            logger.error('netstate exception was: {}'.format(exc))
            raise exc


cache = dc.Index(get_cachedir())
off_q = dc.Deque(directory=get_cachedir('off_queue'))
node_q = dc.Deque(directory=get_cachedir('node_queue'))
netobj_q = dc.Deque(directory=get_cachedir('netobj_queue'))
staging_q = dc.Deque(directory=get_cachedir('staging_queue'))
wdg_q = dc.Deque(directory=get_cachedir('wedge_queue'))

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
