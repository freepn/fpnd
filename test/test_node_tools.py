# -*- coding: utf-8 -*-
import os
import sys
import time
import shutil
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
from node_tools.helper_funcs import check_and_set_role
from node_tools.helper_funcs import config_from_ini
from node_tools.helper_funcs import do_setup
from node_tools.helper_funcs import find_ipv4_iface
from node_tools.helper_funcs import get_cachedir
from node_tools.helper_funcs import get_filepath
from node_tools.helper_funcs import json_dump_file
from node_tools.helper_funcs import json_load_file
from node_tools.helper_funcs import log_fpn_state
from node_tools.helper_funcs import run_event_handlers
from node_tools.helper_funcs import update_state
from node_tools.helper_funcs import validate_role
from node_tools.helper_funcs import xform_state_diff
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
from node_tools.node_funcs import control_daemon
from node_tools.node_funcs import get_moon_data
from node_tools.node_funcs import run_moon_cmd
from node_tools.sched_funcs import check_return_status


try:
    from datetime import timezone
    utc = timezone.utc
except ImportError:
    from daemon.timezone import UTC
    utc = UTC()


# unittest-based test cases
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


class CheckReturnsTest(unittest.TestCase):
    """
    Tests for check_return_status().
    """
    def test_bad_returns(self):
        naughty_list = [1, (), '', [], {}, {False: 'blarg'}, False, None]
        for thing in naughty_list:
            # print(thing)
            self.assertFalse(check_return_status(thing))

    def test_int_return(self):
        self.assertTrue(check_return_status(0))
        self.assertFalse(check_return_status(1))

    def test_bool_return(self):
        self.assertTrue(check_return_status(True))
        self.assertFalse(check_return_status(False))

    def test_string_return(self):
        self.assertFalse(check_return_status('blurt'))
        good_list = ['OK', 'Success', 'UP', 'good']
        for thing in good_list:
            self.assertTrue(check_return_status(thing))

    def test_multiple_returns(self):
        self.assertTrue(check_return_status((True, 'Success', 0)))
        self.assertFalse(check_return_status((False, 'blarg', 1)))


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
        self.bin_dir = os.path.join(os.getcwd(), 'bin')

    def test_bin_path(self):
        # print(self.bin_dir)
        self.assertTrue(os.path.isdir(self.bin_dir))

    def test_get_net_cmds_false(self):
        bin_path = '/bin'
        self.assertIsNone(get_net_cmds(bin_path))

    def test_get_net_cmds_true(self):
        up0, down0, up1, down1 = get_net_cmds(self.bin_dir)
        # print(up0)
        self.assertTrue(os.path.isfile(up0))
        self.assertTrue(os.path.isfile(down0))
        self.assertTrue(os.path.isfile(up1))
        self.assertTrue(os.path.isfile(down1))

    def test_get_net_cmds_single(self):
        cmd = get_net_cmds(self.bin_dir, 'fpn0')
        path, name = os.path.split(cmd[0])
        self.assertEqual(name, 'fpn0-down.sh')

    def test_get_net_cmds_single_up(self):
        cmd = get_net_cmds(self.bin_dir, 'fpn1', True)
        path, name = os.path.split(cmd[0])
        self.assertEqual(name, 'fpn1-setup.sh')


