# -*- coding: utf-8 -*-
import os
import sys
import time
import shutil
import datetime
import logging
import ipaddress
# import mock
import string
import tempfile

import datrie
import pytest

from diskcache import Index

from node_tools.cache_funcs import delete_cache_entry
from node_tools.cache_funcs import find_keys
from node_tools.cache_funcs import load_cache_by_type
from node_tools.cache_funcs import get_endpoint_data
from node_tools.cache_funcs import get_net_status
from node_tools.cache_funcs import get_node_status
from node_tools.cache_funcs import get_peer_status
from node_tools.cache_funcs import get_state
from node_tools.cache_funcs import handle_node_status
from node_tools.ctlr_funcs import get_network_id
from node_tools.data_funcs import get_state_values
from node_tools.data_funcs import update_runner
from node_tools.exceptions import MemberNodeError
from node_tools.helper_funcs import AttrDict
from node_tools.helper_funcs import ENODATA
from node_tools.helper_funcs import NODE_SETTINGS
from node_tools.helper_funcs import config_from_ini
from node_tools.helper_funcs import do_setup
from node_tools.helper_funcs import find_ipv4_iface
from node_tools.helper_funcs import get_cachedir
from node_tools.helper_funcs import get_filepath
from node_tools.helper_funcs import json_dump_file
from node_tools.helper_funcs import json_load_file
from node_tools.helper_funcs import log_fpn_state
from node_tools.helper_funcs import run_event_handlers
from node_tools.helper_funcs import set_initial_role
from node_tools.helper_funcs import update_state
from node_tools.helper_funcs import validate_role
from node_tools.msg_queues import populate_leaf_list
from node_tools.node_funcs import cycle_adhoc_net
from node_tools.node_funcs import do_cleanup
from node_tools.node_funcs import node_state_check
from node_tools.node_funcs import parse_moon_data
from node_tools.node_funcs import run_moon_cmd
from node_tools.node_funcs import run_ztcli_cmd
from node_tools.node_funcs import wait_for_moon
from node_tools.sched_funcs import check_return_status


try:
    from datetime import timezone
    utc = timezone.utc
except ImportError:
    from daemon.timezone import UTC
    utc = UTC()


class mock_zt_api_client(object):
    """
    Client API to serve simple GET data endpoints
    """
    def __init__(self):
        self.test_dir = 'test/test_data'
        self.response = '200'

    def get_data(self, endpoint):
        self.endpoint = json_load_file(endpoint, self.test_dir)
        return self.response, self.endpoint


add_net = {'authTokens': [{}],
           'capabilities': [],
           'creationTime': 1586844042713,
           'enableBroadcast': True,
           'id': 'b6079f73ca8129ad',
           'ipAssignmentPools': [],
           'mtu': 2800,
           'multicastLimit': 32,
           'name': 'gswpxcjojl_vs1hj68mve',
           'nwid': 'b6079f73ca8129ad',
           'objtype': 'network',
           'private': True,
           'remoteTraceLevel': 0,
           'remoteTraceTarget': None,
           'revision': 1,
           'routes': [],
           'rules': [{'not': False, 'or': False, 'type': 'ACTION_ACCEPT'}],
           'rulesSource': '',
           'tags': [],
           'v4AssignMode': {'zt': False},
           'v6AssignMode': {'6plane': False, 'rfc4193': False, 'zt': False}}


# has_aging = False
cache = Index(get_cachedir(dir_name='fpn_test'))
max_age = NODE_SETTINGS['max_cache_age']
utc_stamp = datetime.datetime.now(utc)  # use local time for console

client = mock_zt_api_client()


# special test cases
def read_file(filename):
    import codecs

    with codecs.open(filename, 'r', 'utf8') as f:
        return f.read()


def json_check(data):
    import json

    json_dump = json.dumps(data, indent=4, separators=(',', ': '))
    json_load = json.loads(json_dump)
    assert data == json_load


def load_data():
    _, node = client.get_data('status')
    _, peers = client.get_data('peer')
    _, nets = client.get_data('network')
    _, moons = client.get_data('moon')

    return node, peers, nets, moons


def test_dump_and_load_json():
    data_dir = get_cachedir(dir_name='fpn_test')
    (node_data, peer_data, net_data, moon_data) = load_data()
    json_dump_file('node', node_data, data_dir)
    node_dump = json_load_file('node', data_dir)
    json_check(node_dump)
    json_check(peer_data)
    json_check(net_data)
    json_check(moon_data)


def test_node_client_status():
    _, node_data = client.get_data('status')
    status = node_data.get('online')
    assert status


def test_peer_client_status():
    _, peer_data = client.get_data('peer')
    for peer in peer_data:
        if peer['paths'] != []:
            assert peer['paths'][0]['active']


def test_net_client_status():
    _, net_data = client.get_data('network')
    for net in net_data:
        status = net.get('status')
        assert status == 'OK'


def test_get_network_id():
    res = get_network_id(add_net)
    assert res == 'b6079f73ca8129ad'


