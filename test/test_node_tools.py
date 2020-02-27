# -*- coding: utf-8 -*-
import os
import sys
import time
import shutil
import datetime
import logging
import ipaddress
# import mock
import string
import tempfile
import unittest
import warnings

import datrie
import pytest

from diskcache import Index

from node_tools.ctlr_funcs import check_net_trie
from node_tools.ctlr_funcs import create_state_trie
from node_tools.ctlr_funcs import gen_netobj_queue
from node_tools.ctlr_funcs import ipnet_get_netcfg
from node_tools.ctlr_funcs import load_state_trie
from node_tools.ctlr_funcs import name_generator
from node_tools.ctlr_funcs import netcfg_get_ipnet
from node_tools.ctlr_funcs import save_state_trie
from node_tools.helper_funcs import AttrDict
from node_tools.helper_funcs import ENODATA
from node_tools.helper_funcs import NODE_SETTINGS
from node_tools.helper_funcs import find_ipv4_iface
from node_tools.helper_funcs import get_filepath
from node_tools.helper_funcs import set_initial_role
from node_tools.helper_funcs import startup_handlers
from node_tools.helper_funcs import validate_role
from node_tools.helper_funcs import xform_state_diff
from node_tools.logger_config import setup_logging
from node_tools.msg_queues import handle_announce_msg
from node_tools.msg_queues import handle_node_queues
from node_tools.msg_queues import manage_incoming_nodes
from node_tools.msg_queues import valid_announce_msg
from node_tools.network_funcs import get_net_cmds
from node_tools.node_funcs import control_daemon
from node_tools.node_funcs import run_subscriber_daemon
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


class IPv4InterfaceTest(unittest.TestCase):
    """
    Note the input for this test case is the input string for a Python
    ipaddress.IPv4Interface object.
    """
    def test_strip(self):
        """Return IPv4 addr without prefix"""
        strip = find_ipv4_iface('192.168.1.1/24')
        self.assertEqual(strip, '192.168.1.1')

    def test_nostrip(self):
        """Return True if IPv4 addr is valid"""
        nostrip = find_ipv4_iface('172.16.0.241' + '/30', False)
        self.assertTrue(nostrip)

    def test_bogus(self):
        """Return False if IPv4 addr is not valid"""
        bogus_addr = find_ipv4_iface('192.168.1.300/24', False)
        self.assertFalse(bogus_addr)


class IPv4NetObjectTest(unittest.TestCase):
    """
    The input for this test case is a bare IPv4 address string,
    followed by an ipaddress.IPv4Network object.
    """
    def test_get_valid_obj(self):
        """Return IPv4 network object"""
        netobj = netcfg_get_ipnet('172.16.0.241')
        self.assertIsInstance(netobj, ipaddress.IPv4Network)
        self.assertEqual(str(netobj), '172.16.0.240/30')

    def test_get_invalid_obj(self):
        """Raise IPv4 address error"""
        with self.assertRaises(ipaddress.AddressValueError):
            netobj = netcfg_get_ipnet('172.16.0.261')

    def test_get_valid_cfg(self):
        netobj = ipaddress.ip_network('172.16.0.0/30')
        res = ipnet_get_netcfg(netobj)
        self.assertIsInstance(res, AttrDict)
        self.assertEqual(res.host, '172.16.0.2/30')
        # print(res)

    def test_get_invalid_cfg(self):
        """Raise IPv4Network ValueError"""
        with self.assertRaises(ValueError):
            res = ipnet_get_netcfg('172.16.0.0/30')


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


