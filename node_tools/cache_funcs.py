# coding: utf-8

"""cache-specific helper functions."""
import logging
from collections import namedtuple

from node_tools.helper_funcs import AttrDict


logger = logging.getLogger(__name__)


def create_cache_entry(cache, data, key_str):
    """Load new cache entry by key type."""
    new_data = AttrDict.from_nested_dict(data)
    logger.debug('Pushing entry for: {}'.format(key_str))
    with cache.transact():
        key = cache.push(new_data, prefix=key_str)
    logger.debug('New key created for: {}'.format(key))


def find_keys(cache, key_str):
    """Find API key(s) in cache using key type string, return list of keys."""
    valid_keys = ['node', 'peer', 'net', 'moon']
    if key_str not in valid_keys:
        logger.debug('Key type {} not valid'.format(key_str))
        return None
    key_types = [key for key in list(cache) if key_str in key]
    if not key_types:
        logger.debug('Key type {} not in cache'.format(key_str))
        return None
    else:
        return key_types


def get_endpoint_data(cache, key_str):
    """
    Get all data for key type from cache.
    :param cache: <cache> object
    :param key_str: desired 'key_str', one of
                    ['node'|'peer'|'net']
    :return tuple: (list of [keys], list of [values])
    """
    logger.debug('Entering get_endpoint_data with key_str: {}'.format(key_str))
    values = []
    key_list = find_keys(cache, key_str)
    if key_list:
        for key in key_list:
            with cache.transact():
                data = cache[key]
            values.append(data)
            logger.debug('Appending data for key: {}'.format(key))
    else:
        key_list = []
    logger.debug('Leaving get_endpoint_data')
    return (key_list, values)


def get_net_status(cache):
    """
    Get status data for node endpoint 'network' from cache, return a
    list of namedTuples.
    """
    networks = []  # list of network namedTuples
    Network = namedtuple('Network', 'identity status mac ztdevice gateway')
    key_list, values = get_endpoint_data(cache, 'net')
    if key_list:
        for key, data in zip(key_list, values):
            ztname = data.portDeviceName
            route = data.routes[1]['via']
            net_data = [data.id, data.status, data.mac, ztname, route]
            logger.debug('net list: {}'.format(net_data))
            netStatus = Network._make(net_data)
            networks.append(netStatus)
        logger.debug('netStatus list: {}'.format(networks))
    return networks


def get_node_status(cache):
    """
    Get data for node endpoint 'status' from cache, return a
    namedTuple.
    """
    node_data = []
    Node = namedtuple('Node', 'identity status tcpFallback worldId')
    key_list, values = get_endpoint_data(cache, 'node')
    if values:
        d = values[0]
        status = 'ONLINE' if d.online else 'OFFLINE'
        node_data = [d.address, status, d.tcpFallbackActive, d.planetWorldId]
        logger.debug('node list: {}'.format(node_data))
        nodeStatus = Node._make(node_data)
    else:
        nodeStatus = ()
    return nodeStatus


def get_peer_status(cache):
    """
    Get status data for node endpoint 'peer' from cache, return a
    list of namedTuples.
    """
    peers = []  # list of peer namedTuples
    Peer = namedtuple('Peer', 'identity role active address port')
    key_list, values = get_endpoint_data(cache, 'peer')
    if key_list:
        for key, data in zip(key_list, values):
            ifup = data.paths[0]['active']
            addr = data.paths[0]['address'].split('/', maxsplit=1)
            peer_data = [data.address, data.role, ifup, addr[0], addr[1]]
            logger.debug('peer list: {}'.format(peer_data))
            peerStatus = Peer._make(peer_data)
            peers.append(peerStatus)
        logger.debug('peerStatus list: {}'.format(peers))
    return peers


def load_cache_by_type(cache, data, key_str):
    """Load or update cache by key type string (uses find_keys)."""
    from itertools import zip_longest
    key_list = find_keys(cache, key_str)
    logger.debug('Entering load_cache with key_list: {}'.format(key_list))
    if not key_list:
        if 'node' in key_str:
            create_cache_entry(cache, data, key_str)
        else:
            for item in data:
                create_cache_entry(cache, item, key_str)
    else:
        if 'node' in str(key_list):
            for key in key_list:
                update_cache_entry(cache, data, key)
        else:
            for key, item in zip_longest(key_list, data):
                if not key:
                    create_cache_entry(cache, item, key_str)
                elif not item:
                    logger.debug('Removing cache entry for key: {}'.format(key))
                    with cache.transact():
                        del cache[key]
                else:
                    update_cache_entry(cache, item, key)
    key_list = find_keys(cache, key_str)
    logger.debug('Leaving load_cache with key_list: {}'.format(key_list))


def update_cache_entry(cache, data, key):
    """Update single cache entry by key."""
    new_data = AttrDict.from_nested_dict(data)
    if key.rstrip('-0123456789') in ('net', 'moon'):
        tgt = 'id'
    else:
        tgt = 'address'
    data_id = new_data[tgt]
    logger.info('New data has id: {}'.format(data_id))
    logger.debug('Updating cache entry for key: {}'.format(key))
    with cache.transact():
        cache[key] = new_data
