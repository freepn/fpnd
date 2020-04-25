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

    try:
        for param in [nw_id, node_id, needs]:
            assert type(param) is list
        for param in [nw_id, node_id]:
            assert len(param) < 3
        assert len(needs) == 0 or len(needs) == 2
    except:
        return False
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
    the target network from the `routes` list as a python IPv4 netobj.
    :param trie: ID state trie
    :param net_id: network ID to retrive
    :return: <netobj> or None
    """
    from node_tools.ctlr_funcs import netcfg_get_ipnet

    payload = trie[net_id]
    netobj = None

    for route in payload['routes']:
        if route['via'] is None:
            tgt_route = route['target']
            netobj = netcfg_get_ipnet(tgt_route)

    return netobj


def load_id_trie(net_trie, id_trie, nw_id, node_id, needs=[], nw=False):
    """
    Load ID state trie based on current data from ZT api.  Default key
    is node key with network payload; set `nw` = True for network key
    with node payload.
    :notes: This is intended to run in the normal netstate context; the
            default key param should be a list of one ID.
    :param net_trie: datrie trie object
    :param id_trie: datrie trie object
    :param nw_id: list of network IDs
    :param node_id: list of node IDs
    :param: needs: list of needs
    :param nw: bool net|node ID is key
    """
    from node_tools.helper_funcs import NODE_SETTINGS

    if not check_trie_params(nw_id, node_id, needs):
        raise AssertionError

    id_list = []
    payload = (id_list, needs)

    if nw:
        net_id = nw_id[0]
        suf_list = net_trie.suffixes(net_id)
        mbr_list = suf_list[1:]
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
        key_id = mbr_id
        id_list = net_list

    id_trie[key_id] = payload


def trie_is_empty(trie):
    """
    Check shared state Trie is fresh and empty (mainly on startup).
    :param trie: newly instantiated `datrie.Trie(alpha_set)`
    """
    try:
        assert trie.is_dirty()
        assert list(trie) == []
    except:
        return False
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
    if not check_trie_params(nw_id, node_id, needs):
        raise AssertionError

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
