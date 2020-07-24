# coding: utf-8

"""asyncio-specific wrapper functions."""

import asyncio
import aiohttp
import logging
import time


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
                time.sleep(0.01)
                netcfg = get_dangling_net_data(ct.net_trie, exit_net)
                gw_cfg = set_network_cfg(netcfg.host)
                logger.debug('BOOTSTRAP: got node addr {} for exit net'.format(gw_cfg))
                await config_network_object(client, gw_cfg, exit_net, node_id)
                trie_nets = [net_id, exit_net]
            else:
                logger.error('BOOTSTRAP: malformed exit net data {}'.format(data_list))

        await config_network_object(client, gw, net_id, node_id)
        logger.debug('BOOTSTRAP: set gw addr {} for src net {}'.format(gw, net_id))

        node_needs = [False, False]
        net_needs = [False, True]
        if not ex:
            update_id_trie(ct.id_trie, [exit_net], [node_id, exit_node], needs=[False, False], nw=True)

        update_id_trie(ct.id_trie, trie_nets, [node_id], needs=node_needs)
        update_id_trie(ct.id_trie, [net_id], [node_id], needs=net_needs, nw=True)
        # logger.debug('TRIE: id_trie has items: {}'.format(ct.id_trie.items()))


async def close_mbr_net(client, node_lst, boot_lst, min_nodes=5):
    """
    Wrapper for closing the bootstrap chain or adding it to an existing
    (closed) network. This should run in the ctlr state runner *after*
    the other handlers.
    :param client: ztcli_api client object
    :param node_lst: list of all active nodes
    :param boot_lst: list of bootstrap nodes
    :param min_nodes: minimum number of nodes for a closed network
    """
    from node_tools import ctlr_data as ct
    from node_tools import state_data as st

    from node_tools.ctlr_funcs import unset_network_cfg
    from node_tools.network_funcs import publish_cfg_msg
    from node_tools.trie_funcs import cleanup_state_tries
    from node_tools.trie_funcs import find_dangling_nets
    from node_tools.trie_funcs import find_exit_net
    from node_tools.trie_funcs import get_neighbor_ids
    from node_tools.trie_funcs import get_target_node_id

    head_id = boot_lst[-1]
    tail_id = boot_lst[0]
    head_exit_net = find_exit_net(ct.id_trie)[0]
    head_src_net, _, _, _ = get_neighbor_ids(ct.net_trie, head_id)
    tail_exit_net = find_dangling_nets(ct.id_trie)[0]
    deauth = unset_network_cfg()

    # if true, we only have a boot list
    if len(node_lst) == len(boot_lst):
        # check if we have enough nodes for a network
        if len(boot_lst) >= min_nodes:
            logger.debug('CLOSURE: creating network from boot_list {}'.format(boot_lst))
            for mbr_id in [head_id, tail_id]:
                st.wait_cache.set(mbr_id, True, 90)
            # detach and connect head to tail
            await config_network_object(client, deauth, head_exit_net, head_id)
            cleanup_state_tries(ct.net_trie, ct.id_trie, head_exit_net, head_id, mbr_only=True)
            logger.debug('CLOSURE: deauthed head id {} from exit net {}'.format(head_id, head_exit_net))

            await connect_mbr_node(client, head_id, head_src_net, tail_exit_net, tail_id)
            publish_cfg_msg(ct.id_trie, head_id, addr='127.0.0.1')
        else:
            logger.debug('CLOSURE: not enough bootstrap nodes to wrap')
    else:
        logger.debug('CLOSURE: adding bootstrap list {} to network'.format(boot_lst))
        tgt_id = get_target_node_id(node_lst, boot_lst)
        tgt_net, tgt_exit_net, tgt_src_node, tgt_exit_node = get_neighbor_ids(ct.net_trie, tgt_id)
        tgt_src_net, _, _, _ = get_neighbor_ids(ct.net_trie, tgt_src_node)

        for mbr_id in [tgt_id, tail_id, head_id, tgt_exit_node]:
            st.wait_cache.set(mbr_id, True, 120)
        # detach and connect tgt to tail
        await config_network_object(client, deauth, tgt_exit_net, tgt_id)
        cleanup_state_tries(ct.net_trie, ct.id_trie, tgt_exit_net, tgt_id, mbr_only=True)
        logger.debug('CLOSURE: deauthed tgt id {} from tgt exit net {}'.format(tgt_id, tgt_exit_net))

        await connect_mbr_node(client, tgt_id, tgt_src_net, tail_exit_net, tail_id)
        publish_cfg_msg(ct.id_trie, tgt_id, addr='127.0.0.1')

        # detach and connect head to tgt exit net
        await config_network_object(client, deauth, head_exit_net, head_id)
        cleanup_state_tries(ct.net_trie, ct.id_trie, head_exit_net, head_id, mbr_only=True)
        logger.debug('CLOSURE: deauthed node id {} from head exit net {}'.format(head_id, head_exit_net))

        await connect_mbr_node(client, head_id, head_src_net, tgt_exit_net, tgt_exit_node)
        time.sleep(0.02)
        publish_cfg_msg(ct.id_trie, head_id, addr='127.0.0.1')


