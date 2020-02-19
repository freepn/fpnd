# coding: utf-8

"""ctlr-specific helper functions."""
import logging

from node_tools.cache_funcs import find_keys
from node_tools.cache_funcs import get_node_status
from node_tools.cache_funcs import load_cache_by_type
from node_tools.node_funcs import control_daemon


logger = logging.getLogger(__name__)


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


def handle_node_status(data, cache):
    """
    Cache handling for node status/state data
    """
    node_id = data.get('address')
    logger.debug('Found node: {}'.format(node_id))
    load_cache_by_type(cache, data, 'node')
    logger.debug('Returned {} key is: {}'.format('node', find_keys(cache, 'node')))

    nodeStatus = get_node_status(cache)
    logger.debug('Got node state: {}'.format(nodeStatus))
    load_cache_by_type(cache, nodeStatus, 'nstate')

    return node_id


def process_netobj(netobj):
    """
    Process a (python) network object into config Attrdict.
    :param subnet object: python subnet object from the netobj queue
    :return config dict: Attrdict of JSON config fragments
    """
    pass


def run_subscriber_daemon(cmd='restart'):
    """
    Command wrapper for msg subscriber daemon to log status.
    :param cmd: command to pass to the msg_subscriber daemon
                <start|stop|restart>
    """

    subscriber = 'msg_subscriber.py'

    logger.debug('Subscribing to node msgs: {}'.format(subscriber))
    res = control_daemon(cmd, script=subscriber)
    logger.debug('sub daemon response: {}'.format(res))
