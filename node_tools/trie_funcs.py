# coding: utf-8

"""trie-specific helper functions."""

import logging

import datrie


logger = logging.getLogger(__name__)


def create_state_trie(prefix='trie', ext='.dat'):
    """
    Create a file-backed trie object.
    """
    import string
    import tempfile

    fd, fname = tempfile.mkstemp(suffix=ext, prefix=prefix)
    trie = datrie.Trie(string.hexdigits)
    trie.save(fname)

    return fd, fname


def load_state_trie(fname):
    """
    Load a file-backed trie object.
    """
    trie = datrie.Trie.load(fname)
    return trie


def save_state_trie(trie, fname):
    """
    Save a file-backed trie object.
    """
    trie.save(fname)


def check_trie_params(nw_id, node_id, needs):
    """Check load/update trie params for correctness"""

    for param in [nw_id, node_id, needs]:
        if not isinstance(param, list):
            raise AssertionError('Invalid trie parameter: {}'.format(param))
    for param in [nw_id, node_id]:
        if not len(param) < 3:
            raise AssertionError('Invalid trie parameter: {}'.format(param))
    if not (nw_id != [] or node_id != []):
        raise AssertionError('Invalid trie parameter')
    if (len(needs) == 1 or len(needs) > 3):
        raise AssertionError('Invalid trie parameter: {}'.format(needs))
    return True


def cleanup_state_tries(net_trie, id_trie, nw_id, node_id, mbr_only=False):
    """
    Delete offlined mbr nodes/nets from state data tries. This needs to
    run whenever nodes are disconnected or removed, in order to cleanup
    stale trie data.
    :param net_trie: net state trie object
    :param id_trie: ID state trie object
    :param nw_id: network ID str
    :param node_id: mbr node ID str
    :param mbr_only: if True, delete only the member node keys
    """

    if mbr_only:
        mbr_key = nw_id + node_id
        del net_trie[mbr_key]
        del id_trie[node_id]
    else:
        for key in net_trie.keys(nw_id):
            del net_trie[key]
        del id_trie[nw_id]
        if node_id:
            if node_id in id_trie:
                del id_trie[node_id]


def find_dangling_nets(trie):
    """
    Find networks with needs that are `True` (search the ID trie).
    :notes: In this case the target networks should already be attached
            to mbr nodes in the bootstrap chain, meaning we look for the
            "last" one in the chain and return the net/node IDs.
    :param trie: ID state trie
    :return: list of network ID and attached node ID
    """
    net_list = []

    for net in [x for x in list(trie) if len(x) == 16]:
        if trie[net][1] == [False, True]:
            net_list = [net, trie[net][0][0]]
    return net_list


def find_exit_net(trie):
    """
    Find the network attached to the exit node (search the ID trie).
    :param trie: ID state trie
    :return: network ID for the (only) network on the exit node
    """
    net_list = []

    for node in [x for x in list(trie) if len(x) == 10]:
        if trie[node][1] == [False, False] and len(trie[node][0]) == 1:
            net_list = trie[node][0]
    return net_list


def get_active_nodes(id_trie):
    """
    Find all the currently active nodes (search the ID trie).
    :notes: In this case the answer depends on when this runs (relative
            to the cmds in `netstate` runner).
    :param id_trie: ID state trie
    :return: list of node IDs (empty list if None)
    """
    node_list = []

    for node in [x for x in list(id_trie) if len(x) == 10]:
        node_list.append(node)
    return node_list


def get_bootstrap_list(net_trie, id_trie):
    """
    Find all the nodes in the bootstrap chain (search the net trie).
    :notes: We start counting from the last node in the bootstrap
    chain.
    :param trie: net data trie
    :param trie: ID state trie
    :return: list of node IDs (empty list if None)
    """
    from node_tools.ctlr_funcs import get_exit_node_id

    node_list = []
    next_node = None
    exit_node = get_exit_node_id()
    dangle_list = find_dangling_nets(id_trie)
    last_node = dangle_list[1]
    prev_node = last_node

    if last_node != exit_node:
        while next_node != exit_node:
            node_list.append(prev_node)
            _, _, _, next_node = get_neighbor_ids(net_trie, prev_node)
            prev_node = next_node

    return node_list


def get_dangling_net_data(trie, net_id):
    """
    Given the net ID, get the payload from the net data trie and return
    the target network cfg from the `routes` list.
    :notes: The return format matches the cfg_dict payload used by
            config_network_object()
    :param trie: net data trie
    :param net_id: network ID to retrive
    :return: Attrdict <netcfg> or None
    """
    from node_tools.ctlr_funcs import ipnet_get_netcfg
    from node_tools.ctlr_funcs import netcfg_get_ipnet

    payload = trie[net_id]
    netcfg = None

    for route in payload['routes']:
        if route['via'] is not None:
            tgt_route = route['via']
            netobj = netcfg_get_ipnet(tgt_route)
            netcfg = ipnet_get_netcfg(netobj)

    return netcfg


