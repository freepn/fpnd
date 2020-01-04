# -*- coding: utf-8 -*-
import time
import datetime
import logging
import ipaddress
# import mock
import unittest

import warnings
import pytest

from diskcache import Index

from node_tools.logger_config import setup_logging
from node_tools.helper_funcs import ENODATA, NODE_SETTINGS
from node_tools.helper_funcs import find_ipv4_iface
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
        assert peer['paths'][0]['active']
        # assert active


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


def test_deorbit_moon():
    res = run_moon_cmd('deadd738e6', action='deorbit')
    assert res is False


def test_unorbit_moon():
    res = run_moon_cmd('deadd738e6', action='unorbit')
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
        assert len(list(cache)) == 1

    def test_update_cache_node():
        _, node_data = client.get_data('status')
        load_cache_by_type(cache, node_data, 'node')
        assert len(list(cache)) == 1

    def test_load_cache_peer():
        _, peer_data = client.get_data('peer')
        load_cache_by_type(cache, peer_data, 'peer')
        assert len(list(cache)) == 6

    def test_load_cache_net():
        _, net_data = client.get_data('network')
        load_cache_by_type(cache, net_data, 'net')
        assert len(list(cache)) == 8

    def test_update_cache_net():
        _, net_data = client.get_data('network')
        del net_data[1]
        load_cache_by_type(cache, net_data, 'net')
        assert len(list(cache)) == 7

    def test_find_keys_nonet():
        assert find_keys(cache, 'net') is None

    def test_find_keys():
        tuna = find_keys(cache, 'tuna')
        assert tuna is None
        node = find_keys(cache, 'node')
        assert 'node' in str(node)
        net = find_keys(cache, 'net')
        assert len(net) == 2

    def test_update_runner():
        res = update_runner()

    def test_cache_size():
        assert len(cache) == 9

    test_cache_is_empty()
    test_load_cache_node()
    test_update_cache_node()
    test_load_cache_peer()
    test_find_keys_nonet()
    test_load_cache_net()
    test_update_cache_net()
    test_load_cache_net()
    test_find_keys()
    test_update_runner()
    test_cache_size()


def test_get_node_status():
    Node = get_node_status(cache)
    assert isinstance(Node, dict)
    assert 'status' in Node
    assert 'tcpFallback' in Node
    assert Node['tcpFallback'] is False


def test_get_peer_status():
    peers = get_peer_status(cache)
    assert isinstance(peers, list)
    for Peer in peers:
        assert isinstance(Peer, dict)
        assert 'role' in Peer
        assert 'address' in Peer
        assert Peer['active'] is True


def test_get_net_status():
    nets = get_net_status(cache)
    assert isinstance(nets, list)
    for Net in nets:
        assert isinstance(Net, dict)
        assert 'mac' in Net
        assert 'ztaddress' in Net
        assert 'gateway' in Net


def test_load_node_status():
    Node = get_node_status(cache)
    load_cache_by_type(cache, Node, 'nstate')
    assert len(cache) == 10
    # print(list(cache))


def test_load_moon_status():
    moonStatus = []
    peers = get_peer_status(cache)
    for peer in peers:
        if peer['role'] == 'MOON':
            moonStatus.append(peer)
            break
    load_cache_by_type(cache, moonStatus, 'mstate')
    assert len(cache) == 11
    # print(list(cache))


class BasicConfigTest(unittest.TestCase):

    """Basic tests for logger_config.py"""

    def setUp(self):
        super(BasicConfigTest, self).setUp()
        self.handlers = logging.root.handlers
        self.saved_handlers = logging._handlers.copy()
        self.saved_handler_list = logging._handlerList[:]
        self.original_logging_level = logging.root.level
        self.addCleanup(self.cleanup)
        logging.root.handlers = []

    def tearDown(self):
        for h in logging.root.handlers[:]:
            logging.root.removeHandler(h)
            h.close()
        super(BasicConfigTest, self).tearDown()

    def cleanup(self):
        setattr(logging.root, 'handlers', self.handlers)
        logging._handlers.clear()
        logging._handlers.update(self.saved_handlers)
        logging._handlerList[:] = self.saved_handler_list
        logging.root.level = self.original_logging_level

    def test_debug_level(self):
        old_level = logging.root.level
        self.addCleanup(logging.root.setLevel, old_level)

        debug = True
        setup_logging(debug, '/dev/null')
        self.assertEqual(logging.root.level, logging.DEBUG)
        # Test that second call has no effect
        logging.basicConfig(level=58)
        self.assertEqual(logging.root.level, logging.DEBUG)

    def test_info_level(self):
        old_level = logging.root.level
        self.addCleanup(logging.root.setLevel, old_level)

        debug = False
        setup_logging(debug, '/dev/null')
        self.assertEqual(logging.root.level, logging.INFO)
        # Test that second call has no effect
        logging.basicConfig(level=58)
        self.assertEqual(logging.root.level, logging.INFO)


class TestIPv4Methods(unittest.TestCase):
    """
    Note the input for this test case is an ipaddress.IPv4Interface
    object.
    """
    def test_strip(self):
        """Return IPv4 addr without prefix"""
        strip = find_ipv4_iface('192.168.1.1/24')
        self.assertEqual(strip, '192.168.1.1')

    def test_nostrip(self):
        """Return True if IPv4 addr is valid"""
        nostrip = find_ipv4_iface('192.168.1.1/24', False)
        self.assertTrue(nostrip)

    def test_bogus(self):
        """Return False if IPv4 addr is not valid"""
        bogus_addr = find_ipv4_iface('192.168.1.300/24', False)
        self.assertFalse(bogus_addr)
