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
    from node_tools.ctlr_funcs import set_network_cfg
    from node_tools.trie_funcs import find_dangling_nets
    from node_tools.trie_funcs import get_dangling_net_data
    from node_tools.trie_funcs import update_id_trie

    await add_network_object(client, ctlr_id=ctlr_id)
    net_id = get_network_id(client.data)
    logger.debug('BOOTSTRAP: added network id {}'.format(net_id))
    net_rules = ct.rules
    await config_network_object(client, net_rules, net_id)
    logger.debug('BOOTSTRAP: added network rules {}'.format(net_rules))
    await get_network_object_ids(client)
    logger.debug('BOOTSTRAP: got network list {}'.format(client.data))

    net_list = client.data
    if net_id in net_list:
        # Get details about each network
        await get_network_object_data(client, net_id)
        logger.debug('BOOTSTRAP: got network data {}'.format(client.data))
        trie_nets = [net_id]

        await add_network_object(client, net_id, node_id)
        logger.debug('BOOTSTRAP: added node id {} to gw net'.format(node_id))
        await get_network_object_ids(client, net_id)
        member_dict = client.data
        logger.debug('BOOTSTRAP: got node dict {}'.format(member_dict))
        await get_network_object_data(client, net_id, node_id)
        logger.debug('BOOTSTRAP: got node data {}'.format(client.data))

        ipnet, _, gw = handle_net_cfg(deque)
        await config_network_object(client, ipnet, net_id)

        # A dedicated exit node is a special case, otherwise, each new node
        # gets a src_net here, and still *needs* a exit_net.  We also need to
        # update the src net needs after linking the next mbr node.
        if not ex:
            data_list = find_dangling_nets(ct.id_trie)
            logger.debug('BOOTSTRAP: got exit net {}'.format(data_list))
            if len(data_list) == 2:
                exit_net = data_list[0]
                exit_node = data_list[1]
                await add_network_object(client, exit_net, node_id)
                logger.debug('BOOTSTRAP: added node id {} to exit net {}'.format(node_id, exit_net))
                netcfg = get_dangling_net_data(ct.net_trie, exit_net)
                gw_cfg = set_network_cfg(netcfg.host)
                logger.debug('BOOTSTRAP: got node addr {} for exit net'.format(gw_cfg))
                await config_network_object(client, gw_cfg, exit_net, node_id)
                trie_nets = [net_id, exit_net]

        await config_network_object(client, gw, net_id, node_id)
        logger.debug('BOOTSTRAP: set gw addr {} for src net {}'.format(gw, net_id))

        node_needs = [False, False]
        net_needs = [False, True]
        if not ex:
            update_id_trie(ct.id_trie, [exit_net], [node_id, exit_node], needs=[False, False], nw=True)

        update_id_trie(ct.id_trie, trie_nets, [node_id], needs=node_needs)
        update_id_trie(ct.id_trie, [net_id], [node_id], needs=net_needs, nw=True)
        # logger.debug('TRIE: id_trie has items: {}'.format(ct.id_trie.items()))


async def connect_mbr_node(client, node_id, src_net, exit_net, gw_node):
    """
    Wrapper to reconnect an existing member node; needs the (upstream)
    exit net and node IDs as well as its own ID and src_net ID.
    :notes: uses both Tries (required by offline_mbr_node below)
    :param client: ztcli_api client object
    :param node_id: node ID
    :param node_net: src_net ID for node
    :param exit_net: network ID of the gateway net to connect
    :param gw_node: node ID of the gateway host
    """
    from node_tools import ctlr_data as ct

    from node_tools.ctlr_funcs import set_network_cfg
    from node_tools.trie_funcs import get_dangling_net_data
    from node_tools.trie_funcs import update_id_trie

    await add_network_object(client, exit_net, node_id)
    logger.debug('CONNECT: added neighbor {} to exit net {}'.format(node_id, exit_net))
    netcfg = get_dangling_net_data(ct.net_trie, exit_net)
    gw_cfg = set_network_cfg(netcfg.host)
    logger.debug('CONNECT: got cfg {} for exit net'.format(gw_cfg))
    await config_network_object(client, gw_cfg, exit_net, node_id)
    logger.debug('CONNECT: net_trie keys: {}'.format(list(ct.net_trie)))
    logger.debug('CONNECT: id_trie keys: {}'.format(list(ct.id_trie)))

    update_id_trie(ct.id_trie, [exit_net], [node_id, gw_node], needs=[False, False], nw=True)
    update_id_trie(ct.id_trie, [src_net, exit_net], [node_id], needs=[False, False])