class SetRolesTest(unittest.TestCase):
    """
    Tests for check_and_set_role() and validate_role().
    """
    def setUp(self):
        super(SetRolesTest, self).setUp()
        from node_tools import state_data as st

        self.saved_state = AttrDict.from_nested_dict(st.fpnState)
        self.default_state = AttrDict.from_nested_dict(st.defState)
        self.state = st.fpnState
        # self.state.update(online=False)

        self.role = NODE_SETTINGS['node_role']
        self.parent_dir = os.path.join(os.getcwd(), 'test/role_test')
        self.ctlr = 'bb8dead3c63cea29.json'
        self.ctlr_dir = os.path.join(self.parent_dir, 'controller.d', 'network')
        self.ctlr_file = os.path.join(self.ctlr_dir, self.ctlr)
        self.moon = '000000' + NODE_SETTINGS['moon_list'][0] + '.moon'
        self.moon_dir = os.path.join(self.parent_dir, 'moons.d')
        self.moon_file = os.path.join(self.moon_dir, self.moon)
        self.createDirs()
        self.addCleanup(self.cleanDirs)

    def tearDown(self):
        from node_tools import state_data as st

        st.fpnState = self.saved_state
        NODE_SETTINGS['node_role'] = None
        super(SetRolesTest, self).tearDown()

    def createDirs(self):
        os.makedirs(self.parent_dir, exist_ok=False)

    def cleanDirs(self):
        shutil.rmtree(self.parent_dir)

    def test_ctlr_role(self):
        self.assertIsNone(self.role)
        os.makedirs(self.ctlr_dir, exist_ok=False)

        with open(self.ctlr_file, "w") as file:
            file.write('')
        result = check_and_set_role('controller', path=self.parent_dir)
        self.assertTrue(result)
        self.assertEqual(NODE_SETTINGS['node_role'], 'controller')

        validate_role()
        self.assertIsNone(NODE_SETTINGS['node_role'])

        # print(NODE_SETTINGS)
        NODE_SETTINGS['ctlr_list'].append(self.state['fpn_id'])
        validate_role()
        self.assertEqual(NODE_SETTINGS['node_role'], 'controller')

    def test_moon_role(self):
        self.assertIsNone(self.role)
        os.makedirs(self.moon_dir, exist_ok=False)

        with open(self.moon_file, "w") as file:
            file.write('')
        result = check_and_set_role('moon', path=self.parent_dir)
        self.assertFalse(result)
        self.assertIsNone(NODE_SETTINGS['node_role'])

        self.state.update(online=True,
                          fpn_id='ddfd7368e6',
                          moon_id0='deadd738e6')
        NODE_SETTINGS['node_role'] = 'moon'
        validate_role()
        self.assertIsNone(NODE_SETTINGS['node_role'])
        NODE_SETTINGS['moon_list'].append(self.state['fpn_id'])
        validate_role()
        self.assertEqual(NODE_SETTINGS['node_role'], 'moon')
        self.assertEqual(NODE_SETTINGS['node_runner'], 'peerstate.py')

    def test_passing_path(self):
        self.assertTrue(os.path.isdir(self.parent_dir))
        result = check_and_set_role('foobar', path=self.parent_dir)
        self.assertFalse(result)

    @pytest.mark.xfail(raises=PermissionError)
    def test_passing_nothing(self):
        result = check_and_set_role('foobar')
        self.assertFalse(result)


class StateChangeTest(unittest.TestCase):
    """
    Note the input for this test case is a pair of node fpnState
    objects (type is dict).
    """
    def setUp(self):
        super(StateChangeTest, self).setUp()
        from node_tools import state_data as st

        self.saved_state = AttrDict.from_nested_dict(st.fpnState)
        self.default_state = AttrDict.from_nested_dict(st.defState)
        self.state = st.fpnState

    def tearDown(self):
        from node_tools import state_data as st

        # defState = s.defState

        st.fpnState = self.saved_state
        super(StateChangeTest, self).tearDown()

    def show_state(self):
        from node_tools import state_data as st

        print('')
        print(self.default_state)
        print(self.state)

    def test_change_none(self):
        # self.show_state()
        # self.state = self.default_state
        self.assertIsInstance(self.state, dict)
        self.assertFalse(self.state['online'])
        self.assertFalse(self.state['fpn1'])

    def test_change_online(self):
        self.state.update(online=True)
        self.assertTrue(self.state['online'])
        self.assertFalse(self.state['fpn0'])
        self.assertFalse(self.state['fpn1'])

    def test_change_upfpn0(self):
        self.state.update(online=True, fpn0=True)
        self.assertTrue(self.state['online'])
        self.assertTrue(self.state['fpn0'])
        self.assertFalse(self.state['fpn1'])

    def test_change_upfpn1_downfpn0(self):
        self.state.update(online=True, fpn0=False, fpn1=True)
        self.assertTrue(self.state['online'])
        self.assertFalse(self.state['fpn0'])
        self.assertTrue(self.state['fpn1'])


