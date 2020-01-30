#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Target:   Python 3.6

import os
import sys
import time
import syslog
import datetime

from daemon import Daemon
from nanoservice import Responder


pid_file = '/tmp/responder.pid'
stdout = '/tmp/responder.log'
stderr = '/tmp/responder_err.log'


def echo(msg):
    print("Echoing message: {}".format(msg))
    return msg


# Inherit from Daemon class
class rspDaemon(Daemon):
    # implement run method
    def run(self):

        self.sock_addr = 'ipc:///tmp/service.sock'
        self.tcp_addr = 'tcp://0.0.0.0:9443'

        s = Responder(self.tcp_addr, timeouts=(None, None))
        s.register('echo', echo)
        s.start()


if __name__ == "__main__":

    daemon = rspDaemon(pid_file, stdout=stdout, stderr=stderr, verbose=1)
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