class QueueHandlingTest(unittest.TestCase):
    """
    Test managing node queues.
    """
    def setUp(self):
        super(QueueHandlingTest, self).setUp()
        import diskcache as dc

        self.node_q = dc.Deque(directory='/tmp/test-nq')
        self.reg_q = dc.Deque(directory='/tmp/test-rq')
        self.wait_q = dc.Deque(directory='/tmp/test-wq')
        self.node1 = 'deadbeef01'
        self.node2 = '20beefdead'
        self.node3 = 'beef03dead'

    def tearDown(self):

        self.node_q.clear()
        self.reg_q.clear()
        self.wait_q.clear()
        super(QueueHandlingTest, self).tearDown()

    def test_handle_node_queues(self):
        self.node_q.append(self.node1)
        self.node_q.append(self.node2)

        self.assertEqual(list(self.node_q), [self.node1, self.node2])
        self.assertEqual(list(self.reg_q), [])
        self.assertEqual(list(self.wait_q), [])

        handle_node_queues(self.node_q, self.wait_q)
        self.assertEqual(list(self.node_q), [])
        self.assertEqual(list(self.wait_q), [self.node1, self.node2])

    def test_manage_fpn_nodes(self):
        self.node_q.append(self.node1)
        self.node_q.append(self.node2)

        self.assertEqual(list(self.node_q), [self.node1, self.node2])
        self.assertEqual(list(self.reg_q), [])
        self.assertEqual(list(self.wait_q), [])

        # register node1
        self.reg_q.append(self.node1)

        manage_incoming_nodes(self.node_q, self.reg_q, self.wait_q)
        self.assertEqual(list(self.node_q), [])
        self.assertEqual(list(self.reg_q), [self.node1])
        self.assertEqual(list(self.wait_q), [self.node2])

        # register node2
        self.reg_q.append(self.node2)

        manage_incoming_nodes(self.node_q, self.reg_q, self.wait_q)
        self.assertEqual(list(self.node_q), [])
        self.assertEqual(list(self.reg_q), [self.node1, self.node2])
        self.assertEqual(list(self.wait_q), [])

    def test_manage_other_nodes(self):
        self.assertFalse(check_return_status(self.node_q))
        self.node_q.append(self.node1)
        self.node_q.append(self.node2)

        self.assertEqual(list(self.node_q), [self.node1, self.node2])
        self.assertEqual(list(self.reg_q), [])
        self.assertEqual(list(self.wait_q), [])

        manage_incoming_nodes(self.node_q, self.reg_q, self.wait_q)
        self.assertEqual(list(self.node_q), [])
        self.assertEqual(list(self.reg_q), [])
        self.assertEqual(list(self.wait_q), [self.node1, self.node2])

        # unregistered nodes are still peers
        self.node_q.append(self.node1)
        self.node_q.append(self.node2)

        manage_incoming_nodes(self.node_q, self.reg_q, self.wait_q)
        self.assertEqual(list(self.node_q), [])
        self.assertEqual(list(self.reg_q), [])
        self.assertEqual(list(self.wait_q), [self.node1,
                                             self.node2,
                                             self.node1,
                                             self.node2])

        # node1 still not seen yet, late register from node2
        self.node_q.append(self.node1)
        self.reg_q.append(self.node2)

        manage_incoming_nodes(self.node_q, self.reg_q, self.wait_q)
        self.assertEqual(list(self.node_q), [])
        self.assertEqual(list(self.reg_q), [self.node2])
        self.assertEqual(list(self.wait_q), [self.node1,
                                             self.node1,
                                             self.node1])

        # node2 registered and node1 expired
        manage_incoming_nodes(self.node_q, self.reg_q, self.wait_q)
        self.assertEqual(list(self.node_q), [])
        self.assertEqual(list(self.reg_q), [self.node2])
        self.assertEqual(list(self.wait_q), [])


class QueueMsgHandlingTest(unittest.TestCase):
    """
    Test announce msg handling/node queueing.
    """
    def setUp(self):
        super(QueueMsgHandlingTest, self).setUp()
        import diskcache as dc

        self.node_q = dc.Deque(directory='/tmp/test-nq')
        self.reg_q = dc.Deque(directory='/tmp/test-rq')
        self.wait_q = dc.Deque(directory='/tmp/test-wq')
        self.node1 = 'beef01dead'
        self.node2 = '02beefdead'
        self.node3 = 'deadbeef03'

    def tearDown(self):

        self.node_q.clear()
        self.reg_q.clear()
        self.wait_q.clear()
        super(QueueMsgHandlingTest, self).tearDown()

    def test_handle_msgs(self):
        self.assertEqual(list(self.node_q), [])
        self.node_q.append(self.node1)
        self.node_q.append(self.node2)
        self.node_q.append(self.node3)
        self.wait_q.append(self.node3)

        self.assertEqual(list(self.node_q), [self.node1, self.node2, self.node3])
        self.assertEqual(list(self.reg_q), [])
        self.assertEqual(list(self.wait_q), [self.node3])

        handle_announce_msg(self.node_q, self.reg_q, self.wait_q, self.node1)
        self.assertEqual(list(self.node_q), [self.node1, self.node2, self.node3])
        self.assertEqual(list(self.reg_q), [self.node1])
        self.assertEqual(list(self.wait_q), [self.node3])

        handle_announce_msg(self.node_q, self.reg_q, self.wait_q, self.node2)
        self.assertEqual(list(self.node_q), [self.node1, self.node2, self.node3])
        self.assertEqual(list(self.reg_q), [self.node1, self.node2])
        self.assertEqual(list(self.wait_q), [self.node3])

        handle_announce_msg(self.node_q, self.reg_q, self.wait_q, self.node3)
        self.assertEqual(list(self.node_q), list(self.reg_q))
        self.assertEqual(list(self.wait_q), [self.node3])
        # print(list(self.node_q), list(self.reg_q), list(self.wait_q))


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
        self.state.update(fpn_id='deadbeef00')
        self.role = NODE_SETTINGS['node_role']

    def tearDown(self):
        from node_tools import state_data as st

        st.fpnState = self.saved_state
        NODE_SETTINGS['node_role'] = None
        super(SetRolesTest, self).tearDown()

    def test_ctlr_role(self):
        self.assertIsNone(self.role)

        set_initial_role()
        validate_role()
        self.assertIsNone(NODE_SETTINGS['node_role'])

        NODE_SETTINGS['ctlr_list'].append(self.state['fpn_id'])

        validate_role()

        self.assertEqual(NODE_SETTINGS['node_role'], 'controller')
        self.assertEqual(self.state['fpn_role'], 'controller')
        self.assertEqual(NODE_SETTINGS['node_runner'], 'netstate.py')
        NODE_SETTINGS['ctlr_list'].remove(self.state['fpn_id'])

    def test_moon_role(self):
        self.assertIsNone(self.role)

        set_initial_role()
        validate_role()
        self.assertIsNone(NODE_SETTINGS['node_role'])

        NODE_SETTINGS['moon_list'].append(self.state['fpn_id'])

        validate_role()

        self.assertEqual(NODE_SETTINGS['node_role'], 'moon')
        self.assertEqual(NODE_SETTINGS['node_runner'], 'peerstate.py')
        self.assertEqual(self.state['fpn_role'], 'moon')
        NODE_SETTINGS['moon_list'].remove(self.state['fpn_id'])


