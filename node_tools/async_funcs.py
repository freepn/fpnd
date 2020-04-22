# coding: utf-8

"""asyncio-specific wrapper functions."""

import asyncio
import aiohttp
import logging


logger = logging.getLogger(__name__)


async def bootstrap_mbr_node(client, ctlr_id, node_id, deque, ex=False):
    """
    Wrapper for bootstrapping a new member node; adds one network for
    each node and adds each node to its (new) network.  Updates net/id
    tries with new data.
    :notes: Since we *always* provide a new (ZT) network, we do *not*
            handle existing nodes here.  The `deque` parameter is
            required for handle_net_cfg().
    :param client: ztcli_api client object
    :param ctlr_id: node ID of controller node
    :param node_id: node ID
    :param deque: netobj queue
    :param ex: True if node is an exit node
    """
    from node_tools import ctlr_data as ct

    from node_tools.ctlr_funcs import get_network_id
    from node_tools.ctlr_funcs import handle_net_cfg
    from node_tools.trie_funcs import update_id_trie

    await add_network_object(client, ctlr_id=ctlr_id)
    net_id = get_network_id(client.data)
    logger.debug('BOOTSTRAP: added network id {}'.format(net_id))
    await get_network_object_ids(client)
    logger.debug('BOOTSTRAP: got network list {}'.format(client.data))

    net_list = client.data
    if net_id in net_list:
        # Get details about each network
        await get_network_object_data(client, net_id)
        logger.debug('BOOTSTRAP: got network data {}'.format(client.data))

        await add_network_object(client, net_id, node_id)
        logger.debug('BOOTSTRAP: added node id {}'.format(node_id))
        await get_network_object_ids(client, net_id)
        member_dict = client.data
        logger.debug('BOOTSTRAP: got node dict {}'.format(member_dict))
        await get_network_object_data(client, net_id, node_id)
        logger.debug('BOOTSTRAP: got node data {}'.format(client.data))

        net, src, gw = handle_net_cfg(deque)
        await config_network_object(client, net, net_id)

        # dedicated exit node is a special case, otherwise, each new node
        # gets a src_net here, and still *needs* a gw_net
        if ex:
            await config_network_object(client, gw, net_id, node_id)
            node_needs = [False, False]
        else:
            await config_network_object(client, src, net_id, node_id)
            node_needs = [True, False]
        net_needs = [False, True]

        update_id_trie(ct.id_trie, [net_id], [node_id], needs=node_needs)
        update_id_trie(ct.id_trie, [net_id], [node_id], needs=net_needs, nw=True)
        logger.debug('TRIE: id_trie has items: {}'.format(ct.id_trie.items()))


async def add_network_object(client, net_id=None, mbr_id=None, ctlr_id=None):
    """
    Command wrapper for creating ZT objects under the `controller` endpoint.
    Required arguments are `client` and either one of the following:
        `net_id` *and* `mbr_id` to create a member object *or* just
        `ctlr_id` to create a network object.
    :param client: ztcli_api client object
    :param net_id: network ID endpoint path
    :param mbr_id: member ID endpoint path
    :param ctlr_id: network controller ID
    """
    from node_tools.ctlr_funcs import name_generator

    if net_id and mbr_id:
        endpoint = 'controller/network/{}/member/{}'.format(net_id, mbr_id)
        cfg_dict = {'': ''}
    elif ctlr_id:
        net_name = name_generator()
        endpoint = 'controller/network/{}'.format(ctlr_id + '______')
        cfg_dict = {'name': net_name}
    else:
        logger.error('One or more required arguments not found!')
        return

    await client.set_value(cfg_dict, endpoint)


async def config_network_object(client, cfg_dict, net_id, mbr_id=None):
    """
    Command wrapper for configuring ZT objects under the `controller` endpoint.
    Required arguments are `client` and `cfg_dict`, plus either one of
    the following:
        `net_id` *and* `mbr_id` to configure a member object *or* just
        `net_id` to configure a network object.
    :param client: ztcli_api client object
    :param cfg_dict: dictionary of configuration fragments
    :param net_id: network ID endpoint path
    :param mbr_id: member ID endpoint path
    """
    if mbr_id and net_id:
        endpoint = 'controller/network/{}/member/{}'.format(net_id, mbr_id)
    elif net_id:
        endpoint = 'controller/network/{}'.format(net_id)
    else:
        logger.error('One or more required arguments not found!')
        return

    await client.set_value(cfg_dict, endpoint)


async def delete_network_object(client, net_id, mbr_id=None):
    """
    Command wrapper for deleting ZT objects under the `controller` endpoint.
    Required arguments are `client` and either one of the following:
        `net_id` *and* `mbr_id` to delete a member object *or* just
        `net_id` to delete a network object.
    Warning: deleting a network object is permanent.
    :param client: ztcli_api client object
    :param net_id: network ID endpoint path
    :param mbr_id: member ID endpoint path
    """
    if mbr_id and net_id:
        endpoint = 'controller/network/{}/member/{}'.format(net_id, mbr_id)
    elif net_id:
        endpoint = 'controller/network/{}'.format(net_id)
    else:
        logger.error('One or more required arguments not found!')
        return

    await client.delete_thing(endpoint)


async def get_network_object_data(client, net_id, mbr_id=None):
    """
    Command wrapper for getting ZT network/member data under the
    `controller` endpoint.
    Required arguments are `client` and either one of the following:
        `net_id` *and* `mbr_id` to get member data *or* just
        `net_id` to get network data.
    :param client: ztcli_api client object
    :param net_id: network ID endpoint path
    :param mbr_id: member ID endpoint path
    """
    if mbr_id and net_id:
        endpoint = 'controller/network/{}/member/{}'.format(net_id, mbr_id)
    elif net_id:
        endpoint = 'controller/network/{}'.format(net_id)
    else:
        logger.error('One or more required arguments not found!')
        return

    await client.get_data(endpoint)


async def get_network_object_ids(client, net_id=None):
    """
    Command wrapper for getting ZT network/member objects under the
    `controller` endpoint.
    Required arguments are `client` and optionally `net_id` to get
    member IDs from a network.
    :param client: ztcli_api client object
    :param net_id: network ID endpoint path
    """
    if net_id:
        endpoint = 'controller/network/{}/member'.format(net_id)
    else:
        endpoint = 'controller/network'

    await client.get_data(endpoint)
