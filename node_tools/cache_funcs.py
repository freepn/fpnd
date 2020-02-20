# coding: utf-8

"""cache-specific helper functions."""
import logging
from collections import namedtuple

from node_tools.helper_funcs import AttrDict
from node_tools.helper_funcs import NODE_SETTINGS
from node_tools.helper_funcs import find_ipv4_iface


logger = logging.getLogger(__name__)


def create_cache_entry(cache, data, key_str):
    """
    Load new cache entry by key type.
    :param cache: Index <cache> object
    :param data: payload data in a dictionary
    :param key_str: desired 'key_str', one of
                    ['node'|'peer'|'net'|'mbr'|'moon'] or
                    ['nstate'|'mstate'|'istate']
    """
    new_data = AttrDict.from_nested_dict(data)
    logger.debug('Pushing entry for: {}'.format(key_str))
    with cache.transact():
        key = cache.push(new_data, prefix=key_str)
    logger.debug('New key created for: {}'.format(key))


def delete_cache_entry(cache, key_str):
    """
    Delete cache entry by key type.
    :param cache: Index <cache> object
    :param key_str: desired 'key_str', one of
                    ['node'|'peer'|'net'|'mbr'|'moon'] or
                    ['nstate'|'mstate'|'istate']
    """
    key_list = find_keys(cache, key_str)
    if key_list:
        for key in key_list:
            logger.debug('Deleting entry for: {}'.format(key))
            with cache.transact():
                del cache[key]
        logger.debug('Deleted cache items matching: {}'.format(key_str))
    else:
        logger.warning('No matchine keys found for: {}'.format(key_str))


def find_keys(cache, key_str):
    """Find API key(s) in cache using key type string, return list of keys."""
    valid_strings = ['node', 'peer', 'moon', 'net', 'mbr', 'nstate', 'mstate', 'istate']
    match_list = [key for key in valid_strings if key_str in key]
    if not match_list:
        logger.debug('Key type {} not valid'.format(key_str))
        return None
    key_list = [key for key in list(cache) if key_str in key]
    if not key_list:
        logger.debug('Key type {} not in cache'.format(key_str))
        return None
    else:
        return key_list


def get_endpoint_data(cache, key_str):
    """
    Get all data for key type from cache (can be endpoint or state).
    :param cache: Index <cache> object
    :param key_str: desired 'key_str', one of
                    ['node'|'peer'|'net'|'mbr'|'moon'] or
                    ['nstate'|'mstate'|'istate']
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
    return (key_list, values)


def get_net_status(cache):
    """
    Get user node status data for 'network' endpoint from cache, return
    list of dictionaries.
    NOTE: Not valid for networks under the 'controller' endpoint.
    """
    networks = []  # list of network objects
    key_list, values = get_endpoint_data(cache, 'net')
    if key_list:
        for key, data in zip(key_list, values):
            # we need to check for missing route list here
            if data.routes:
                for addr in data.assignedAddresses:
                    if find_ipv4_iface(addr, False):
                        zt_addr = find_ipv4_iface(addr)
                        break
                netStatus = {'identity': data.id,
                             'status': data.status,
                             'mac': data.mac,
                             'ztdevice': data.portDeviceName,
                             'ztaddress': zt_addr,
                             'gateway': data.routes[1]['via']}
                networks.append(netStatus)
        logger.debug('netStatus list: {}'.format(networks))
    return networks


def get_node_status(cache):
    """
    Get data for 'status' endpoint from cache, return a dict.
    """
    nodeStatus = {}
    key_list, values = get_endpoint_data(cache, 'node')
    if values:
        d = values[0]
        status = 'ONLINE' if d.online else 'OFFLINE'
        nodeStatus = {'identity': d.address,
                      'status': status,
                      'tcpFallback': d.tcpFallbackActive,
                      'worldId': d.planetWorldId}
        logger.debug('nodeStatus dict: {}'.format(nodeStatus))
    return nodeStatus


def get_peer_status(cache):
    """
    Get status data for 'peer' endpoint from cache, return a
    list of dictionaries.
    """
    peers = []  # list of peer objects
    key_list, values = get_endpoint_data(cache, 'peer')
    if key_list:
        for key, data in zip(key_list, values):
            addr = data.paths[0]['address'].split('/', maxsplit=1)
            peerStatus = {'identity': data.address,
                          'role': data.role,
                          'active': data.paths[0]['active'],
                          'address': addr[0],
                          'port': addr[1]}
            peers.append(peerStatus)
        logger.debug('peerStatus list: {}'.format(peers))
    return peers


def get_state(cache):
    """
    Get state data from cache to build node state and update it.

    """
    from node_tools import state_data as st

    key_list, values = get_endpoint_data(cache, 'state')
    if key_list:
        d = {}
        for key, data in zip(key_list, values):
            if 'nstate' in str(key):
                if 'ONLINE' in data.status:
                    d['online'] = True
                d['fpn_id'] = data.identity
                d['fallback'] = data.tcpFallback
            if 'mstate' in str(key) and not NODE_SETTINGS['node_role']:
                d['moon_id0'] = data.identity
                d['moon_addr'] = data.address
            if 'istate' in str(key) and 'OK' in data.status:
                if data.ztaddress == data.gateway:
                    d['fpn1'] = True
                    d['fpn_id1'] = data.identity
                else:
                    d['fpn0'] = True
                    d['fpn_id0'] = data.identity
            else:
                d.update(fpn0=None, fpn1=None, fpn_id0=None, fpn_id1=None)
        st.fpnState.update(d)
        logger.debug('fpnState: {}'.format(st.fpnState))


def handle_node_status(data, cache):
    """
    Cache handling/state update for node status data (common to all roles).
    :param data: ZT client data from 'status' endpoint
    :param cache: Index <cache> object
    """
    node_id = data.get('address')
    logger.debug('Found node: {}'.format(node_id))
    load_cache_by_type(cache, data, 'node')
    logger.debug('Returned {} key is: {}'.format('node', find_keys(cache, 'node')))

    nodeStatus = get_node_status(cache)
    logger.debug('Got node state: {}'.format(nodeStatus))
    load_cache_by_type(cache, nodeStatus, 'nstate')

    return node_id


def load_cache_by_type(cache, data, key_str):
    """Load or update cache by key type string (uses find_keys)."""
    from itertools import zip_longest
    key_list = find_keys(cache, key_str)
    if not key_list:
        if key_str in ('node', 'nstate'):
            create_cache_entry(cache, data, key_str)
        else:
            for item in data:
                create_cache_entry(cache, item, key_str)
    else:
        if key_str in ('node', 'nstate'):
            update_cache_entry(cache, data, key_list[0])
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


def update_cache_entry(cache, data, key):
    """
    Update single cache entry by key.
    :param cache: <cache> object
    :param data: payload data in a dictionary
    :param key_str: desired 'key_str', one of
                    ['node'|'peer'|'net'|'mbr'|'moon'] or
                    ['nstate'|'mstate'|'istate']
    """
    new_data = AttrDict.from_nested_dict(data)
    if 'state' in key.rstrip('-0123456789'):
        tgt = 'identity'
    elif key.rstrip('-0123456789') in ('net', 'moon'):
        tgt = 'id'
    else:
        tgt = 'address'
    data_id = new_data[tgt]
    logger.debug('New data has id: {}'.format(data_id))
    logger.debug('Updating cache entry for key: {}'.format(key))
    with cache.transact():
        cache[key] = new_data
