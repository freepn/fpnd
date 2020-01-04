# coding: utf-8

"""Data update helper functions."""
from __future__ import print_function

import logging
import datetime
import functools

from diskcache import Index

from node_tools.cache_funcs import get_state
from node_tools.helper_funcs import get_cachedir
from node_tools.helper_funcs import update_state
from node_tools.helper_funcs import ENODATA
from node_tools.helper_funcs import NODE_SETTINGS

try:
    from datetime import timezone
    utc = timezone.utc
except ImportError:
    from daemon.timezone import UTC
    utc = UTC()


logger = logging.getLogger(__name__)
cache = Index(get_cachedir())
max_age = NODE_SETTINGS['max_cache_age']


def do_logstats(msg=None):
    """Log cache size/key stats with optional ``msg`` string"""
    size = len(cache)
    if msg:
        logger.debug(msg)
    logger.debug('{} items currently in cache.'.format(size))
    logger.debug('Cache items: {}'.format(list(cache)))


def with_cache_aging(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        """
        cache wrapper to manage timestamp age for update_runner()
        * get timestamp and clear cache if greater than max_age
        * update cache timestamp based on result
        * log some debug info
        :return result: result from update_runner()
        """
        stamp = None
        utc_stamp = datetime.datetime.now(utc)
        do_logstats('Entering cache wrapper')
        if 'utc-time' in cache:
            stamp = cache['utc-time']
            cache_age = utc_stamp - stamp  # this is a timedelta
            logger.debug('Cache age is: {} sec'.format(cache_age.seconds))
            logger.debug('Maximum cache age: {} sec'.format(max_age))
            if cache_age.seconds > max_age:
                logger.debug('Cache data is too old!!')
                logger.debug('Stale data will be removed!!')
                cache.clear()
            else:
                logger.info('Cache is {} sec old (still valid)'.format(cache_age.seconds))
        else:
            cache.update([('utc-time', utc_stamp)])

        result = func(*args, **kwargs)
        logger.info('Get data result: {}'.format(result))

        if stamp is not None and result is ENODATA or None:
            cache.update([('utc-time', stamp)])
            logger.debug('Old cache time is: {:%Y-%m-%d %H:%M:%S %Z}'.format(stamp))
        else:
            cache.update([('utc-time', utc_stamp)])
            logger.debug('New cache time is: {:%Y-%m-%d %H:%M:%S %Z}'.format(utc_stamp))
        return result
    return wrapper


def with_state_check(func):
    @functools.wraps(func)
    def state_check(*args, **kwargs):
        """
        cache wrapper for checking nodeState before and after the
        update_runner() tries to grab new data.

        """
        oldState = get_state(cache)
        if not oldState.online:
            logger.warning('nodeState not initialized (node not online)')
        else:
            logger.info('Node online with id: {}'.format(oldState.fpn_id))

        result = func(*args, **kwargs)

        newState = get_state(cache)
        if not newState.online and not oldState.online:
            logger.warning('nodeState still not initialized (node not online)')
        elif newState.online and oldState.online:
            if newState == oldState:
                logger.info('No state change, all is well')
        return result
    return state_check


@with_cache_aging
@with_state_check
def update_runner():
    try:
        res = update_state()
        size = len(cache)
    except:  # noqa: E722
        logger.error('No data available, cache was NOT updated')
        pass
    else:
        if size < 1:
            logger.debug('No data available (live or cached)')
        elif size > 0:
            do_logstats()
        else:
            logger.debug('Cache empty and API returned ENODATA')
    do_logstats('Leaving update_runner')
    return res
