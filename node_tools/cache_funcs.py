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
    key_types = ['node', 'peer', 'net']
    if key_str not in key_types:
        logger.debug('Key type {} not valid'.format(key_str))
        return None
    valid_keys = [key for key in list(cache) if key_str in key]
    if not valid_keys:
        logger.debug('Key type {} not in cache'.format(key_str))
        # logger.error('valid_keys: {}'.format(valid_keys))
        return None
    else:
        return valid_keys


def get_node_status():
    """Get node ID and status from cache."""
    raise NotImplementedError


def load_cache_by_type(cache, data, key_str):
    """Load or update cache by key type string (uses find_keys)."""
    from itertools import zip_longest
    key_list = find_keys(cache, key_str)
    logger.debug('Starting load_cache with key_list: {}'.format(key_list))
    if not key_list:
        if 'node' in key_str:
            create_cache_entry(cache, data, key_str)
        else:
            for item in data:
                create_cache_entry(cache, item, key_str)
    else:
        if 'node' in str(key_list):
            key, _ = cache.pull(prefix=key_str)
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
    old_id = new_data.get('address')
    logger.error('New data has address: {}'.format(old_id))
    logger.debug('Updating cache entry for key: {}'.format(key))
    with cache.transact():
        cache[key] = new_data
