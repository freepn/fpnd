#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Target:   Python 3.6

import datetime

import warnings
import pytest

from diskcache import Index

from node_tools.helper_funcs import get_cachedir
from node_tools.cache_funcs import get_status
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
        data = get_status(cache, 'node')
        assert isinstance(data, dict)
        assert len(data) == 2
        assert 'id' in data
        assert 'status' in data
        assert data.get('status') == 'ONLINE'

    def test_peer_get_status():
        data = get_status(cache, 'peer')
        assert isinstance(data, dict)
        assert len(data) == 2
        assert 'id' in data
        assert 'status' in data
        assert data.get('status') == 'PLANET' or 'MOON'


def test_api_warning_msg():
    with pytest.warns(UserWarning):
        warnings.warn("Cannot connect to ZeroTier API", UserWarning)


def test_enodata_warning_msg():
    with pytest.warns(UserWarning):
        warnings.warn("Cache empty and API returned ENODATA", UserWarning)


def test_aging_not_available_warning_msg():
    with pytest.warns(UserWarning):
        warnings.warn("Cache aging not available", UserWarning)
