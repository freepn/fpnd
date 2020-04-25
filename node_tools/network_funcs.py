# coding: utf-8

"""Network helper functions."""
from __future__ import print_function

import logging

from node_tools.helper_funcs import NODE_SETTINGS
from node_tools.sched_funcs import run_until_success


logger = logging.getLogger(__name__)


def do_peer_check(ztaddr):
    """
    ADHOC MODE
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
            logger.debug('ADHOC: found target IP addr {}'.format(addr))

    home = NODE_SETTINGS['home_dir']
    cmd_file = os.path.join(home, 'ping_gateway.sh')
    cmd = [cmd_file, addr]

    result = do_net_cmd(cmd)
    logger.debug('do_gateway_check {} returned: {}'.format(cmd, result))
    return result


def drain_reg_queue(reg_q, pub_q, addr=None):
    import time
    from nanoservice import Publisher

    if NODE_SETTINGS['use_localhost'] or not addr:
        addr = '127.0.0.1'

    pub = Publisher('tcp://{}:9442'.format(addr))
    id_list = list(reg_q)

    # Need to wait a bit on connect to prevent lost messages
    time.sleep(0.002)

    for _ in id_list:
        with reg_q.transact():
            node_id = reg_q.popleft()
        pub.publish('handle_node', node_id)
        with pub_q.transact():
            pub_q.append(node_id)
        logger.debug('Published msg {} to {}'.format(node_id, addr))


@run_until_success(max_retry=4)
def echo_client(fpn_id, addr, send_cfg=False):
    import json
    from nanoservice import Requester
    from node_tools import state_data as st
    from node_tools.node_funcs import node_state_check
    from node_tools.node_funcs import run_ztcli_cmd

    if NODE_SETTINGS['use_localhost'] or not addr:
        addr = '127.0.0.1'

    cfg = st.cfg_msgs
    node_data = st.fpnState
    reply_list = []
    reciept = False
    c = Requester('tcp://{}:9443'.format(addr), timeouts=(1000, 1000))

    try:
        if send_cfg:
            reply_list = c.call('node_cfg', fpn_id)
            logger.debug('CFG: send_cfg reply is {}'.format(reply_list))
            if 'result' not in reply_list[0]:
                logger.warning('CFG: malformed reply {}'.format(reply_list))
            else:
                node_data['cfg_ref'] = reply_list[0]['ref']
                cfg = json.loads(reply_list[0]['result'])
                logger.debug('CFG: state has payload {}'.format(cfg))
                for net in cfg['networks']:
                    res = run_ztcli_cmd(action='join', extra=net)
                    logger.warning('run_ztcli_cmd join result: {}'.format(res))
        else:
            reply_list = c.call('echo', fpn_id)
            node_data['msg_ref'] = reply_list[0]['ref']
        reciept = True
        logger.debug('Send result is {}'.format(reply_list))
        if not send_cfg and not node_data['cfg_ref']:
            res = node_state_check()
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

    # with shell=false cmd must be a sequence not a string
    try:
        b = subprocess.Popen(cmd,
                             stderr=subprocess.PIPE,
                             stdout=subprocess.PIPE,
                             shell=False,
                             env={'VERBOSE': ''})

        out, err = b.communicate()
        retcode = b.returncode

        if err:
            logger.error('net cmd {} err: {}'.format(tail, err.decode().strip()))
            res = err
        elif 'Success' in out.decode().strip():
            state = True
            res = out
            logger.info('net cmd {} result: {}'.format(tail, out.decode().strip()))
        elif retcode == 1:
            if 'setup' in tail:
                msg = out
            else:
                msg = err
            logger.error('net cmd {} msg: {}'.format(tail, msg.decode().strip()))

    except Exception as exc:
        logger.error('net cmd {} exception: {}'.format(tail, exc))
        retcode = exc

    return state, res, retcode
