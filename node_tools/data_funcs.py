# coding: utf-8

"""Data update helper functions."""
from __future__ import print_function

import logging
import datetime
import functools

from diskcache import Index

from node_tools.cache_funcs import get_state
from node_tools.helper_funcs import get_cachedir
from node_tools.helper_funcs import log_fpn_state
from node_tools.helper_funcs import run_event_handlers
from node_tools.helper_funcs import update_state
from node_tools.helper_funcs import AttrDict
from node_tools.helper_funcs import ENODATA
from node_tools.helper_funcs import NODE_SETTINGS

from datetime import timezone


utc = timezone.utc
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


def get_state_values(old, new, pairs=False):
    """
    Get ordered changes for two state item views
    :param old: old state dict
    :param new: new state dict
    :param pairs: if true, each tuple in the return list will contain a
                  tuple of pairs for each change (old, new).  otherwise
                  return a tuple with only the new value for each change.
    :return: None (updates state_data.changes)
    """
    from node_tools import state_data as st

    if isinstance(old, dict) and isinstance(new, dict):
        diff = []
        if old == new:
            logger.debug('State is unchanged')
        else:
            if not pairs:
                diff = [j for i, j in zip(old.items(), new.items()) if i != j]
            else:
                diff = []
                for i, j in zip(old.items(), new.items()):
                    if i != j:
                        item = (i, j)
                        diff.append(item)
                logger.debug('State changed: {}'.format(diff))
        st.changes = tuple(diff)


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
        from node_tools import state_data as st

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
        log_fpn_state()
        run_event_handlers()
        return result
    return wrapper


def with_state_check(func):
    @functools.wraps(func)
    def state_check(*args, **kwargs):
        """
        cache wrapper for checking nodeState before and after the
        update_runner() tries to grab new data.

        """
        from node_tools import state_data as st

        get_state(cache)
        prev_state = AttrDict.from_nested_dict(st.fpnState)

        if not prev_state.online:
            logger.warning('nodeState not initialized (node not online)')
        else:
            logger.info('Node online with id: {}'.format(prev_state.fpn_id))

        result = func(*args, **kwargs)

        get_state(cache)
        next_state = AttrDict.from_nested_dict(st.fpnState)

        if not next_state.online and not prev_state.online:
            logger.warning('nodeState still not initialized (node not online)')
        elif next_state.online and prev_state.online:
            get_state_values(prev_state, next_state)
            logger.debug('State diff is: {}'.format(st.changes))

        return result
    return state_check


@with_cache_aging
@with_state_check
def update_runner():
    size = len(cache)
    try:
        res = update_state()
        logger.debug('API result: {}'.format(res))
    except:  # noqa: E722
        logger.warning('No data available, cache was NOT updated')
        pass
    else:
        if size < 1:
            logger.warning('No data available (live or cached)')
        elif size > 0:
            do_logstats()
        else:
            logger.warning('Cache empty and API returned ENODATA')
    do_logstats('Leaving update_runner')
    return res