class StateChangeTest(unittest.TestCase):
    """
    Note the input for this test case is a pair of node fpnState
    objects (type is dict).
    """
    def setUp(self):
        super(StateChangeTest, self).setUp()
        from node_tools import state_data as st

        self.saved_state = AttrDict.from_nested_dict(st.defState)
        self.state = self.saved_state

    def tearDown(self):
        from node_tools import state_data as st

        st.fpnState = self.saved_state
        super(StateChangeTest, self).tearDown()

    def show_state(self):
        from node_tools import state_data as st

        print('')
        print(self.saved_state)
        print(self.state)

    def test_change_none(self):
        # self.show_state()
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


def test_daemon_subscriber_start(capfd):
    """
    Test if we can (re)start the msg_subscriber daemon.
    """
    NODE_SETTINGS['home_dir'] = os.path.join(os.getcwd(), 'scripts')
    res = run_subscriber_daemon()
    captured = capfd.readouterr()
    assert res == 0
    # print(captured.out)
    assert 'Stopping' in captured.out
    assert 'Starting' in captured.out


def test_daemon_subscriber_stop(capfd):
    """
    Test if we can stop the msg_subscriber daemon.
    """
    NODE_SETTINGS['home_dir'] = os.path.join(os.getcwd(), 'scripts')
    res = run_subscriber_daemon('stop')
    captured = capfd.readouterr()
    assert res == 0
    assert 'Stopping' in captured.out
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


def test_state_trie_load_save():
    # the char set under test is string.hexdigits
    _, fname = create_state_trie()
    trie = load_state_trie(fname)
    trie['f00baf'] = 1
    trie['foobar'] = 2
    trie['baf'] = 3
    trie['fa'] = 4
    trie['Faa'] = 'vasia'
    save_state_trie(trie, fname)
    del trie

    trie2 = load_state_trie(fname)
    assert trie2['f00baf'] == 1
    assert trie2['baf'] == 3
    assert trie2['fa'] == 4
    assert trie2['Faa'] == 'vasia'

    with pytest.raises(KeyError):
        assert trie2['foobar'] == 2


def test_check_net_trie():
    from node_tools import ctlr_data as ct
    res = check_net_trie(ct.net_trie)
    assert res is True


def test_name_generator():
    name = name_generator()
    assert len(name) == 21
    assert name.isprintable()


def test_name_generator_chars():
    name = name_generator(size=15, char_set=string.hexdigits)
    assert len(name) == 31
    str1, str2 = name.split(sep='_', maxsplit=-1)
    assert all(c in string.hexdigits for c in str1)
    assert all(c in string.hexdigits for c in str2)


def test_set_initial_role():
    set_initial_role()


def test_startup_handlers():
    startup_handlers()


def test_invalid_msg():
    res = valid_announce_msg('deadbeeh00')
    assert res is False
    res = valid_announce_msg('deadbeef0')
    assert res is False
    res = valid_announce_msg('deadbeef000')
    assert res is False


def test_valid_msg():
    res = valid_announce_msg('deadbeef00')
    assert res is True


def test_api_warning_msg():
    with pytest.warns(UserWarning):
        warnings.warn("Cannot connect to ZeroTier API", UserWarning)


def test_enodata_warning_msg():
    with pytest.warns(UserWarning):
        warnings.warn("Cache empty and API returned ENODATA", UserWarning)


def test_aging_not_available_warning_msg():
    with pytest.warns(UserWarning):
        warnings.warn("Cache aging not available", UserWarning)


def test_gen_netobj_queue():
    import diskcache as dc

    netobj_q = dc.Deque(directory='/tmp/test-oq')
    netobj_q.clear()

    gen_netobj_queue(netobj_q, ipnet='192.168.0.0/24')
    assert len(netobj_q) == 64
    net = netobj_q.peekleft()
    assert isinstance(net, ipaddress.IPv4Network)
    assert len(list(net)) == 4
    assert len(list(net.hosts())) == 2
    gen_netobj_queue(netobj_q, ipnet='192.168.0.0/24')
    # netobj_q.clear()
