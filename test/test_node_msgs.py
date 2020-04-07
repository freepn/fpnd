# -*- coding: utf-8 -*-
import unittest

from nanoservice import Subscriber
from nanoservice import Publisher

from node_tools.ctlr_funcs import trie_is_empty
from node_tools.network_funcs import drain_reg_queue
from node_tools.msg_queues import handle_announce_msg
from node_tools.msg_queues import handle_node_queues
from node_tools.msg_queues import make_cfg_msg
from node_tools.msg_queues import manage_incoming_nodes
from node_tools.msg_queues import valid_announce_msg
from node_tools.msg_queues import valid_cfg_msg
from node_tools.msg_queues import wait_for_cfg_msg
from node_tools.sched_funcs import check_return_status


def test_invalid_msg():
    for msg in ['deadbeeh00', 'deadbeef0', 'deadbeef000']:
        res = valid_announce_msg(msg)
        assert res is False


def test_valid_msg():
    res = valid_announce_msg('deadbeef00')
    assert res is True


def test_invalid_cfg_msg():
    msg_list = [
                '{"node": "deadbeef00"}',
                '{"node_id": "02beefdead"}',
                '{"node_id": "02beefhead", "net0_id": "7ac4235ec5d3d938"}'
               ]
    for msg in msg_list:
        res = valid_cfg_msg(msg)
        assert res is False


def test_valid_cfg_msg():
    res = valid_cfg_msg('{"node_id": "02beefdead", "net0_id": "7ac4235ec5d3d938"}')
    assert res is True


def test_make_cfg_msg():
    from node_tools import ctlr_data as ct
    assert trie_is_empty(ct.id_trie) is True

    node_id = '02beefdead'
    net_list = ['7ac4235ec5d3d938']
    ct.id_trie[node_id] = net_list
    cfg_msg = '{"node_id": "02beefdead", "networks": ["7ac4235ec5d3d938"]}'

    res = make_cfg_msg(ct.id_trie, node_id)
    assert type(res) is str
    assert res == cfg_msg


class BaseTestCase(unittest.TestCase):

    def setUp(self):
        import diskcache as dc

        self.node1 = 'deadbeef01'
        self.node2 = '20beefdead'
        self.node_q = dc.Deque(directory='/tmp/test-nq')
        self.pub_q = dc.Deque(directory='/tmp/test-pq')
        self.node_q.clear()
        self.pub_q.clear()

        self.addr = '127.0.0.1'
        self.tcp_addr = 'tcp://{}:9442'.format(self.addr)
        self.sub_list = []

        def handle_msg(msg):
            self.sub_list.append(msg)
            return self.sub_list

        self.service = Subscriber(self.tcp_addr)
        self.service.subscribe('handle_node', handle_msg)

    def tearDown(self):
        self.node_q.clear()
        self.pub_q.clear()
        self.service.socket.close()


class TestPubSub(BaseTestCase):

    def test_node_pub(self):
        self.node_q.append(self.node1)
        self.node_q.append(self.node2)

        # Client side
        drain_reg_queue(self.node_q, self.pub_q)

        # server side
        res = self.service.process()
        res = self.service.process()
        self.assertEqual(list(self.node_q), [])
        self.assertEqual(list(self.pub_q), ['deadbeef01', '20beefdead'])
        self.assertEqual(res, [self.node1, self.node2])

    def test_node_pub_addr(self):
        self.node_q.append(self.node1)
        self.node_q.append(self.node2)

        # Client side
        drain_reg_queue(self.node_q, self.pub_q, self.addr)

        # server side
        res = self.service.process()
        res = self.service.process()
        self.assertEqual(list(self.node_q), [])
        self.assertEqual(list(self.pub_q), ['deadbeef01', '20beefdead'])
        self.assertEqual(res, [self.node1, self.node2])


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


class WaitForMsgHandlingTest(unittest.TestCase):
    """
    Test net_id cfg msg handling/node queueing.
    """
    def setUp(self):
        super(WaitForMsgHandlingTest, self).setUp()
        import diskcache as dc

        self.pub_q = dc.Deque(directory='/tmp/test-pq')
        self.active_q = dc.Deque(directory='/tmp/test-aq')
        self.node1 = 'beef01dead'
        self.node2 = '02beefdead'
        self.node3 = 'deadbeef03'
        self.cfg1 = '{"node_id": "beef01dead", "net0_id": "bb8dead3c63cea29", "net1_id": "7ac4235ec5d3d938"}'
        self.cfg2 = '{"node_id": "02beefdead", "net0_id": "7ac4235ec5d3d938"}'

        self.pub_q.append(self.node1)
        self.pub_q.append(self.node2)
        self.active_q.append(self.cfg1)
        self.active_q.append(self.cfg2)

    def tearDown(self):

        self.pub_q.clear()
        self.active_q.clear()
        super(WaitForMsgHandlingTest, self).tearDown()

    def test_wait_for_cfg(self):
        import json
        res = wait_for_cfg_msg(self.pub_q, self.active_q, self.node1)
        self.assertIsInstance(res, dict)
        self.assertEqual(res['node_id'], self.node1)
        self.assertEqual(res['net0_id'], 'bb8dead3c63cea29')
        # print(len(json.loads(self.cfg1)))
        # print(len(json.loads(self.cfg2)))

    def test_wait_for_cfg_none(self):
        res = wait_for_cfg_msg(self.pub_q, self.active_q, self.node3)
        self.assertIsNone(res)
        self.pub_q.remove(self.node2)
        res = wait_for_cfg_msg(self.pub_q, self.active_q, self.node2)
        self.assertEqual(res['node_id'], self.node2)
