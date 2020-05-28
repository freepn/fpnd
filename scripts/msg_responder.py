#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Target:   Python 3.6

import os
import sys
import time
import datetime
import logging
import logging.handlers

import diskcache as dc
from daemon import Daemon
from nanoservice import Responder

from nanoservice.error import ServiceError

from node_tools import state_data as st

from node_tools.helper_funcs import get_cachedir
from node_tools.msg_queues import add_one_only
from node_tools.msg_queues import clean_from_queue
from node_tools.msg_queues import handle_announce_msg
from node_tools.msg_queues import lookup_node_id
from node_tools.msg_queues import valid_announce_msg
from node_tools.msg_queues import wait_for_cfg_msg


logger = logging.getLogger(__name__)

# set log level and handler/formatter
logger.setLevel(logging.DEBUG)
logging.getLogger('node_tools.msg_queues').level = logging.DEBUG

handler = logging.handlers.SysLogHandler(address='/dev/log', facility='daemon')
formatter = logging.Formatter('%(module)s: %(funcName)s+%(lineno)s: %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

pid_file = '/tmp/responder.pid'
stdout = '/tmp/responder.log'
stderr = '/tmp/responder_err.log'

cfg_q = dc.Deque(directory=get_cachedir('cfg_queue'))
hold_q = dc.Deque(directory=get_cachedir('hold_queue'))
off_q = dc.Deque(directory=get_cachedir('off_queue'))
pub_q = dc.Deque(directory=get_cachedir('pub_queue'))
wdg_q = dc.Deque(directory=get_cachedir('wedge_queue'))

node_q = dc.Deque(directory=get_cachedir('node_queue'))
reg_q = dc.Deque(directory=get_cachedir('reg_queue'))
wait_q = dc.Deque(directory=get_cachedir('wait_queue'))

tmp_q = dc.Deque(directory=get_cachedir('tmp_queue'))


def clean_stale_cfgs(key_str, deque):
    """
    Clean any stale cfg msgs from the cfg deque.
    """
    if len(deque) != 0:
        for item in list(deque):
            if key_str in item:
                clean_from_queue(item, deque)


def timerfunc(func):
    """
    A timer decorator
    """
    def function_timer(*args, **kwargs):
        """
        A nested function for timing other functions
        """
        start = time.process_time()
        value = func(*args, **kwargs)
        end = time.process_time()
        runtime = end - start
        msg = "{func} took {time} seconds to process msg"
        print(msg.format(func=func.__name__,
                         time=runtime))
        return value
    return function_timer


def echo(msg):
    """
    Process valid node msg/queues, ie, msg must be a valid node ID.
    :param str node ID: zerotier node identity
    :return: str node ID
    """
    if valid_announce_msg(msg):
        logger.debug('Got valid announce msg: {}'.format(msg))
        clean_stale_cfgs(msg, cfg_q)
        handle_announce_msg(node_q, reg_q, wait_q, msg)
        node_data = lookup_node_id(msg, tmp_q)
        if node_data:
            logger.info('Handled announce msg from host {}'.format(node_data[msg]))
        return msg
    else:
        node_data = lookup_node_id(msg, tmp_q)
        if node_data:
            logger.info('Bad announce msg from host {}'.format(node_data[msg]))
        else:
            logger.warning('Bad announce msg: {}'.format(msg))


def get_node_cfg(msg):
    """
    Process valid cfg msg, ie, msg must be a valid node ID.
    :param str node ID: zerotier node identity
    :return: str JSON object with node ID and network ID(s)
    """
    import json

    if valid_announce_msg(msg):
        node_data = lookup_node_id(msg, tmp_q)
        if node_data:
            logger.info('Got valid cfg request msg from host {}'.format(node_data[msg]))
        res = wait_for_cfg_msg(cfg_q, hold_q, reg_q, msg)
        logger.debug('hold_q contents: {}'.format(list(hold_q)))
        if res:
            logger.debug('Got cfg result: {}'.format(res))
            return res
        else:
            logger.debug('Null result for ID: {}'.format(msg))
            # raise ServiceError
    else:
        node_data = lookup_node_id(msg, tmp_q)
        if node_data:
            logger.info('Bad cfg msg from host {}'.format(node_data[msg]))
        else:
            logger.warning('Bad cfg msg: {}'.format(msg))


def offline(msg):
    """
    Process offline node msg (validate and add to offline_q).
    :param str node ID: zerotier node identity
    :return: str node ID
    """
    if valid_announce_msg(msg):
        clean_stale_cfgs(msg, cfg_q)
        node_data = lookup_node_id(msg, tmp_q)
        if node_data:
            logger.info('Got valid offline msg from host {}'.format(node_data[msg]))
        with off_q.transact():
            add_one_only(msg, off_q)
        with pub_q.transact():
            clean_from_queue(msg, pub_q)
        logger.debug('Node ID {} cleaned from pub_q'.format(msg))
        return msg
    else:
        node_data = lookup_node_id(msg, tmp_q)
        if node_data:
            logger.info('Bad offline msg from host {}'.format(node_data[msg]))
        else:
            logger.warning('Bad offline msg: {}'.format(msg))


def wedged(msg):
    """
    Process wedged node msg (validate and add to wedge_q). Note these
    are currently disabled for testing.
    :param str node ID: zerotier node identity
    :return: str node ID
    """
    if valid_announce_msg(msg):
        node_data = lookup_node_id(msg, tmp_q)
        if node_data:
            logger.info('Got valid wedged msg from host {}'.format(node_data[msg]))
        with wdg_q.transact():
            # re-enable msg processing for testing
            add_one_only(msg, wdg_q)
        return msg
    else:
        node_data = lookup_node_id(msg, tmp_q)
        if node_data:
            logger.info('Bad wedged msg from host {}'.format(node_data[msg]))
        else:
            logger.warning('Bad wedged msg: {}'.format(msg))


# Inherit from Daemon class
class rspDaemon(Daemon):
    # implement run method
    def run(self):

        self.sock_addr = 'ipc:///tmp/service.sock'
        self.tcp_addr = 'tcp://0.0.0.0:9443'

        s = Responder(self.tcp_addr, timeouts=(None, None))
        s.register('echo', echo)
        s.register('node_cfg', get_node_cfg)
        s.register('offline', offline)
        s.register('wedged', wedged)
        s.start()


if __name__ == "__main__":

    daemon = rspDaemon(pid_file, stdout=stdout, stderr=stderr, verbose=1)
    if len(sys.argv) == 2:
        if 'start' == sys.argv[1]:
            logger.info('Starting')
            daemon.start()
        elif 'stop' == sys.argv[1]:
            logger.info('Stopping')
            daemon.stop()
        elif 'restart' == sys.argv[1]:
            logger.info('Restarting')
            daemon.restart()
        elif 'status' == sys.argv[1]:
            res = daemon.status()
            logger.info('Status is {}'.format(res))
        else:
            print("Unknown command")
            sys.exit(2)
        sys.exit(0)
    else:
        print("usage: {} start|stop|restart|status".format(sys.argv[0]))
        sys.exit(2)
