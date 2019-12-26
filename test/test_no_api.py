#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Target:   Python 3.6

import datetime

import warnings
import pytest

from diskcache import Index

from node_tools.helper_funcs import get_cachedir
from node_tools.helper_funcs import update_state
from node_tools.cache_funcs import get_endpoint_data
from node_tools.cache_funcs import get_net_status
from node_tools.cache_funcs import get_node_status
from node_tools.cache_funcs import get_peer_status
from node_tools.data_funcs import update_runner
from node_tools.helper_funcs import ENODATA, NODE_SETTINGS

try:
    from datetime import timezone
    utc = timezone.utc
except ImportError:
    from daemon.timezone import UTC
    utc = UTC()


# has_aging = False
cache = Index('test/test_data')
max_age = NODE_SETTINGS['max_cache_age']
utc_stamp = datetime.datetime.now(utc)  # use local time for console


def should_be_enodata_or_ok():
    # res = update_state()
    res = update_runner()
    return res


def test_should_be_enodata_or_ok():
    res = should_be_enodata_or_ok()
    assert res == ENODATA or 'OK'
    return res


res = test_should_be_enodata_or_ok()
# res = update_runner()
print(res)

size = len(cache)


if size:
    def test_node_get_status():
        Node = get_node_status(cache)
        assert isinstance(Node, tuple)
        if Node:
            print('Node:')
            assert hasattr(Node, 'status')
            assert hasattr(Node, 'tcpFallback')
            assert Node.tcpFallback is False
            print(Node)

    def test_peer_get_status():
        peers = get_peer_status(cache)
        assert isinstance(peers, list)
        if peers:
            print('Peers:')
            for Peer in peers:
                assert isinstance(Peer, tuple)
                assert hasattr(Peer, 'role')
                assert Peer.active is True
                assert hasattr(Peer, 'address')
                print(Peer)

    def test_net_get_status():
        nets = get_net_status(cache)
        assert isinstance(nets, list)
        if nets:
            print('Nets:')
            for Net in nets:
                assert isinstance(Net, tuple)
                assert hasattr(Net, 'mac')
                assert hasattr(Net, 'gateway')
                print(nets)

    def test_get_endpoint_data_node():
        key_list, values = get_endpoint_data(cache, 'node')
        print(key_list)
        if key_list:
            assert isinstance(key_list, list)
            assert 'node' in str(key_list)
            assert values[0].online

    def test_get_endpoint_data_peer():
        key_list, values = get_endpoint_data(cache, 'peer')
        print(key_list)
        if key_list:
            assert isinstance(key_list, list)
            assert 'peer' in str(key_list)
            assert values[0].role == 'PLANET'


def test_api_warning_msg():
    with pytest.warns(UserWarning):
        warnings.warn("Cannot connect to ZeroTier API", UserWarning)


def test_enodata_warning_msg():
    with pytest.warns(UserWarning):
        warnings.warn("Cache empty and API returned ENODATA", UserWarning)


def test_aging_not_available_warning_msg():
    with pytest.warns(UserWarning):
        warnings.warn("Cache aging not available", UserWarning)
