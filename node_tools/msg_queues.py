# coding: utf-8

"""msg queue-specific helper functions."""

import logging


logger = logging.getLogger(__name__)


def handle_announce_msg(node_q, reg_q, wait_q, msg):
    for node in list(wait_q):
        if node not in list(reg_q):
            if msg == node:
                with reg_q.transact():
                    reg_q.append(msg)
    for node in list(node_q):
        if node not in list(reg_q):
            if msg == node:
                with reg_q.transact():
                    reg_q.append(msg)


def handle_node_queues(node_q, staging_q):
    staging_list = []
    for _ in list(node_q):
        with node_q.transact():
            node_id = node_q.popleft()
            if node_id not in staging_list:
                staging_list.append(node_id)
    for node_id in staging_list:
        if staging_q.count(node_id) < 1:
            with staging_q.transact():
                staging_q.append(node_id)


def manage_incoming_nodes(node_q, reg_q, wait_q):
    for node in list(reg_q):
        if node in list(node_q):
            with node_q.transact():
                node_q.remove(node)
    for node in list(wait_q):
        if wait_q.count(node) >= 3 or node in list(reg_q):
            while wait_q.count(node) != 0:
                wait_q.remove(node)
    for node in list(node_q):
        if wait_q.count(node) < 3:
            wait_q.append(node)
    with node_q.transact():
        node_q.clear()


def populate_leaf_list(node_q, wait_q, data):
    from node_tools import state_data as st

    st.leaf_nodes = []
    if data['identity'] in node_q or data['identity'] in wait_q:
        st.leaf_nodes.append({data['identity']: data['address']})


def valid_announce_msg(msg):
    import string

    try:
        assert len(msg) == 10
        assert set(msg).issubset(string.hexdigits)
    except:
        return False
    return True


def wait_for_cfg_msg(pub_q, active_q, msg):
    """
    Handle valid member node request for network ID(s) and return
    the result (or `None`).  Expects responder daemon to raise the
    nanoservice exception if result is `None`.
    :param pub_q: queue of published node IDs
    :param active_q: queue of active nodes with net IDs
    :param msg: net_id cfg message needing a response
    :return: JSON str (net_id cfg msg) or None
    """
    import json

    result = None

    if msg not in list(pub_q):
        logger.error('Node ID {} not in pub_queue'.format(msg))
    else:
        for item in list(active_q):
            node_cfg = json.loads(item)
            if msg == node_cfg['node_id']:
                result = node_cfg
                with pub_q.transact():
                    pub_q.remove(msg)
                logger.debug('Node ID {} removed from pub_q'.format(msg))
    return result
