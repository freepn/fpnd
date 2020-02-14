# coding: utf-8

"""msg queue-specific helper functions."""
import logging


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
            staging_list.append(node_id)
    for node_id in staging_list:
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
