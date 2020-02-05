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


pid_file = '/tmp/subscriber.pid'
stdout = '/tmp/subscriber.log'
stderr = '/tmp/subscriber_err.log'

node_q = dc.Deque(directory=get_cachedir('node_queue'))


# Inherit from Daemon class
class subDaemon(Daemon):
    # implement run method
    def run(self):

        self.sock_addr = 'ipc:///tmp/service.sock'
        self.tcp_addr = 'tcp://0.0.0.0:9442'

        def handle_msg(msg):
            if valid_announce_msg(msg):
                print('Node ID is: {}'.format(msg))
                if msg not in node_q:
                    node_q.append(msg)
                    syslog.syslog(syslog.LOG_INFO,
                                  'Adding node id: {}'.format(msg))
                syslog.syslog(syslog.LOG_INFO,
                              '{} nodes in node queue'.format(len(node_q)))

            else:
                syslog.syslog(syslog.LOG_ERROR, "Bad msg recieved!")

        s = Subscriber(self.tcp_addr)
        s.subscribe('handle_node', handle_msg)
        s.start()


if __name__ == "__main__":

    daemon = subDaemon(pid_file, stdout=stdout, stderr=stderr, verbose=1)
    if len(sys.argv) == 2:
        if 'start' == sys.argv[1]:
            syslog.syslog(syslog.LOG_INFO, "Starting")
            daemon.start()
        elif 'stop' == sys.argv[1]:
            syslog.syslog(syslog.LOG_INFO, "Stopping")
            daemon.stop()
        elif 'restart' == sys.argv[1]:
            syslog.syslog(syslog.LOG_INFO, "Restarting")
            daemon.restart()
        else:
            print("Unknown command")
            sys.exit(2)
        sys.exit(0)
    else:
        print("usage: {} start|stop|restart".format(sys.argv[0]))
        sys.exit(2)
