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
    Update/load ID state trie with current ID data.  Default key is node
    key with network payload; set `nw` = True for network key with
    node payload.

    :param trie: datrie trie object
    :param nw_id: list of network IDs
    :param node_id: list of node IDs
    :param: needs: list of needs
    :param nw: bool nw|node ID is key
    """
    for param in [nw_id, node_id, needs]:
        assert type(param) is list
    for param in [nw_id, node_id]:
        assert 3 > len(param) > 0
    assert len(needs) == 0 or len(needs) == 2

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
