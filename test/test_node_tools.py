# -*- coding: utf-8 -*-
import os
import time
import datetime
import logging
import ipaddress
# import mock
import unittest

import warnings
import pytest

from diskcache import Index

# from node_tools import state_data as stest
from node_tools.logger_config import setup_logging
from node_tools.helper_funcs import AttrDict
from node_tools.helper_funcs import ENODATA
from node_tools.helper_funcs import NODE_SETTINGS
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
from node_tools.cache_funcs import get_state
from node_tools.data_funcs import get_state_values
from node_tools.data_funcs import update_runner
from node_tools.network_funcs import get_net_cmds
from node_tools.network_funcs import run_net_cmd
from node_tools.node_funcs import get_moon_data
from node_tools.node_funcs import run_moon_cmd


try:
    from datetime import timezone
    utc = timezone.utc
except ImportError:
    from daemon.timezone import UTC
    utc = UTC()


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


class IPv4MethodsTest(unittest.TestCase):
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


class NetCmdTest(unittest.TestCase):
    """
    Simple test of find_the_net_script.
    """
    def setUp(self):
        super(NetCmdTest, self).setUp()
        self.bin_dir = os.getcwd() + '/bin'

    def test_bin_path(self):
        self.assertTrue(os.path.isdir(self.bin_dir))
        # print(self.bin_dir)

    def test_get_net_cmds(self):
        bin_path = self.bin_dir
        up0, down0, up1, down1 = get_net_cmds(bin_path)
        # print(type(up0))
        # print(up0)
        self.assertTrue(os.path.isfile(up0[0]))
        self.assertTrue(os.path.isfile(down0))
        self.assertTrue(os.path.isfile(up1))
        self.assertTrue(os.path.isfile(down1))

    def test_run_net_cmd(self):
        # bin_path = self.bin_dir
        # up0, _, _, _ = get_net_cmds(bin_path)
        state, res = run_net_cmd(['/bin/false'])
        self.assertFalse(state)
        # print(state)
        # print(res)


class StateChangeTest(unittest.TestCase):
    """
    Note the input for this test case is a pair of node fpnState
    objects (type is dict).
    """
    def setUp(self):
        super(StateChangeTest, self).setUp()
        from node_tools import state_data as stest

        self.default_state = stest.defState
        self.state = stest.fpnState

    def tearDown(self):
        from node_tools import state_data as s

        # defState = s.defState

        s.fpnState = self.default_state
        super(StateChangeTest, self).tearDown()

    def test_change_none(self):
        self.state = self.default_state
        self.assertIsInstance(self.state, dict)
        self.assertFalse(self.state['online'])
        self.assertFalse(self.state['fpn1'])

    def test_change_online(self):
        from node_tools import state_data as stest
        self.state.update(online=True)
        self.assertTrue(self.state['online'])
        self.assertFalse(self.state['fpn0'])
        self.assertFalse(self.state['fpn1'])

    def test_change_upfpn0(self):
        from node_tools import state_data as stest
        self.state.update(fpn0=True)
        self.assertTrue(self.state['online'])
        self.assertTrue(self.state['fpn0'])
        self.assertFalse(self.state['fpn1'])

    def test_change_upfpn1_downfpn0(self):
        from node_tools import state_data as stest
        self.state.update(fpn0=False, fpn1=True)
        self.assertTrue(self.state['online'])
        self.assertTrue(self.state['fpn1'])
        self.assertFalse(self.state['fpn0'])


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
    data_dir = get_cachedir(dir_name='fpn_data')
    (node_data, peer_data, net_data) = load_data()
    json_dump_file('node', node_data, data_dir)
    node_dump = json_load_file('node', data_dir)
    json_check(node_dump)
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
        del peer_data[0]
        load_cache_by_type(cache, peer_data, 'peer')
        assert len(list(cache)) == 5

    def test_update_cache_peer():
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
    test_update_cache_peer()
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


def test_load_node_state():
    Node = get_node_status(cache)
    load_cache_by_type(cache, Node, 'nstate')
    assert len(cache) == 10
    # print(list(cache))


def test_load_moon_state():
    moonStatus = []
    peers = get_peer_status(cache)
    for peer in peers:
        if peer['role'] == 'MOON':
            moonStatus.append(peer)
            break
    load_cache_by_type(cache, moonStatus, 'mstate')
    assert len(cache) == 11
    # print(list(cache))


def test_load_net_state():
    Node = get_net_status(cache)
    load_cache_by_type(cache, Node, 'istate')
    assert len(cache) == 13


def test_load_new_state():
    Node = get_net_status(cache)
    load_cache_by_type(cache, Node, 'istate')
    assert len(cache) == 13


def test_find_state_keys():
    data = find_keys(cache, 'state')
    assert len(data) == 4
    s = str(data)
    assert 'nstate' in s
    assert 'mstate' in s
    assert 'istate' in s
    # print(data)


def test_get_state():
    from node_tools import state_data as stest

    get_state(cache)
    nodeState = AttrDict.from_nested_dict(stest.fpnState)
    assert isinstance(nodeState, dict)
    assert nodeState['online']
    assert nodeState['fpn_id'] == 'ddfd7368e6'
    assert not nodeState['fallback']
    assert nodeState['fpn0']
    assert nodeState['fpn1']
    assert nodeState['moon_id0'] == 'deadd738e6'
    assert nodeState['fpn_id0'] == 'b6079f73c63cea29'
    assert nodeState['fpn_id1'] == '3efa5cb78a8129ad'
    # print(nodeState)


def test_get_state_values():
    from node_tools import state_data as stest

    assert isinstance(stest.changes, list)
    assert not stest.changes

    get_state(cache)
    prev_state = AttrDict.from_nested_dict(stest.fpnState)
    assert prev_state['online']
    assert prev_state['fpn0']
    assert prev_state['fpn1']

    # induce a change
    stest.fpnState.update(fpn1=False)
    next_state = AttrDict.from_nested_dict(stest.fpnState)
    assert not next_state['fpn1']
    assert not stest.changes

    # now we should see old/new values in the state diff
    get_state_values(prev_state, next_state, True)
    assert isinstance(stest.changes, list)
    assert len(stest.changes) == 1
    assert len(stest.changes[0]) == 2
    # print(stest.changes)

    # reset shared state vars
    stest.changes = []
    stest.fpnState.update(fpn1=True)
    assert stest.fpnState == prev_state

    # induce two changes
    stest.fpnState.update(fpn0=False, fpn1=False)
    next_state = AttrDict.from_nested_dict(stest.fpnState)
    assert not next_state['fpn0']
    assert not next_state['fpn1']
    assert not stest.changes

    # now we should see only new values for both changes in the state diff
    get_state_values(prev_state, next_state)
    assert isinstance(stest.changes, list)
    assert len(stest.changes) == 2
    assert len(stest.changes[0]) == 2
    # print(stest.changes)
