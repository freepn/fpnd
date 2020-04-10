# coding: utf-8

"""trie-specific helper functions."""

import logging

import datrie


logger = logging.getLogger(__name__)


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


def create_state_trie(prefix='trie', ext='.dat'):
    import string
    import tempfile

    fd, fname = tempfile.mkstemp(suffix=ext, prefix=prefix)
    trie = datrie.Trie(string.hexdigits)
    trie.save(fname)

    return fd, fname


def load_state_trie(fname):
    trie = datrie.Trie.load(fname)
    return trie


def save_state_trie(trie, fname):
    trie.save(fname)
