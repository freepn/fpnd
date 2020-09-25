# coding: utf-8

"""Network helper functions."""
from __future__ import print_function

import logging

from node_tools import state_data as st

from node_tools.helper_funcs import NODE_SETTINGS
from node_tools.helper_funcs import put_state_msg
from node_tools.sched_funcs import catch_exceptions
from node_tools.sched_funcs import run_until_success


logger = logging.getLogger(__name__)


def do_host_check(path=None):
    """
    Try and ping a google DNS server over the (default) host route.
    :param path: path to script dir
    """
    import os

    if not path:
        path = NODE_SETTINGS['home_dir']
    cmd = os.path.join(path, 'ping_google.sh')

    result = do_net_cmd([cmd])
    return result


def do_net_check(path=None):
    """
    Try and get the geoip location using fpn route.
    :param path: path to script dir
    """
    import os

    if not path:
        path = NODE_SETTINGS['home_dir']

    cmd_file = os.path.join(path, 'show-geoip.sh')
    cmd = [cmd_file]
    doh_host = NODE_SETTINGS['doh_host']
    max_wait = NODE_SETTINGS['max_timeout']

    if doh_host is not None:
        cmd = [cmd_file, doh_host]
        logger.debug('ENV: geoip script using doh_host: {}'.format(doh_host))

    result = do_net_cmd(cmd)
    state, res, retcode = result
    fpn_data = st.fpnState
    net_wait = st.wait_cache

    if not state:
        host_state, _, _ = do_host_check()
        if fpn_data['fpn0'] and fpn_data['fpn1'] and retcode == 4:
            if fpn_data['route'] is True:
                fpn_data['route'] = None
                net_wait.set('failed_once', True, max_wait)
            else:
                if host_state:
                    fpn_data['route'] = False
                elif not net_wait.get('failed_once') and not fpn_data['route']:
                    fpn_data['route'] = False
            logger.error('HEALTH: network route state is {}'.format(fpn_data['route']))
            logger.error('HEALTH: host route state is {}'.format(host_state))
            logger.debug('HEALTH: net_wait is {}'.format(net_wait.get('failed_once')))
        else:
            logger.error('do_net_check {} returned: {}'.format(cmd, result))
    else:
        if fpn_data['fpn0'] and fpn_data['fpn1']:
            if retcode == 0:
                fpn_data['route'] = True
                fpn_data['wdg_ref'] = None
                put_state_msg('CONNECTED')
            logger.info('HEALTH: network route state is {}'.format(fpn_data['route']))
        elif fpn_data['route'] is None:
            logger.info('HEALTH: no state yet (state is {})'.format(fpn_data['route']))

    return result


def do_peer_check(ztaddr):
    """
    Try and ping the gateway/peer and goose the network if down.
    :param addr: target addr
    """
    import os
    from node_tools.ctlr_funcs import netcfg_get_ipnet

    addr = ztaddr

    try:
        netobj = netcfg_get_ipnet(ztaddr)
    except ValueError as exc:
        logger.error('netobj error is {}'.format(exc))
        raise exc

    for host in list(netobj.hosts()):
        if str(host) != ztaddr:
            addr = str(host)
            break
            logger.debug('PEER: found target IP addr {}'.format(addr))

    home = NODE_SETTINGS['home_dir']
    cmd_file = os.path.join(home, 'ping_gateway.sh')
    cmd = [cmd_file, addr]

    result = do_net_cmd(cmd)
    logger.debug('do_gateway_check {} returned: {}'.format(cmd, result))
    return result


def drain_msg_queue(reg_q, pub_q=None, tmp_q=None, addr=None, method='handle_node'):
    """
    This function now handles several different methods; note the optional
    queue params should not be used together.
    :param reg_q: queue of registered nodes
    :param pub_q: queue of published nodes (use for publishing online nodes)
    :param tmp_q: queue of nodes/addrs for logging (use for publishing offline nodes)
    """
    import time
    from nanoservice import Publisher
    from node_tools.msg_queues import add_one_only

    if NODE_SETTINGS['use_localhost'] or not addr:
        addr = '127.0.0.1'

    pub = Publisher('tcp://{}:9442'.format(addr))
    id_list = list(reg_q)

    # Need to wait a bit on connect to prevent lost messages
    time.sleep(0.002)

    for _ in id_list:
        with reg_q.transact():
            node_id = reg_q.popleft()
        pub.publish(method, node_id)
        if pub_q is not None:
            with pub_q.transact():
                add_one_only(node_id, pub_q)
        logger.debug('Published msg {} to {}'.format(node_id, addr))


