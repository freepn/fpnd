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


def create_state_trie(directory='/tmp/state_trie'):
    import os
    import string
    import datrie as dt

    trie = dt.Trie(string.hexdigits)
    trie.save(os.path.join(directory, 'trie.dat'))


def load_state_trie(directory='/tmp/state_trie'):
    import os
    import datrie as dt

    trie = dt.Trie.load(os.path.join(directory, 'trie.dat'))
    return trie


def save_state_trie(trie, directory='/tmp/state_trie'):
    import os
    import datrie as dt

    trie.save(os.path.join(directory, 'trie.dat'))


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