def get_neighbor_ids(trie, node_id):
    """
    Given the node ID, get the payloads from the net trie and return
    the attached network and neighbor node IDs.
    :param trie: net data trie
    :param node_id: node ID to lookup
    :return: tuple of net and node IDs
    """
    from node_tools.ctlr_funcs import ipnet_get_netcfg
    from node_tools.ctlr_funcs import is_exit_node
    from node_tools.ctlr_funcs import netcfg_get_ipnet
    from node_tools.helper_funcs import find_ipv4_iface

    node_list = []
    key_list = []
    src_net = None
    exit_net = None
    src_node = None
    exit_node = None

    for key in trie:
        if node_id in key:
            key_list.append(key[0:16])
            node_list.append(trie[key])

    if len(key_list) != 2 and (len(key_list) == 1 and not is_exit_node(node_id)):
        raise AssertionError('Node {} keys {} are invalid!'.format(node_id, key_list))
    else:
        for key, data in zip(key_list, node_list):
            node_ip = data['ipAssignments'][0]
            ipnet = netcfg_get_ipnet(node_ip)
            netcfg = ipnet_get_netcfg(ipnet)
            gw_ip = find_ipv4_iface(netcfg.gateway[0])
            if node_ip == gw_ip:
                src_net = key
                for node in trie.suffixes(src_net)[1:]:
                    if node_id != node:
                        src_node = node
            else:
                exit_net = key
                for node in trie.suffixes(exit_net)[1:]:
                    if node_id != node:
                        exit_node = node
    return src_net, exit_net, src_node, exit_node


def get_target_node_id(node_lst, boot_lst):
    """
    Return a target node ID from the active network to use as an
    insertion point for all the nodes in the bootstrap list.
    :notes: choice of tgt node is random; this may change
    :param trie: net data trie
    :param node_lst: list of all active nodes
    :param boot_lst: list of bootstrap nodes
    :return: <str> node ID
    """
    import random
    from node_tools.ctlr_funcs import is_exit_node

    return random.choice([x for x in node_lst if x not in boot_lst and not is_exit_node(x)])


def get_wedged_node_id(trie, node_id):
    """
    Get the node ID of a wedged node, where wedged is defined by the
    network failure error code returned by wget (retcode == 4).  The
    wedge msg is initiated by its downstream neightbor node.
    :param trie: net data trie
    :param node_id: ID of node with network failure
    :return: exit node ID or None
    """
    from node_tools import state_data as st

    _, _, _, exit_node = get_neighbor_ids(trie, node_id)

    if st.wait_cache.get(exit_node):
        exit_node = None

    logger.debug('TRIE: node {} has exit node {}'.format(node_id, exit_node))
    return exit_node


def load_id_trie(net_trie, id_trie, nw_id, node_id, needs=[], nw=False, prune=False):
    """
    Load ID state trie based on current data from ZT api.  Default key
    is node key with network payload; set `nw` = True for network key
    with node payload.
    :notes: This is intended to run in the normal netstate context; the
            default key param should be a list of one ID.
            * one of `nw_id` or `node_id` must be a non-empty list
            * `needs` should be empty (it is unused)
    :param net_trie: datrie trie object
    :param id_trie: datrie trie object
    :param nw_id: list of network IDs
    :param node_id: list of node IDs
    :param: needs: list of needs
    :param nw: bool net|node ID is key
    """
    from node_tools.helper_funcs import NODE_SETTINGS

    check_trie_params(nw_id, node_id, needs)

    id_list = []
    prune_list = []

    if nw:
        net_id = nw_id[0]
        mbr_list = net_trie.suffixes(net_id)[1:]
        logger.debug('TRIE: net_id {} has mbr {} list'.format(net_id, mbr_list))
        if len(mbr_list) == 2:
            needs = [False, False]
        elif len(mbr_list) == 1:
            needs = [False, True]
        key_id = net_id
        id_list = mbr_list
        if prune and id_list == []:
            prune_list.append(net_id)
    else:
        net_list = []
        mbr_id = node_id[0]
        for key in list(net_trie):
            if mbr_id in key:
                net_list.append(key[0:16])
        if len(net_list) == 2:
            needs = [False, False]
        elif len(net_list) == 1:
            needs = [False, True]
            if mbr_id in NODE_SETTINGS['use_exitnode']:
                needs = [False, False]
        logger.debug('TRIE: mbr_id {} has net_list {}'.format(mbr_id, net_list))
        key_id = mbr_id
        id_list = net_list

    payload = (id_list, needs)
    logger.debug('TRIE: loading key {} with payload {}'.format(key_id, payload))
    id_trie[key_id] = payload
    return prune_list


def trie_is_empty(trie):
    """
    Check shared state Trie is fresh and empty (mainly on startup).
    :param trie: newly instantiated `datrie.Trie(alpha_set)`
    """
    if not (trie.is_dirty() and list(trie) == []):
        raise AssertionError('Trie {} is not empty!'.format(trie))
    return True


def update_id_trie(trie, nw_id, node_id, needs=[], nw=False):
    """
    Update/load ID state trie with new ID data.  Default key is node
    key with network payload; set `nw` = True for network key with
    node payload.
    :notes: This is intended to run in the bootstrap_mbr_node context.
    :param trie: id state trie object
    :param nw_id: list of network IDs
    :param node_id: list of node IDs
    :param: needs: list of needs
    :param nw: bool nw|node ID is key
    """
    check_trie_params(nw_id, node_id, needs)

    id_list = []
    payload = (id_list, needs)

    if nw:
        for item in node_id:
            id_list.append(item)
        key_id = nw_id[0]
    else:
        for item in nw_id:
            id_list.append(item)
        key_id = node_id[0]

    trie[key_id] = payload