async def cleanup_orphans(client):
    """
    Simple cleanup function to run after node juggling and before the
    tries are updated (in the main netstate context).
    :param client: ztcli_api client object
    """
    from node_tools import ctlr_data as ct
    from node_tools import state_data as st

    from node_tools.trie_funcs import cleanup_state_tries
    from node_tools.trie_funcs import find_orphans

    check_list = find_orphans(ct.net_trie, ct.id_trie)
    logger.debug('{} nets in check_list: {}'.format(len(check_list), check_list))
    if check_list != []:
        for thing in check_list:
            if isinstance(thing, str):
                await delete_network_object(client, thing)
                time.sleep(0.01)
                cleanup_state_tries(ct.net_trie, ct.id_trie, thing, None)
                logger.warning('CLEANUP: removed orphan: {}'.format(thing))
            elif isinstance(thing, tuple):
                if st.wait_cache.get(thing[1]) is None:
                    await delete_network_object(client, thing[0])
                    time.sleep(0.02)
                    cleanup_state_tries(ct.net_trie, ct.id_trie, thing[0], thing[1])
                    logger.warning('CLEANUP: removed orphan: {}'.format(thing))


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
        logger.debug('OFFLINE: got node_nets {} and nodes {} {}'.format(node_nets, src_node, exit_node))
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


async def unwrap_mbr_net(client, node_lst, boot_lst, min_nodes=5):
    """
    Wrapper for unwrapping the (closed) network when it gets too small.
    This should run in the ctlr state runner *after* the other handlers
    (and when there are not enough nodes to keep a closed network).
    :param client: ztcli_api client object
    :param node_lst: list of all active nodes
    :param boot_lst: list of bootstrap nodes
    :param min_nodes: minimum number of nodes for a closed network
    """
    from node_tools import ctlr_data as ct

    from node_tools.ctlr_funcs import unset_network_cfg
    from node_tools.network_funcs import publish_cfg_msg
    from node_tools.trie_funcs import cleanup_state_tries
    from node_tools.trie_funcs import find_dangling_nets
    from node_tools.trie_funcs import get_neighbor_ids
    from node_tools.trie_funcs import get_target_node_id

    if len(node_lst) < min_nodes and len(boot_lst) == 0:
        logger.debug('UNWRAP: creating bootstrap list from network {}'.format(node_lst))
        tgt_id = get_target_node_id(node_lst, boot_lst)
        tgt_net, tgt_exit_net, _, _ = get_neighbor_ids(ct.net_trie, tgt_id)
        # tgt_src_net, _, _, _ = get_neighbor_ids(ct.net_trie, tgt_src_node)
        data_list = find_dangling_nets(ct.id_trie)
        exit_net = data_list[0]
        exit_node = data_list[1]
        deauth = unset_network_cfg()

        # detach and connect tgt node back to exit node
        await config_network_object(client, deauth, tgt_exit_net, tgt_id)
        cleanup_state_tries(ct.net_trie, ct.id_trie, tgt_exit_net, tgt_id, mbr_only=True)
        logger.debug('UNWRAP: deauthed node id {} from tgt exit net {}'.format(tgt_id, tgt_exit_net))

        await connect_mbr_node(client, tgt_id, tgt_net, exit_net, exit_node)
        publish_cfg_msg(ct.id_trie, tgt_id, addr='127.0.0.1')
    else:
        logger.debug('UNWRAP: num nodes at least {} so not unwrapping'.format(min_nodes))


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
