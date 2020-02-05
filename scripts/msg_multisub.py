#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Target:   Python 3.6

import os
import sys
import time
import syslog
import datetime

from multiprocessing import Process

import diskcache as dc
from daemon import Daemon
from nanoservice import Subscriber

from node_tools.helper_funcs import get_cachedir
from node_tools.msg_queues import valid_announce_msg


pid_file = '/tmp/subscriber.pid'
stdout = '/tmp/subscriber.log'
stderr = '/tmp/subscriber_err.log'

node_q = dc.Deque(directory=get_cachedir('node_queue'))


def print_stats(n, duration):
    pairs = [
        ('Total messages', n),
        ('Total duration (s)', duration),
        ('Throughput (msg/s)', n/duration)
    ]
    for pair in pairs:
        label, value = pair
        print(' * {:<25}: {:10,.2f}'.format(label, value))


def service_runner(addr, n):
    """ Run subscriber service and fill node queue (with stats)"""

    s = Subscriber(addr)

    def handle_msg(msg):
        pass

    s.subscribe('handle_node', handle_msg)

    started = time.time()
    for _ in range(n):
        s.process()
    duration = time.time() - started

    print('Subscriber service stats:')
    print_stats(n, duration)
    return


# Inherit from Daemon class
class subDaemon(Daemon):
    # implement run method
    def run(self):

        self.sock_addr = 'ipc:///tmp/service.sock'
        self.tcp_addr = 'tcp://0.0.0.0:9442'
        self.n = 10

        # Fork service
        service_process = Process(target=service_runner,
                                  args=(self.tcp_addr, self.n))
        service_process.start()
        while True:
            time.sleep(1)
        service_process.terminate()


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
