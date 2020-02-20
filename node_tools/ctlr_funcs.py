# coding: utf-8

"""ctlr-specific helper functions."""
import logging

from node_tools.cache_funcs import find_keys
from node_tools.cache_funcs import get_node_status
from node_tools.cache_funcs import load_cache_by_type


logger = logging.getLogger(__name__)


def check_net_trie(trie):
    """
    Check shared state Trie is fresh and empty (mainly on startup)
    :param trie: newly instantiated ``datrie.Trie(alpha_set)``
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
    import datrie

    fd, fname = tempfile.mkstemp(suffix=ext, prefix=prefix)
    trie = datrie.Trie(string.hexdigits)
    trie.save(fname)

    return fd, fname


def load_state_trie(fname):
    import datrie

    trie = datrie.Trie.load(fname)
    return trie


def save_state_trie(trie, fname):
    trie.save(fname)


def gen_netobj_queue(deque, ipnet='172.16.0.0/12'):
    import ipaddress

    if len(deque) > 0:
        logger.debug('Using existing queue: {}'.format(deque.directory))
    else:
        logger.debug('Generating netobj queue, please be patient...')
        netobjs = list(ipaddress.ip_network(ipnet).subnets(new_prefix=30))
        for net in netobjs:
            deque.append(net)
    logger.debug('{} IPv4 network objects in queue: {}'.format(len(deque), deque.directory))


def process_netobj(netobj):
    """
    Process a (python) network object into config Attrdict.
    :param subnet object: python subnet object from the netobj queue
    :return config dict: Attrdict of JSON config fragments
    """
    pass