def test_join_args():
    res = run_ztcli_cmd(action='join', extra='b6079f73ca8129ad')
    assert res is None or 'failed' in res
    res = cycle_adhoc_net('b6079f73ca8129ad', nap=1)
    assert res is None


def test_get_moon_data():
    res = run_ztcli_cmd(action='listmoons')
    assert isinstance(res, list)


def test_parse_moon_data():
    _, moon_data = client.get_data('moon')
    result = parse_moon_data(moon_data)
    # print(result)
    assert result == [('deadd738e6', '10.0.1.66', '9993'),
                      ('beefa7b693', '192.168.0.66', '9993')]


def test_get_node_info():
    res = run_ztcli_cmd(action='info')
    assert res is None or 'failed' in res


def test_orbit_moon():
    res = run_moon_cmd('deadd738e6', action='orbit')
    assert res is False


def test_deorbit_moon():
    res = run_moon_cmd('deadd738e6', action='deorbit')
    assert res is False


def test_unorbit_moon():
    res = run_moon_cmd('deadd738e6', action='unorbit')
    assert res is False


def test_wait_for_moon():
    res = wait_for_moon(timeout=1)
    assert res == []


def test_should_be_enodata():
    def should_be_enodata():
        res = update_state()
        return res

    res = should_be_enodata()
    assert res is ENODATA


def test_cache_loading():

    def test_cache_is_empty():
        cache.clear()
        assert list(cache) == []
        res = update_runner()
        assert res is ENODATA
        # print(res)

    def test_load_cache_node():
        _, node_data = client.get_data('status')
        load_cache_by_type(cache, node_data, 'node')
        assert len(list(cache)) == 1

    def test_update_cache_node():
        _, node_data = client.get_data('status')
        load_cache_by_type(cache, node_data, 'node')
        assert len(list(cache)) == 1

    def test_load_cache_peer():
        _, peer_data = client.get_data('peer')
        del peer_data[0]
        load_cache_by_type(cache, peer_data, 'peer')
        assert len(list(cache)) == 6

    def test_delete_cache_entry_no_key():
        delete_cache_entry(cache, 'reep')
        assert len(list(cache)) == 6

    def test_delete_cache_entry():
        delete_cache_entry(cache, 'peer')
        assert len(list(cache)) == 1

    def test_update_cache_peer():
        _, peer_data = client.get_data('peer')
        load_cache_by_type(cache, peer_data, 'peer')
        assert len(list(cache)) == 7

    def test_load_cache_net():
        _, net_data = client.get_data('network')
        load_cache_by_type(cache, net_data, 'net')
        assert len(list(cache)) == 9

    def test_update_cache_net():
        _, net_data = client.get_data('network')
        del net_data[1]
        load_cache_by_type(cache, net_data, 'net')
        assert len(list(cache)) == 8
        _, net_data = client.get_data('network')
        load_cache_by_type(cache, net_data, 'net')
        assert len(list(cache)) == 9

    def test_find_keys_nonet():
        assert find_keys(cache, 'net') is None

    def test_update_runner():
        res = update_runner()
        assert res is ENODATA
        # print(res)

    def test_cache_size():
        assert len(cache) == 9

    def test_handle_node_status():
        _, node_data = client.get_data('status')
        handle_node_status(node_data, cache)

    test_cache_is_empty()
    test_load_cache_node()
    test_update_cache_node()
    test_load_cache_peer()
    test_delete_cache_entry_no_key()
    test_delete_cache_entry()
    test_update_cache_peer()
    test_find_keys_nonet()
    test_load_cache_net()
    test_update_cache_net()
    test_update_runner()
    test_cache_size()
    test_handle_node_status()


def test_get_node_status():
    Node = get_node_status(cache)
    assert isinstance(Node, dict)
    assert 'status' in Node
    assert 'tcpFallback' in Node
    assert Node['tcpFallback'] is False


def test_get_peer_status():
    peers = get_peer_status(cache)
    assert isinstance(peers, list)
    for Peer in peers:
        assert isinstance(Peer, dict)
        assert 'role' in Peer
        assert 'address' in Peer
        assert Peer['active'] is True


def test_get_net_status():
    nets = get_net_status(cache)
    assert isinstance(nets, list)
    for Net in nets:
        assert isinstance(Net, dict)
        assert 'mac' in Net
        assert 'ztaddress' in Net
        assert 'gateway' in Net


def test_populate_leaf_list():
    import diskcache as dc
    from node_tools import state_data as st

    node_q = dc.Deque(directory='/tmp/test-nq')
    wait_q = dc.Deque(directory='/tmp/test-wq')
    node_q.clear()
    wait_q.clear()
    node_q.append('beef9f73c6')

    peers = get_peer_status(cache)
    for peer in peers:
        if peer['role'] == 'LEAF':
            populate_leaf_list(node_q, wait_q, peer)
            assert len(st.leaf_nodes) == 1
            assert st.leaf_nodes[0]['beef9f73c6'] == '134.47.250.137'

    node_q.clear()
    wait_q.append('beef9f73c6')
    for peer in peers:
        if peer['role'] == 'LEAF':
            populate_leaf_list(node_q, wait_q, peer)
            assert len(st.leaf_nodes) == 1
            assert st.leaf_nodes[0]['beef9f73c6'] == '134.47.250.137'

    wait_q.clear()
    st.leaf_nodes = []


