# coding: utf-8

"""ctlr-specific helper functions."""

import logging

from node_tools.helper_funcs import AttrDict
from node_tools.helper_funcs import NODE_SETTINGS
from node_tools.helper_funcs import find_ipv4_iface
from node_tools.helper_funcs import json_load_file


logger = logging.getLogger(__name__)


def gen_netobj_queue(deque, ipnet='172.16.0.0/12'):
    import ipaddress

    if len(deque) > 0:
        logger.debug('Using existing queue: {}'.format(deque.directory))
    else:
        logger.debug('Generating netobj queue, please be patient...')
        netobjs = list(ipaddress.ip_network(ipnet).subnets(new_prefix=30))
        for net in netobjs:
            deque.append(net)
    logger.debug('{} IPNetwork objects in queue: {}'.format(len(deque), deque.directory))


def get_exit_node_id():
    """
    Get the exit node ID (if not empty, return the first ID in the list).
    :return str: Id of the exit node
    """
    result = None
    if len(NODE_SETTINGS['use_exitnode']) > 0:
        result = NODE_SETTINGS['use_exitnode'][0]
    return result


def get_network_id(data):
    """
    Get the network ID from the dict-ish client payload (ie, the content
    of client.data) passed to/from `add_network_object`.
    :param data: <dict> network attributres
    :return: <str> network ID
    """

    net_data = AttrDict.from_nested_dict(data)
    return net_data.id


def handle_net_cfg(deque):
    """
    Handle the initial net_cfg for a (new) member node. Required format
    derived from async wrapper funcs.  Context is netstate runner and
    bootstrap_mbr_node.
    :param deque: netobj queue
    :return: tuple of formatted cfg fragments
    """

    ipnet = deque.popleft()
    netcfg = ipnet_get_netcfg(ipnet)
    gw_ip = find_ipv4_iface(netcfg.gateway[0])
    src_ip = find_ipv4_iface(netcfg.host[0])

    ip_range = [{'ipRangeStart': '{}'.format(gw_ip),
                 'ipRangeEnd': '{}'.format(src_ip)}]

    src_addr = {
        'ipAssignments': netcfg.host,
        'authorized': True
    }

    gw_addr = {
        'ipAssignments': netcfg.gateway,
        'authorized': True
    }

    net_defs = {
        'routes': netcfg.net_routes,
        'ipAssignmentPools': ip_range
    }

    mbr_ip = AttrDict.from_nested_dict(src_addr)
    gw_ip = AttrDict.from_nested_dict(gw_addr)
    ip_net = AttrDict.from_nested_dict(net_defs)

    return ip_net, mbr_ip, gw_ip


def ipnet_get_netcfg(netobj):
    """
    Process a (python) network object into config Attrdict.
    :notes: Each item in the route list must be processed as a separate
            config fragment.
    :param netobj: python subnet object from the netobj queue
    :return: `dict` Attrdict of JSON config fragments
    """
    import ipaddress as ip

    if isinstance(netobj, ip.IPv4Network):
        net_cidr = str(netobj)
        net_pfx = '/' + str(netobj.prefixlen)
        gate_iface = ip.IPv4Interface(str(list(netobj.hosts())[0]) + net_pfx)
        host_iface = ip.IPv4Interface(str(list(netobj.hosts())[1]) + net_pfx)
        gate_addr = str(gate_iface.ip)
        host_cidr = [str(host_iface)]
        gate_cidr = [str(gate_iface)]

        net_routes = [{"target": "{}".format(net_cidr)},
                      {"target": "0.0.0.0/0", "via": "{}".format(gate_addr)}]

        d = {
            "net_routes": net_routes,
            "host": host_cidr,
            "gateway": gate_cidr
        }
        return AttrDict.from_nested_dict(d)
    else:
        raise ValueError('{} is not a valid IPv4Network object'.format(netobj))


def is_exit_node(node_id):
    """
    Check if node_id is an exit node.
    :param node_id: mbr node ID string
    :return bool: True if node is an exit node
    """
    if node_id in NODE_SETTINGS['use_exitnode']:
        return True
    return False


def name_generator(size=10, char_set=None):
    """
    Generate a random network name for ZT add_network_object. The
    name returned is two substrings of <size> concatenated together
    with an underscore. Default character set is lowercase ascii plus
    digits, default size is 10.
    :param size: size of each substring in chars
    :param char_set: character set used for sub strings
    :return: `str` network name
    """
    import random

    if not char_set:
        import string
        chars = string.ascii_lowercase + string.digits
    else:
        chars = char_set

    str1 = ''.join(random.choice(chars) for _ in range(size))
    str2 = ''.join(random.choice(chars) for _ in range(size))
    return str1 + '_' + str2


def netcfg_get_ipnet(addr, cidr='/30'):
    """
    Process member host or gateway addr string into the (python)
    network object it belongs to.  We also assume/require the CIDR
    prefix for `addr` == /30 to be compatible with gen_netobj_queue().
    :param addr: IPv4 address string without mask
    :param cidr: network prefix
    :return: <netobj> network object for host_addr
    :raises: AddressValueError
    """
    import ipaddress as ip
    from node_tools.helper_funcs import find_ipv4_iface

    if find_ipv4_iface(addr + cidr, strip=False):
        netobj = ip.ip_network(addr + cidr, strict=False)
        return netobj
    else:
        raise ip.AddressValueError


def set_network_cfg(cfg_addr):
    """
    Take the netcfg for mbr and wrap it so it can be applied during mbr
    bootstrap (ie, wrap the address with authorized=True, etc).
    :param cfg_addr: <list> gw or host portion of netcfg object
    :return: <dict> formatted cfg fragment for async payload
    """

    src_addr = {
        'ipAssignments': cfg_addr,
        'authorized': True
    }

    return AttrDict.from_nested_dict(src_addr)


def unset_network_cfg():
    """
    Create a config fragment to unset (remove) the IP address and
    deauthorize the node.
    :return: <dict> formatted cfg fragment for async payload
    """

    src_addr = {
        'ipAssignments': [],
        'authorized': False
    }

    return AttrDict.from_nested_dict(src_addr)
