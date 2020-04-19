#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Target:   Python 3.6

import os
import sys
import time
import syslog
import datetime

import diskcache as dc
from daemon import Daemon
from nanoservice import Subscriber

from node_tools.helper_funcs import get_cachedir
from node_tools.msg_queues import valid_announce_msg
from node_tools.msg_queues import valid_cfg_msg


pid_file = '/tmp/subscriber.pid'
std_out = '/tmp/subscriber.log'
std_err = '/tmp/subscriber_err.log'

active_q = dc.Deque(directory=get_cachedir('act_queue'))
node_q = dc.Deque(directory=get_cachedir('node_queue'))
pub_q = dc.Deque(directory=get_cachedir('pub_queue'))


def handle_msg(msg):
    if valid_announce_msg(msg):
        print('SUB: Valid node ID: {}'.format(msg))
        if msg not in node_q:
            with node_q.transact():
                node_q.append(msg)
            syslog.syslog(syslog.LOG_DEBUG,
                          'SUB: Adding node id: {}'.format(msg))
        syslog.syslog(syslog.LOG_INFO,
                      'SUB: {} nodes in node queue'.format(len(node_q)))

    else:
        syslog.syslog(syslog.LOG_DEBUG, 'SUB: Bad node msg is {}'.format(msg))


def handle_cfg(msg):
    import json

    if valid_cfg_msg(msg):
        print('SUB: Valid cfg msg: {}'.format(msg))
        cfg_msg = json.loads(msg)
        if cfg_msg['node_id'] in pub_q:
            with active_q.transact():
                if active_q.count(msg) < 1:
                    active_q.append(msg)
                    syslog.syslog(syslog.LOG_DEBUG,
                                  'SUB: Adding node cfg: {}'.format(msg))
        syslog.syslog(syslog.LOG_INFO,
                      'SUB: {} cfgs in active queue'.format(len(active_q)))

    else:
        syslog.syslog(syslog.LOG_DEBUG, 'SUB: Bad cfg msg is {}'.format(msg))


# Inherit from Daemon class
class subDaemon(Daemon):
    # implement run method
    def run(self):

        self.sock_addr = 'ipc:///tmp/service.sock'
        self.tcp_addr = 'tcp://0.0.0.0:9442'

        s = Subscriber(self.tcp_addr)
        s.subscribe('handle_node', handle_msg)
        s.subscribe('cfg_msgs', handle_cfg)
        s.start()


if __name__ == "__main__":

    daemon = subDaemon(pid_file, stdout=std_out, stderr=std_err, verbose=1)
    if len(sys.argv) == 2:
        if 'start' == sys.argv[1]:
            syslog.syslog(syslog.LOG_INFO, "SUB: Starting")
            daemon.start()
        elif 'stop' == sys.argv[1]:
            syslog.syslog(syslog.LOG_INFO, "SUB: Stopping")
            daemon.stop()
        elif 'restart' == sys.argv[1]:
            syslog.syslog(syslog.LOG_INFO, "SUB: Restarting")
            daemon.restart()
        elif 'status' == sys.argv[1]:
            res = daemon.status()
            syslog.syslog(syslog.LOG_INFO, "SUB: Status is {}".format(res))
        else:
            print("Unknown command")
            sys.exit(2)
        sys.exit(0)
    else:
        print("usage: {} start|stop|restart|status".format(sys.argv[0]))
        sys.exit(2)
