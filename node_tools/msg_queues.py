# coding: utf-8

"""msg queue-specific helper functions."""
import logging


logger = logging.getLogger('node_tools.msg_queues')


def add_one_only(item, deque):
    """
    Add item to deque only if not already present (ie, avoid duplicates).
    """
    if deque.count(item) < 1:
        deque.append(item)


def clean_from_queue(item, deque):
    """
    Remove all instances of item from deque.
    """
    while deque.count(item) != 0:
        thing = deque.peek()
        if thing == item:
            deque.pop()
        else:
            deque.rotate()


def handle_announce_msg(node_q, reg_q, wait_q, hold_q, msg):
    for node in list(node_q):
        if msg == node:
            with reg_q.transact():
                reg_q.append(msg)
    for node in list(wait_q):
        if msg == node:
            with reg_q.transact():
                reg_q.append(msg)


def handle_node_queues(node_q, staging_q):
    for _ in list(node_q):
        with node_q.transact():
            node_id = node_q.popleft()
        with staging_q.transact():
            add_one_only(node_id, staging_q)


def handle_wedged_nodes(trie, wdg_q, off_q):
    """
    Use node ID in wedged queue to lookup the corresponding exit node ID
    and add it to the offline queue.  This is the only way we currently
    have to remove a wedged exit node.
    """
    from node_tools.ctlr_funcs import is_exit_node
    from node_tools.trie_funcs import get_wedged_node_id

    deduped = list(set(list(wdg_q)))
    for node_id in deduped:
        with wdg_q.transact():
            clean_from_queue(node_id, wdg_q)
        wedged_node = get_wedged_node_id(trie, node_id)
        if wedged_node is not None:
            if not is_exit_node(wedged_node):
                with off_q.transact():
                    add_one_only(wedged_node, off_q)


def make_cfg_msg(trie, node_id):
    """
    Create the net_cfg msg for a node and return cfg string.  Node
    IDs come from the node/active queues and networks come from the
    `id_trie`.
    :param trie: state trie of nodes/nets
    :param node_id: node ID
    :return: JSON str (net_id cfg msg)
    """
    import json

    d = {
        "node_id": "{}".format(node_id),
        "networks": []
    }

    d["networks"] = trie[node_id][0]

    return json.dumps(d)


def manage_incoming_nodes(node_q, reg_q, wait_q):
    with node_q.transact():
        for node in list(reg_q):
            if node in list(node_q):
                node_q.remove(node)
    for node in list(wait_q):
        if wait_q.count(node) >= 3 or node in list(reg_q):
            clean_from_queue(node, wait_q)
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


def process_hold_queue(msg, hold_q, reg_q, max_hold=5):
    """
    Process nodes in a holding queue if no matching cfg msg is found.
    Wait for `max_hold` and then move back to reg_q.
    :param msg: net_id cfg message needing a response (node ID)
    :param hold_q: queue of pending nodes (waiting for cfg)
    :param reg_q: queue of registered nodes
    :param max_hold: max number of node msgs processed
    """
    with hold_q.transact():
        hold_q.append(msg)
    logger.debug('Node ID {} held in hold_q'.format(msg))

    if hold_q.count(msg) > max_hold:
        with reg_q.transact():
            add_one_only(msg, reg_q)
        logger.debug('Node ID {} sent back to reg_q'.format(msg))
        with hold_q.transact():
            clean_from_queue(msg, hold_q)


def valid_announce_msg(msg):
    import string

    if not (len(msg) == 10 and set(msg).issubset(string.hexdigits)):
        raise AssertionError('Announce msg {} is invalid!'.format(msg))
    return True


def valid_cfg_msg(msg):
    import json
    import string

    if isinstance(msg, str) and 'node_id' in msg:
        cfg = json.loads(msg)
        id_str = cfg['node_id']
        if (set(id_str).issubset(string.hexdigits) and
                len(id_str) == 10 and
                'networks' in cfg.keys() and
                len(cfg) == 2):
            return True
        else:
            raise AssertionError('Config msg {} is invalid!'.format(msg))
    else:
        raise AssertionError('Config msg {} is invalid!'.format(msg))


def wait_for_cfg_msg(cfg_q, hold_q, reg_q, msg):
    """
    Handle valid member node request for network ID(s) and return
    the result (or `None`).  Expects client wrapper to raise the
    nanoservice warning if no cfg result. We use the hold queue as
    a timeout mechanism and re-add to the reg queue after `max_hold`
    attempts with no cfg result.
    :param cfg_q: queue of cfg msgs (nodes with net IDs)
    :param hold_q: queue of pending nodes (waiting for cfg)
    :param msg: (outgoig) net_id cfg message needing a response
    :return: JSON str (net_id cfg msg) or None
    """
    import json

    result = None

    if len(cfg_q) == 0:
        process_hold_queue(msg, hold_q, reg_q, max_hold=3)
    else:
        for item in list(cfg_q):
            cfg_dict = json.loads(item)
            if msg == cfg_dict['node_id']:
                result = item
                with cfg_q.transact():
                    cfg_q.remove(item)
                if msg in list(hold_q):
                    with hold_q.transact():
                        clean_from_queue(msg, hold_q)
            else:
                process_hold_queue(msg, hold_q, reg_q, max_hold=3)

    if not result:
        logger.debug('Node ID {} not found'.format(msg))
    return result
