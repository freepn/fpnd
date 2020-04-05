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
from nanoservice import Responder

from nanoservice.error import ServiceError

from node_tools import state_data as st

from node_tools.helper_funcs import get_cachedir
from node_tools.msg_queues import handle_announce_msg
from node_tools.msg_queues import valid_announce_msg
from node_tools.msg_queues import wait_for_cfg_msg


pid_file = '/tmp/responder.pid'
stdout = '/tmp/responder.log'
stderr = '/tmp/responder_err.log'

active_q = dc.Deque(directory=get_cachedir('act_queue'))
pub_q = dc.Deque(directory=get_cachedir('pub_queue'))

node_q = dc.Deque(directory=get_cachedir('node_queue'))
reg_q = dc.Deque(directory=get_cachedir('reg_queue'))
wait_q = dc.Deque(directory=get_cachedir('wait_queue'))


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


@timerfunc
def echo(msg):
    """
    Process valid node msg/queues, ie, msg must be a valid node ID.
    :param str node ID: zerotier node identity
    :return: str node ID
    """
    if valid_announce_msg(msg):
        syslog.syslog(syslog.LOG_INFO, "Got valid announce msg: {}".format(msg))
        handle_announce_msg(node_q, reg_q, wait_q, msg)
        return msg
    else:
        syslog.syslog(syslog.LOG_ERROR, "Bad announce msg: {}".format(msg))


@timerfunc
def get_node_cfg(msg):
    """
    Process valid cfg msg, ie, msg must be a valid node ID.
    :param str node ID: zerotier node identity
    :return: str JSON object with node ID and network ID(s)
    """
    import json

    if valid_announce_msg(msg):
        syslog.syslog(syslog.LOG_INFO, "Got valid net_id request: {}".format(msg))
        result = wait_for_cfg_msg(pub_q, active_q, msg)
        if result:
            syslog.syslog(syslog.LOG_INFO, "Got net_id result: {}".format(result))
            return json.dumps(result)
        else:
            syslog.syslog(syslog.LOG_INFO, "No result for ID: {}".format(msg))
            raise ServiceError
    else:
        syslog.syslog(syslog.LOG_ERROR, "Bad net_id msg: {}".format(msg))


# Inherit from Daemon class
class rspDaemon(Daemon):
    # implement run method
    def run(self):

        self.sock_addr = 'ipc:///tmp/service.sock'
        self.tcp_addr = 'tcp://0.0.0.0:9443'

        s = Responder(self.tcp_addr, timeouts=(None, None))
        s.register('echo', echo)
        s.register('node_cfg', get_node_cfg)
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
        elif 'status' == sys.argv[1]:
            res = daemon.status()
            syslog.syslog(syslog.LOG_INFO, "Status is {}".format(res))
        else:
            print("Unknown command")
            sys.exit(2)
        sys.exit(0)
    else:
        print("usage: {} start|stop|restart|status".format(sys.argv[0]))
        sys.exit(2)
