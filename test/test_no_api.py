#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Target:   Python 3.6

import datetime

import warnings
import pytest

from diskcache import Index

from node_tools.helper_funcs import get_cachedir
from node_tools.data_funcs import update_runner
from node_tools.helper_funcs import ENODATA, NODE_SETTINGS

try:
    from datetime import timezone
    utc = timezone.utc
except ImportError:
    from daemon.timezone import UTC
    utc = UTC()


has_aging = False
cache = Index(get_cachedir())
max_age = NODE_SETTINGS['max_cache_age']
utc_stamp = datetime.datetime.now(utc)  # use local time for console


# reset timestamp if needed
try:
    stamp = cache['utc-time']
    cache_age = utc_stamp - stamp  # this is a timedelta
    has_aging = True
    print('Cache age is: {} sec'.format(cache_age.seconds))
    print('Maximum cache age: {} sec'.format(max_age))
    if cache_age.seconds > max_age:
        print('Cache data is too old!!')
        print('Stale data will be removed!!')
        cache.clear()

except KeyError:
    pass
    has_aging = False


def should_be_enodata_or_ok():
    res = update_runner()
    return res


# res = update_state()
# res = update_runner()


def test_should_be_enodata_or_ok():
    res = should_be_enodata_or_ok()
    assert res == ENODATA or 'OK'
    return res


def test_api_warning_msg():
    with pytest.warns(UserWarning):
        warnings.warn("Cannot connect to ZeroTier API", UserWarning)


def test_enodata_warning_msg():
    with pytest.warns(UserWarning):
        warnings.warn("Cache empty and API returned ENODATA", UserWarning)


def test_aging_not_available_warning_msg():
    with pytest.warns(UserWarning):
        warnings.warn("Cache aging not available", UserWarning)


res = test_should_be_enodata_or_ok
size = len(cache)

if size > 0:
    print('Get data result: {}'.format(res))
    size = len(cache)
    print('{} items now in cache.'.format(size))
    print('Cache items: {}'.format(list(cache)))

    if has_aging:
        if res is ENODATA or res is None:
            cache.update([('utc-time', stamp)])
        else:
            cache.update([('utc-time', utc_stamp)])
        print('Cache time is: {} sec'.format(utc_stamp.isoformat(' ')))
    else:
        print('Cache aging not available')
else:
    print('Cache empty and API returned ENODATA')
