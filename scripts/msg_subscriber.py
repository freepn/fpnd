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
from nanoservice import Subscriber

from node_tools.helper_funcs import get_cachedir
from node_tools.msg_queues import add_one_only
from node_tools.msg_queues import valid_announce_msg
from node_tools.msg_queues import valid_cfg_msg


log = logging.getLogger(__name__)

# set log level and handler/formatter
log.setLevel(logging.DEBUG)

handler = logging.handlers.SysLogHandler(address='/dev/log', facility='daemon')
formatter = logging.Formatter('%(module)s.%(funcName)s +%(lineno)s: %(message)s')
handler.setFormatter(formatter)
log.addHandler(handler)

pid_file = '/tmp/subscriber.pid'
std_out = '/tmp/subscriber.log'
std_err = '/tmp/subscriber_err.log'

cfg_q = dc.Deque(directory=get_cachedir('cfg_queue'))
node_q = dc.Deque(directory=get_cachedir('node_queue'))
off_q = dc.Deque(directory=get_cachedir('off_queue'))
pub_q = dc.Deque(directory=get_cachedir('pub_queue'))


def handle_msg(msg):
    if valid_announce_msg(msg):
        log.debug('Got valid node ID: {}'.format(msg))
        with node_q.transact():
            node_q.append(msg)
        log.debug('Adding node id: {}'.format(msg))
        log.info('{} nodes in node queue'.format(len(node_q)))

    else:
        log.warning('Bad node msg is {}'.format(msg))


def handle_cfg(msg):
    import json

    if valid_cfg_msg(msg):
        log.debug('Got valid cfg msg: {}'.format(msg))
        cfg_msg = json.loads(msg)
        if cfg_msg['node_id'] in pub_q:
            with cfg_q.transact():
                add_one_only(msg, cfg_q)
            log.debug('Adding node cfg: {}'.format(msg))
        log.info('{} cfgs in active queue'.format(len(cfg_q)))

    else:
        log.warning('Bad cfg msg is {}'.format(msg))


def offline(msg):
    """
    Process offline node msg (validate and add to offline_q).
    """
    if valid_announce_msg(msg):
        log.debug('Got valid offline msg: {}'.format(msg))
        with off_q.transact():
            add_one_only(msg, off_q)
        log.debug('Adding node id: {}'.format(msg))
        log.info('{} nodes in offline queue'.format(len(off_q)))
    else:
        log.warning('Bad offline msg is {}'.format(msg))


# Inherit from Daemon class
class subDaemon(Daemon):
    # implement run method
    def run(self):

        self.sock_addr = 'ipc:///tmp/service.sock'
        self.tcp_addr = 'tcp://0.0.0.0:9442'

        s = Subscriber(self.tcp_addr)
        s.subscribe('handle_node', handle_msg)
        s.subscribe('cfg_msgs', handle_cfg)
        s.subscribe('offline', offline)
        s.start()


if __name__ == "__main__":

    daemon = subDaemon(pid_file, stdout=std_out, stderr=std_err, verbose=1)
    if len(sys.argv) == 2:
        if 'start' == sys.argv[1]:
            log.info('Starting')
            daemon.start()
        elif 'stop' == sys.argv[1]:
            log.info('Stopping')
            daemon.stop()
        elif 'restart' == sys.argv[1]:
            log.info('Restarting')
            daemon.restart()
        elif 'status' == sys.argv[1]:
            res = daemon.status()
            log.info('Status is {}'.format(res))
        else:
            print("Unknown command")
            sys.exit(2)
        sys.exit(0)
    else:
        print("usage: {} start|stop|restart|status".format(sys.argv[0]))
        sys.exit(2)
