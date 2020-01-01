# -*- coding: utf-8 -*-
import time
import datetime
# import mock
# import unittest

import warnings
import pytest

from diskcache import Index

from node_tools.helper_funcs import ENODATA, NODE_SETTINGS
from node_tools.helper_funcs import get_cachedir
from node_tools.helper_funcs import json_dump_file
from node_tools.helper_funcs import json_load_file
from node_tools.helper_funcs import update_state
from node_tools.cache_funcs import find_keys
from node_tools.cache_funcs import load_cache_by_type
from node_tools.cache_funcs import get_endpoint_data
from node_tools.cache_funcs import get_net_status
from node_tools.cache_funcs import get_node_status
from node_tools.cache_funcs import get_peer_status
from node_tools.data_funcs import update_runner
from node_tools.node_funcs import get_moon_data
from node_tools.node_funcs import run_moon_cmd


try:
    from datetime import timezone
    utc = timezone.utc
except ImportError:
    from daemon.timezone import UTC
    utc = UTC()


class mock_zt_api_client(object):
    """
    Client API to serve test data endpoints
    """
    def __init__(self):
        self.test_dir = 'test/test_data'
        self.response = '200'

    def get_data(self, endpoint):
        self.endpoint = json_load_file(endpoint, self.test_dir)
        return self.response, self.endpoint


# has_aging = False
cache = Index(get_cachedir())
max_age = NODE_SETTINGS['max_cache_age']
utc_stamp = datetime.datetime.now(utc)  # use local time for console

client = mock_zt_api_client()


def json_check(data):
    import json

    json_dump = json.dumps(data, indent=4, separators=(',', ': '))
    json_load = json.loads(json_dump)
    assert data == json_load


def load_data():
    _, node = client.get_data('status')
    _, peers = client.get_data('peer')
    _, nets = client.get_data('network')
    return node, peers, nets


def test_dump_and_load_json():
    (node_data, peer_data, net_data) = load_data()
    json_check(node_data)
    json_check(peer_data)
    json_check(net_data)


def test_node_client_status():
    _, node_data = client.get_data('status')
    status = node_data.get('online')
    assert status


def test_peer_client_status():
    _, peer_data = client.get_data('peer')
    for peer in peer_data:
        active = peer['paths'][0]['active']
        assert active


def test_net_client_status():
    _, net_data = client.get_data('network')
    for net in net_data:
        status = net.get('status')
        assert status == 'OK'


def test_get_moon_data():
    res = get_moon_data()
    # print(res)
    assert isinstance(res, list)


def test_orbit_moon():
    res = run_moon_cmd('deadd738e6', action='orbit')
    assert res is False


def should_be_enodata():
    res = update_runner()
    return res


def test_should_be_enodata():
    res = should_be_enodata()
    assert res == ENODATA


def test_api_warning_msg():
    with pytest.warns(UserWarning):
        warnings.warn("Cannot connect to ZeroTier API", UserWarning)


def test_enodata_warning_msg():
    with pytest.warns(UserWarning):
        warnings.warn("Cache empty and API returned ENODATA", UserWarning)


def test_aging_not_available_warning_msg():
    with pytest.warns(UserWarning):
        warnings.warn("Cache aging not available", UserWarning)


def test_cache_loading():

    def test_cache_is_empty():
        cache.clear()
        assert list(cache) == []

    def test_load_cache_node():
        _, node_data = client.get_data('status')
        load_cache_by_type(cache, node_data, 'node')

    def test_load_cache_peer():
        _, peer_data = client.get_data('peer')
        load_cache_by_type(cache, peer_data, 'peer')

    def test_load_cache_net():
        _, net_data = client.get_data('network')
        load_cache_by_type(cache, net_data, 'net')
        assert len(list(cache)) != 0

    def test_find_keys_nonet():
        assert find_keys(cache, 'net') is None

    def test_find_keys():
        tuna = find_keys(cache, 'tuna')
        assert tuna is None
        node = find_keys(cache, 'node')
        assert 'node' in str(node)
        net = find_keys(cache, 'net')
        assert len(net) == 2

    def test_cache_size():
        size = len(cache)
        assert size == 8

    test_cache_is_empty()
    test_load_cache_node()
    test_load_cache_peer()
    test_find_keys_nonet()
    test_load_cache_net()
    test_find_keys()
    test_cache_size()


def test_get_node_status():
    Node = get_node_status(cache)
    assert isinstance(Node, tuple)
    assert hasattr(Node, 'status')
    assert hasattr(Node, 'tcpFallback')
    assert Node.tcpFallback is False


def test_get_peer_status():
    peers = get_peer_status(cache)
    assert isinstance(peers, list)
    for Peer in peers:
        assert isinstance(Peer, tuple)
        assert hasattr(Peer, 'role')
        assert Peer.active is True
        assert hasattr(Peer, 'address')


def test_get_net_status():
    nets = get_net_status(cache)
    assert isinstance(nets, list)
    for Net in nets:
        assert isinstance(Net, tuple)
        assert hasattr(Net, 'mac')
        assert hasattr(Net, 'gateway')


# res = update_state()
# res = update_runner()