@run_until_success()  # default max_retry is 2
def echo_client(fpn_id, addr, send_cfg=False):
    import json
    from node_tools import state_data as st
    from node_tools.node_funcs import node_state_check
    from node_tools.node_funcs import run_ztcli_cmd

    if NODE_SETTINGS['use_localhost'] or not addr:
        addr = '127.0.0.1'

    cfg = st.cfg_msgs
    node_data = st.fpnState
    reply_list = []
    reciept = False

    try:
        if send_cfg:
            reply_list = send_req_msg(addr, 'node_cfg', fpn_id)
            logger.debug('CFG: send_cfg reply is {}'.format(reply_list))
            if 'result' not in reply_list[0]:
                logger.warning('CFG: malformed reply {}'.format(reply_list))
            else:
                node_data['cfg_ref'] = reply_list[0]['ref']
                cfg = json.loads(reply_list[0]['result'])
                logger.debug('CFG: state has payload {}'.format(cfg))
                for net in cfg['networks']:
                    res = run_ztcli_cmd(action='join', extra=net)
                    logger.debug('run_ztcli_cmd join result: {}'.format(res))
        else:
            reply_list = send_req_msg(addr, 'echo', fpn_id)
            node_data['msg_ref'] = reply_list[0]['ref']
        reciept = True
        logger.debug('Send result is {}'.format(reply_list))
        if not send_cfg and not node_data['cfg_ref']:
            res = node_state_check(deorbit=True)
            logger.debug('node_state_check returned {}'.format(res))
    except Exception as exc:
        # success wrapper needs a warning to catch
        logger.warning('Send error is {}'.format(exc))
        raise exc

    return reply_list, reciept


def get_net_cmds(bin_dir, iface=None, state=False):
    import os

    res = None
    if not os.path.isdir(bin_dir):
        logger.error('No such path: {}'.format(bin_dir))
        return res

    if iface:
        cmds = ['fpn0-setup.sh', 'fpn0-down.sh', 'fpn1-setup.sh', 'fpn1-down.sh']
        cmd_str = 'down'
        if state:
            cmd_str = 'setup'
        for cmd in cmds:
            if iface in cmd and cmd_str in cmd:
                cmd_file = os.path.join(bin_dir, cmd)
                if os.path.isfile(cmd_file):
                    res = [cmd_file]
                return res

    else:
        up0 = os.path.join(bin_dir, 'fpn0-setup.sh')
        down0 = os.path.join(bin_dir, 'fpn0-down.sh')
        up1 = os.path.join(bin_dir, 'fpn1-setup.sh')
        down1 = os.path.join(bin_dir, 'fpn1-down.sh')

        cmds = [up0, down0, up1, down1]
        for thing in cmds:
            if not os.path.isfile(thing):
                return res
        res = cmds

    return res


def publish_cfg_msg(trie, node_id, addr=None):
    """
    Publish node cfg message (to root node) with network ID to join.
    Node data is already populated in the ID trie.
    :param trie: `id_trie` state trie
    :param node_id: ID of mbr node to configure
    :param addr: IP address of subscriber
    """
    import time
    from nanoservice import Publisher
    from node_tools.msg_queues import make_cfg_msg

    if NODE_SETTINGS['use_localhost'] or not addr:
        addr = '127.0.0.1'

    pub = Publisher('tcp://{}:9442'.format(addr))

    # Need to wait a bit on connect to prevent lost messages
    time.sleep(0.002)

    msg = make_cfg_msg(trie, node_id)

    pub.publish('cfg_msgs', msg)
    logger.debug('CFG: sent cfg msg {} for node {} to {}'.format(msg, node_id, addr))


@catch_exceptions()
def run_cleanup_check(cln_q, pub_q):
    """
    Command wrapper for decorated cleanup_check (offline data) command.
    :notes: this needs provisioning of the proper tgt IP address
    """
    clean_list = list(cln_q)
    if len(clean_list) != 0:
        for node_id in clean_list:
            if node_id not in list(pub_q):
                try:
                    send_pub_msg('127.0.0.1', 'offline', node_id)
                except Exception as exc:
                    logger.error('Send error is {}'.format(exc))
        cln_q.clear()


@catch_exceptions()
def run_host_check():
    """
    Command wrapper for decorated host_check (net health) command.
    """
    result = do_host_check()
    logger.debug('run_host_check returned tuple: {}'.format(result))
    return result