async def offline_mbr_node(client, node_id):
    """
    Wrapper for handling an offline member node; removes the mbr node
    and its left-hand (src) net, and relinks both nieghbor nodes.
    This should run in the ctlr state runner *before* the state trie
    updates happen.
    :param client: ztcli_api client object
    :param node_id: node ID
    """
    from node_tools import ctlr_data as ct
    from node_tools import state_data as st

    from node_tools.ctlr_funcs import unset_network_cfg
    from node_tools.network_funcs import publish_cfg_msg
    from node_tools.trie_funcs import cleanup_state_tries
    from node_tools.trie_funcs import get_neighbor_ids

    try:
        node_net, exit_net, src_node, exit_node = get_neighbor_ids(ct.net_trie, node_id)
        node_nets = [node_net, exit_net]
        logger.debug('OFFLINE: got node_nets {}'.format(node_nets))
        if exit_node is not None:
            st.wait_cache.set(exit_node, True, 90)
            logger.debug('OFFLINE: added exit_node {} to wait cache'.format(exit_node))
    except Exception as exc:
        logger.error('OFFLINE: {}'.format(exc))
        node_nets = [None, None]

    deauth = unset_network_cfg()
    if node_nets != [None, None]:
        if src_node is not None:
            src_net, _, _, _ = get_neighbor_ids(ct.net_trie, src_node)

        if src_node is None:
            if exit_net is not None:
                await config_network_object(client, deauth, exit_net, node_id)
                cleanup_state_tries(ct.net_trie, ct.id_trie, exit_net, node_id, mbr_only=True)
                logger.debug('OFFLINE: deauthed node id {} from exit net {}'.format(node_id, exit_net))
            await delete_network_object(client, node_net)
            cleanup_state_tries(ct.net_trie, ct.id_trie, node_net, node_id)
            logger.debug('OFFLINE: removed dangling net {}'.format(node_net))
        else:
            await config_network_object(client, deauth, exit_net, node_id)
            cleanup_state_tries(ct.net_trie, ct.id_trie, exit_net, node_id, mbr_only=True)
            logger.debug('OFFLINE: deauthed node id {} from exit net {}'.format(node_id, exit_net))
            await delete_network_object(client, node_net)
            cleanup_state_tries(ct.net_trie, ct.id_trie, node_net, node_id)
            logger.debug('OFFLINE: removed network id {} and node {}'.format(node_net, node_id))

            await connect_mbr_node(client, src_node, src_net, exit_net, exit_node)
            publish_cfg_msg(ct.id_trie, src_node, addr='127.0.0.1')
    else:
        logger.warning('OFFLINE: node {} has missing net list {}'.format(node_id, node_nets))


async def update_state_tries(client, net_trie, id_trie):
    """
    Wrapper to update ctlr state tries from ZT client API.  Loads net/id
    tries with new data (does not remove any stale trie data).
    :param client: ztcli_api client object
    :param net_trie: zt network/member data
    :param id_trie: network/node state
    """
    from node_tools.trie_funcs import load_id_trie

    await get_network_object_ids(client)
    logger.debug('{} networks found'.format(len(client.data)))
    net_list = client.data
    for net_id in net_list:
        mbr_list = []
        # get details about each network and update trie data
        await get_network_object_data(client, net_id)
        net_trie[net_id] = client.data
        # load_id_trie(net_trie, id_trie, [net_id], [], nw=True)
        await get_network_object_ids(client, net_id)
        logger.debug('network {} has {} possible member(s)'.format(net_id, len(client.data)))
        member_dict = client.data
        for mbr_id in member_dict.keys():
            # get details about each network member and update trie data
            await get_network_object_data(client, net_id, mbr_id)
            if client.data['authorized']:
                logger.debug('adding member: {}'.format(mbr_id))
                net_trie[net_id + mbr_id] = client.data
                load_id_trie(net_trie, id_trie, [], [mbr_id])
                mbr_list.append(mbr_id)
        load_id_trie(net_trie, id_trie, [net_id], mbr_list, nw=True)
        logger.debug('member key suffixes: {}'.format(net_trie.suffixes(net_id)))


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
