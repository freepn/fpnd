# coding: utf-8

"""Get data from local ZeroTier node using async client session."""
import asyncio
import aiohttp
import logging

from diskcache import Index
from ztcli_api import ZeroTier
from ztcli_api import ZeroTierConnectionError

from node_tools.async_funcs import add_network_object
from node_tools.async_funcs import get_network_object_data
from node_tools.async_funcs import get_network_object_ids
from node_tools.cache_funcs import handle_node_status
from node_tools.helper_funcs import NODE_SETTINGS
from node_tools.helper_funcs import get_cachedir
from node_tools.helper_funcs import get_token


logger = logging.getLogger('bootstrap')


async def main():
    """
    State cache and ``adhoc`` ctlr mode bootstrap config for a local
    ZeroTier node.
    """
    async with aiohttp.ClientSession() as session:
        # adhoc ctlr needs a separate ZT HOME and identity
        ZT_API = get_token(zt_home='/var/lib/fpnd/zerotier-ctlr')
        client = ZeroTier(ZT_API, loop, session, port=9994)

        try:
            # get status details of the local node and update state
            await client.get_data('status')
            node_id = handle_node_status(client.data, cache)

            # setup network/member data under controller endpoint
            if node_id not in NODE_SETTINGS['use_exitnode']:
                await get_network_object_ids(client)
                logger.debug('{} networks found'.format(len(client.data)))
                if len(client.data) == 0:
                        await add_network_object(client, ctlr_id=node_id)
                logger.debug('Got network data: {}'.format(client.data))
                net_id = client.data[0]
                if len(NODE_SETTINGS['use_exitnode']) == 2:
                    # Get details about each network/member
                    await get_network_object_data(client, net_id)
                    net_data = client.data
                    await get_network_object_ids(client, net_id)
                    logger.debug('{} members found'.format(len(client.data)))
                    if len(client.data) == 0:
                        for node in NODE_SETTINGS['use_exitnode']:
                            await add_network_object(client, net_id, node)
                    await get_network_object_ids(client, net_id)
                    member_dict = client.data
                    for mbr_id in member_dict.keys():
                        await get_network_object_data(client, net_id, mbr_id)
                        logger.debug('Got member state: {}'.format(client.data))
                else:
                    logger.error('You need 2 node IDs in NODE_SETTINGS use_exitnode list!')

        except Exception as exc:
            logger.error(str(exc))
            raise exc


cache = Index(get_cachedir(dir_name='fpn_ctlr'))
loop = asyncio.get_event_loop()
loop.run_until_complete(main())
