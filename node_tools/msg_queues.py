# coding: utf-8

"""msg queue-specific helper functions."""
import logging


def handle_announce_msg(node_q, reg_q, wait_q, msg):
    for node in list(wait_q):
        if node not in list(reg_q):
            if msg == node:
                reg_q.append(msg)
    for node in list(node_q):
        if node not in list(reg_q):
            if msg == node:
                reg_q.append(msg)


def manage_incoming_nodes(node_q, reg_q, wait_q):
    for node in list(reg_q):
        if node in list(node_q):
            node_q.remove(node)
    for node in list(wait_q):
        if wait_q.count(node) >= 3 or node in list(reg_q):
            while wait_q.count(node) != 0:
                wait_q.remove(node)
    for node in list(node_q):
        if wait_q.count(node) < 3:
            wait_q.append(node)
    node_q.clear()


def valid_announce_msg(msg):
    import string

    try:
        assert len(msg) == 10
        assert set(msg).issubset(string.hexdigits)
    except:
        return False
    return True
