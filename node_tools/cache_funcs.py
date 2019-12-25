# coding: utf-8

"""cache-specific helper functions."""
import logging
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
    valid_keys = ['node', 'peer', 'net']
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
    :param: <cache> object
    :param: desired 'key_str', one of
            ['node'|'peer'|'net']
    :return: tuple (list of [keys], list of [values])
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


def get_node_status(cache, key_str):
    """
    Get status for node[type] from cache.
    """
    # from itertools import zip
    status_dict = {}
    key_list, values = get_endpoint_data(cache, key_str)
    if key_list:
        for key, data in zip(key_list, values):
            if 'net' in key:
                node_id = data.id
            else:
                node_id = data.address
            status_dict.update({'id': node_id})
            if 'node' in key:
                if data.online:
                    status_dict.update({'status': 'ONLINE'})
                else:
                    status_dict.update({'status': 'OFFLINE'})
                status_dict.update({'tcpFallback': data.tcpFallbackActive})
                logger.debug('node dict: {}'.format(status_dict))
            elif 'peer' in key:
                status_dict.update({'role': data.role})
                status_dict.update({'active': data.paths[0]['active']})
                addr = data.paths[0]['address'].split('/', maxsplit=1)
                status_dict.update({'ipAddress': addr[0]})
                status_dict.update({'ipPort': addr[1]})
                logger.debug('peer dict: {}'.format(status_dict))
            elif 'net' in key:
                status_dict.update({'status': data.status})
                status_dict.update({'mac': data.mac})
                status_dict.update({'device': data.portDeviceName})
                gw = data.routes[1]['via'] or None
                status_dict.update({'gateway': gw})
                logger.debug('net dict: {}'.format(status_dict))
    return status_dict


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
    if 'net' in str(key):
        tgt = 'id'
    else:
        tgt = 'address'
    old_id = new_data.get(tgt)
    logger.info('New data has id: {}'.format(old_id))
    logger.debug('Updating cache entry for key: {}'.format(key))
    with cache.transact():
        cache[key] = new_data