class XformStateDataTest(unittest.TestCase):
    """
    Tests for state data transformation: xform_state_diff()
    """
    def setUp(self):
        super(XformStateDataTest, self).setUp()
        self.one_new = [('fpn1', False)]
        self.old_new = [(('fpn1', True), ('fpn1', False))]
        self.two_new = [('fpn0', True), ('fpn1', True),
                        ('fpn_id0', 'bb8dead3c63cea29'),
                        ('fpn_id1', '7ac4235ec5d3d938')]
        self.none = []

    def test_return_none(self):
        self.assertIsInstance(xform_state_diff(self.none), dict)

    def test_return_old_new(self):
        diff = xform_state_diff(self.old_new)
        self.assertIsInstance(diff, dict)
        self.assertTrue(diff.old_fpn1)
        self.assertFalse(diff.new_fpn1)

    def test_return_one_new(self):
        diff = xform_state_diff(self.one_new)
        self.assertFalse(diff.fpn1)

    def test_return_two_new(self):
        diff = xform_state_diff(self.two_new)
        self.assertTrue(diff.fpn0)
        self.assertEqual(diff.fpn_id0, 'bb8dead3c63cea29')


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
cache = Index(get_cachedir(dir_name='fpn_test'))
max_age = NODE_SETTINGS['max_cache_age']
utc_stamp = datetime.datetime.now(utc)  # use local time for console

client = mock_zt_api_client()


# pytest-based test cases using capture
# NOTE these tests cannot be run using unittest.TestCase since the
# function under test is actually calling a separate daemon with its
# own context (thus capsys will not work either, so we use capfd)
def test_file_is_found(capfd):
    """
    Test if we can find the msg_responder daemon.
    """
    NODE_SETTINGS['home_dir'] = os.path.join(os.getcwd(), 'scripts')
    res = control_daemon('fart')
    captured = capfd.readouterr()
    assert res == 2
    assert 'Unknown command' in captured.out


def test_daemon_can_start(capfd):
    """
    Test if we can start the msg_responder daemon.
    """
    NODE_SETTINGS['home_dir'] = os.path.join(os.getcwd(), 'scripts')
    res = control_daemon('start')
    captured = capfd.readouterr()
    # print(res)
    assert res == 0
    assert 'Starting' in captured.out


def test_daemon_can_stop(capfd):
    """
    Test if we can stop the msg_responder daemon.
    """
    NODE_SETTINGS['home_dir'] = os.path.join(os.getcwd(), 'scripts')
    res = control_daemon('stop')
    captured = capfd.readouterr()
    assert res == 0
    assert 'Stopped' in captured.out


# @pytest.mark.xfail(raises=PermissionError)
def test_path_ecxeption(capfd):
    """
    Test if we can generate an exception (yes we can, so now we don't
    need to raise it).
    """
    NODE_SETTINGS['home_dir'] = os.path.join(os.getcwd(), '/root')
    res = control_daemon('restart')
    captured = capfd.readouterr()
    assert not res
    assert not captured.out


# special test cases
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
    data_dir = get_cachedir(dir_name='fpn_test')
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


def test_should_be_enodata():
    def should_be_enodata():
        res = update_state()
        return res

    res = should_be_enodata()
    assert res is ENODATA


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
        res = update_runner()
        assert res is ENODATA
        # print(res)

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
        _, net_data = client.get_data('network')
        load_cache_by_type(cache, net_data, 'net')
        assert len(list(cache)) == 8

    def test_find_keys_nonet():
        assert find_keys(cache, 'net') is None

    def test_update_runner():
        res = update_runner()
        assert res is ENODATA
        # print(res)

    def test_cache_size():
        assert len(cache) == 8

    test_cache_is_empty()
    test_load_cache_node()
    test_update_cache_node()
    test_load_cache_peer()
    test_update_cache_peer()
    test_find_keys_nonet()
    test_load_cache_net()
    test_update_cache_net()
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
    assert len(cache) == 9
    # print(list(cache))


