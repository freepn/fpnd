# coding: utf-8

"""cache-specific helper functions."""
import logging
from node_tools.helper_funcs import AttrDict


logger = logging.getLogger(__name__)


def find_key(cache, key_str):
    """Find key(s) in cache using key type string, return list of keys."""
    key_types = ['node', 'peer', 'net']
    if key_str not in key_types:
        logger.error('Key type {} not allowed'.format(key_str))
        return None
    cache_keys = list(cache)
    valid_keys = [key for key in cache_keys if key_str in key]
    return valid_keys


def get_node_status():
    """Get node ID and status from cache."""


def update_net_data(cache, data):
    """Load or update network data for all networks."""


def update_node_data(cache, data):
    """Load or update node status data."""
    keys = list(cache)
    node_data = AttrDict.from_nested_dict(data)
    old_id = node_data.get('address')
    if any(old_id in key for key in keys):
        del cache[old_id]
    if any("node" in key for key in keys):
        key_list = [key for key in keys if 'node' in key]
        if len(key_list) == 1:
            cache[key_list[0]] = node_data
    else:
        cache.push(node_data, prefix='node')


def update_peer_data(cache, data):
    """Load or update peer data for all peers."""
