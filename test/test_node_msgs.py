# -*- coding: utf-8 -*-
import unittest

from nanoservice import Subscriber
from nanoservice import Publisher

from node_tools.network_funcs import drain_reg_queue
from node_tools.node_funcs import control_daemon


class BaseTestCase(unittest.TestCase):

    def setUp(self):
        import diskcache as dc

        self.node1 = 'deadbeef01'
        self.node2 = '20beefdead'
        self.node_q = dc.Deque(directory='/tmp/test-nq')

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
        self.service.socket.close()


class TestPubSub(BaseTestCase):

    def test_node_pub(self):
        self.node_q.append(self.node1)
        self.node_q.append(self.node2)

        # Client side
        drain_reg_queue(self.node_q)

        # server side
        res = self.service.process()
        res = self.service.process()
        self.assertEqual(list(self.node_q), [])
        self.assertEqual(res, [self.node1, self.node2])

    def test_node_pub_addr(self):
        self.node_q.append(self.node1)
        self.node_q.append(self.node2)

        # Client side
        drain_reg_queue(self.node_q, addr=self.addr)

        # server side
        res = self.service.process()
        res = self.service.process()
        self.assertEqual(list(self.node_q), [])
        self.assertEqual(res, [self.node1, self.node2])
