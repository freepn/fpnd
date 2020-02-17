# coding: utf-8

"""ctlr-specific helper functions."""
import logging
import ipaddress


logger = logging.getLogger(__name__)


def gen_netobj_queue(deque, ipnet='172.16.0.0/12'):
    if len(deque) > 0:
        logger.debug('Using existing queue: {}'.format(deque.directory))
    else:
        logger.debug('Generating netobj queue, please be patient...')
        netobjs = list(ipaddress.ip_network(ipnet).subnets(new_prefix=30))
        for net in netobjs:
            deque.append(net)
    logger.debug('{} IPv4 network objects in queue: {}'.format(len(deque), deque.directory))