def test_load_node_state():
    Node = get_node_status(cache)
    load_cache_by_type(cache, Node, 'nstate')
    assert len(cache) == 10
    # print(list(cache))


def test_load_moon_state():
    moonStatus = []
    fpn_moons = ['deadd738e6']
    peers = get_peer_status(cache)
    for peer in peers:
        if peer['role'] == 'MOON' and peer['identity'] in fpn_moons:
            moonStatus.append(peer)
            break
    load_cache_by_type(cache, moonStatus, 'mstate')
    assert len(cache) == 11


def test_load_net_state():
    Node = get_net_status(cache)
    load_cache_by_type(cache, Node, 'istate')
    assert len(cache) == 13


def test_load_new_state():
    Node = get_net_status(cache)
    load_cache_by_type(cache, Node, 'istate')
    assert len(cache) == 13


def test_find_keys():
    tuna = find_keys(cache, 'tuna')
    assert tuna is None
    node = find_keys(cache, 'node')
    assert 'node' in str(node)
    net = find_keys(cache, 'net')
    assert len(net) == 2


def test_find_state_keys():
    data = find_keys(cache, 'state')
    assert len(data) == 4
    s = str(data)
    assert 'nstate' in s
    assert 'mstate' in s
    assert 'istate' in s


def test_get_state():
    from node_tools import state_data as stest

    get_state(cache)
    nodeState = AttrDict.from_nested_dict(stest.fpnState)
    assert isinstance(nodeState, dict)
    assert nodeState.online
    assert nodeState.fpn_id == 'ddfd7368e6'
    assert not nodeState.fallback
    assert nodeState.fpn0
    assert nodeState.fpn1
    assert nodeState.moon_id0 == 'deadd738e6'
    assert nodeState['fpn_id0'] == 'b6079f73c63cea29'
    assert nodeState['fpn_id1'] == 'b6079f73ca8129ad'


def test_do_cleanup():
    from node_tools import state_data as stest

    get_state(cache)
    nodeState = AttrDict.from_nested_dict(stest.fpnState)
    # print(nodeState)
    do_cleanup('./bin')


def test_get_state_values():
    from node_tools import state_data as stest

    assert isinstance(stest.changes, list)
    assert not stest.changes

    get_state(cache)
    prev_state = AttrDict.from_nested_dict(stest.fpnState)
    assert prev_state.online
    assert prev_state.fpn0
    assert prev_state.fpn1

    # induce a change
    stest.fpnState.update(fpn1=False)
    next_state = AttrDict.from_nested_dict(stest.fpnState)
    assert not next_state.fpn1
    assert not stest.changes

    # now we should see old/new values in the state diff
    get_state_values(prev_state, next_state, True)
    assert isinstance(stest.changes, tuple)
    assert len(stest.changes) == 1
    assert len(stest.changes[0]) == 2
    get_state_values(prev_state, next_state)
    assert len(stest.changes[0]) == 2

    # reset shared state vars
    stest.changes = []
    stest.fpnState.update(fpn1=True)
    assert stest.fpnState == prev_state

    # induce two changes
    stest.fpnState.update(fpn0=False, fpn1=False)
    next_state = AttrDict.from_nested_dict(stest.fpnState)
    assert not next_state.fpn0
    assert not next_state.fpn1
    assert not stest.changes

    # now we should see only new values for both changes in the state diff
    get_state_values(prev_state, next_state)
    assert isinstance(stest.changes, tuple)
    assert len(stest.changes) == 2
    assert len(stest.changes[0]) == 2
    # reset shared state vars
    stest.changes = []


def test_node_state_check():
    from node_tools import state_data as stest

    state = AttrDict.from_nested_dict(stest.fpnState)
    assert state.cfg_ref is None
    res = node_state_check()
    assert res is None
    state.update(cfg_ref='7f5c6fc9-28d9-45d6-b210-1a08b958e219')
    res = node_state_check()
    state.update(cfg_ref=None)


def test_run_event_handler():
    from node_tools import state_data as st

    home, pid_file, log_file, debug, msg, mode, role = do_setup()

    prev_state = AttrDict.from_nested_dict(st.defState)
    next_state = AttrDict.from_nested_dict(st.defState)
    assert not st.changes

    get_state_values(prev_state, next_state)
    run_event_handlers(st.changes)
    assert len(st.changes) == 0

    next_state.update(fpn0=True, fpn1=True)
    get_state_values(prev_state, next_state)
    run_event_handlers(st.changes)
    log_fpn_state(st.changes)
    assert len(st.changes) == 2