@catch_exceptions()
def run_net_check():
    """
    Command wrapper for decorated net_check (fpn health) command.
    """
    fpn_data = st.fpnState
    fpn0_state =st.fpn0Data['state']

    if fpn_data['fpn0'] and fpn0_state == 'UP':
        result = do_net_check()
        logger.debug('run_net_check returned tuple: {}'.format(result))
        return result


@run_until_success()
def run_net_cmd(cmd):
    """
    Command wrapper for decorated fpn0/fpn1 net command.
    """
    result = do_net_cmd(cmd)
    logger.debug('run net cmd {} returned tuple: {}'.format(cmd, result))
    return result


def do_net_cmd(cmd):
    """
    Actual net command runner (see above).
    """
    import os
    import subprocess

    res = b''
    state = False
    head, tail = os.path.split(cmd[0])
    if not head or not tail:
        logger.error('Bad cmd or path: {}'.format(cmd[0]))

    env_dict = {'VERBOSE': '',
                'DROP_DNS_53': '',
                'ROUTE_DNS_53': '',
                'SET_IPV4_IFACE': '',
                'DROP_IPV6': ''}

    if NODE_SETTINGS['drop_ipv6']:
        env_dict['DROP_IPV6'] = 'yes'
    if NODE_SETTINGS['route_dns_53']:
        env_dict['ROUTE_DNS_53'] = 'yes'
    if NODE_SETTINGS['private_dns_only']:
        env_dict['DROP_DNS_53'] = 'yes'
    if NODE_SETTINGS['default_iface'] is not None:
        env_dict['SET_IPV4_IFACE'] = NODE_SETTINGS['default_iface']
    logger.debug('ENV: net script settings are {}'.format(env_dict.items()))

    # with shell=false cmd must be a sequence not a string
    try:
        b = subprocess.Popen(cmd,
                             stderr=subprocess.PIPE,
                             stdout=subprocess.PIPE,
                             shell=False,
                             env=env_dict)

        out, err = b.communicate()
        retcode = b.returncode

        if err:
            logger.error('net cmd {} err: {}'.format(tail, err.decode().strip()))
            res = err
        if 'Success' in out.decode().strip() or 'geoloc' in out.decode().strip():
            state = True
            res = out
            logger.info('net cmd {} result: {}'.format(tail, out.decode().strip()))
        if retcode == 1:
            if 'setup' in tail:
                msg = out
            else:
                msg = err
            logger.error('net cmd {} msg: {}'.format(tail, msg.decode().strip()))
        if 'setup' in tail:
            if 'fpn0' in tail:
                st.fpn0Data['state'] = 'UP'
            else:
                st.fpn1Data['state'] = 'UP'
        if 'down' in tail:
            if 'fpn0' in tail:
                st.fpn0Data['state'] = 'DOWN'
            else:
                st.fpn1Data['state'] = 'DOWN'
        if retcode in [4, 6, 28]:
            logger.error('health check shows network failure!')

    except Exception as exc:
        logger.error('net cmd {} exception: {}'.format(tail, exc))
        retcode = exc

    return state, res, retcode


def send_pub_msg(addr, method, data):
    """
    """
    import time
    from nanoservice import Publisher

    if NODE_SETTINGS['use_localhost'] or not addr:
        addr = '127.0.0.1'

    pub = Publisher('tcp://{}:9442'.format(addr))

    # Need to wait a bit on connect to prevent lost messages
    time.sleep(0.002)

    pub.publish(method, data)
    logger.debug('PUB: sent {} msg with paylod {} to {}'.format(method, data, addr))


def send_req_msg(addr, method, data):
    """
    """
    from nanoservice import Requester

    if NODE_SETTINGS['use_localhost'] or not addr:
        addr = '127.0.0.1'

    c = Requester('tcp://{}:9443'.format(addr), timeouts=(1000, 1000))
    reply = []

    try:
        reply = c.call(method, data)
        return reply
    except Exception as exc:
        logger.warning('Call error is {}'.format(exc))
        raise exc


def send_wedged_msg(addr=None):
    """
    Send a special msg type if my routing is stuffed.
    :param addr: moon address if known
    """
    from node_tools.helper_funcs import AttrDict
    from node_tools import state_data as st

    state = AttrDict.from_nested_dict(st.fpnState)
    node_id = state.fpn_id
    reply = []

    if not addr:
        addr = state.moon_addr
    if NODE_SETTINGS['use_localhost'] or not addr:
        addr = '127.0.0.1'

    try:
        reply = send_req_msg(addr, 'wedged', node_id)
        logger.warning('WEDGED: msg reply: {}'.format(reply))

    except Exception as exc:
        logger.error('Send error is {}'.format(exc))

    return reply
