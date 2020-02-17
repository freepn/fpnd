#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Target:   Python 3.6

import time
import ipaddress

import diskcache as dc

from node_tools.helper_funcs import get_cachedir


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
        msg = "{func} took {time} seconds to complete"
        print(msg.format(func=func.__name__,
                         time=runtime))
        return value
    return function_timer


@timerfunc
def gen_netobj_queue(deque, ipnet='172.16.0.0/12'):
    if len(deque) > 0:
        print('Using existing queue: {}'.format(deque.directory))
        print('Timing data no longer valid!')
    else:
        print('Generating netobj queue, please be patient...')
        netobjs = list(ipaddress.ip_network(ipnet).subnets(new_prefix=30))
        for net in netobjs:
            deque.append(net)
    print('{} IPv4 network objects in queue: {}'.format(len(deque), deque.directory))


netobj_q = dc.Deque(directory=get_cachedir('netobj_queue'))

gen_netobj_queue(netobj_q)

test_net = netobj_q.peekleft()

print('Checking first available network')
print('Network with netmask: {}'.format(test_net))
print('Network has host list: {}'.format(list(test_net.hosts())))
iface = ipaddress.ip_interface(str(list(test_net.hosts())[0]))
print('First host has interface: {}'.format(iface))