def test_load_moon_state():
    moonStatus = []
    peers = get_peer_status(cache)
    for peer in peers:
        if peer['role'] == 'MOON':
            moonStatus.append(peer)
            break
    load_cache_by_type(cache, moonStatus, 'mstate')
    assert len(cache) == 10


def test_load_net_state():
    Node = get_net_status(cache)
    load_cache_by_type(cache, Node, 'istate')
    assert len(cache) == 12


def test_load_new_state():
    Node = get_net_status(cache)
    load_cache_by_type(cache, Node, 'istate')
    assert len(cache) == 12


def test_find_keys():
    tuna = find_keys(cache, 'tuna')
    assert tuna is None
    node = find_keys(cache, 'node')
    assert 'node' in str(node)
    net = find_keys(cache, 'net')
    assert len(net) == 2


def test_find_state_keys():
    data = find_keys(cache, 'state')
    assert len(data) == 4
    s = str(data)
    assert 'nstate' in s
    assert 'mstate' in s
    assert 'istate' in s


def test_get_state():
    from node_tools import state_data as stest

    get_state(cache)
    nodeState = AttrDict.from_nested_dict(stest.fpnState)
    assert isinstance(nodeState, dict)
    assert nodeState.online
    assert nodeState.fpn_id == 'ddfd7368e6'
    assert not nodeState.fallback
    assert nodeState.fpn0
    assert nodeState.fpn1
    assert nodeState.moon_id0 == 'deadd738e6'
    assert nodeState['fpn_id0'] == 'b6079f73c63cea29'
    assert nodeState['fpn_id1'] == '3efa5cb78a8129ad'


def test_get_state_values():
    from node_tools import state_data as stest

    assert isinstance(stest.changes, list)
    assert not stest.changes

    get_state(cache)
    prev_state = AttrDict.from_nested_dict(stest.fpnState)
    assert prev_state.online
    assert prev_state.fpn0
    assert prev_state.fpn1

    # induce a change
    stest.fpnState.update(fpn1=False)
    next_state = AttrDict.from_nested_dict(stest.fpnState)
    assert not next_state.fpn1
    assert not stest.changes

    # now we should see old/new values in the state diff
    get_state_values(prev_state, next_state, True)
    assert isinstance(stest.changes, tuple)
    assert len(stest.changes) == 1
    assert len(stest.changes[0]) == 2
    get_state_values(prev_state, next_state)
    assert len(stest.changes[0]) == 2

    # reset shared state vars
    stest.changes = []
    stest.fpnState.update(fpn1=True)
    assert stest.fpnState == prev_state

    # induce two changes
    stest.fpnState.update(fpn0=False, fpn1=False)
    next_state = AttrDict.from_nested_dict(stest.fpnState)
    assert not next_state.fpn0
    assert not next_state.fpn1
    assert not stest.changes

    # now we should see only new values for both changes in the state diff
    get_state_values(prev_state, next_state)
    assert isinstance(stest.changes, tuple)
    assert len(stest.changes) == 2
    assert len(stest.changes[0]) == 2
    # reset shared state vars
    stest.changes = []


def test_run_event_handler():
    from node_tools import state_data as st

    home, pid_file, log_file, debug, msg = do_setup()

    prev_state = AttrDict.from_nested_dict(st.defState)
    next_state = AttrDict.from_nested_dict(st.defState)
    assert not st.changes

    get_state_values(prev_state, next_state)
    run_event_handlers(st.changes)
    assert len(st.changes) == 0

    next_state.update(fpn0=True, fpn1=True)
    get_state_values(prev_state, next_state)
    run_event_handlers(st.changes)
    log_fpn_state(st.changes)
    assert len(st.changes) == 2
