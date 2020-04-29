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
        if not type(param) is list:
            raise AssertionError('Invalid trie parameter: {}'.format(param))
    for param in [nw_id, node_id]:
        if not len(param) < 3:
            raise AssertionError('Invalid trie parameter: {}'.format(param))
    if not (nw_id != [] or node_id != []):
        raise AssertionError('Invalid trie parameter')
    if (len(needs) == 1 or len(needs) > 3):
        raise AssertionError('Invalid trie parameter: {}'.format(needs))
    return True


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


def get_dangling_net_data(trie, net_id):
    """
    Given the ID, get the payload from the net_id state trie and return
    the target network cfg from the `routes` list.
    :notes: The return format matches the cfg_dict payload used by
            config_network_object()
    :param trie: net ID state trie
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


def load_id_trie(net_trie, id_trie, nw_id, node_id, needs=[], nw=False):
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
    :param trie: datrie trie object
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
