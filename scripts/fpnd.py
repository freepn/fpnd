#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Target:   Python 3.6

import os
import sys
import time
import datetime
import logging
import schedule
import functools

import diskcache as dc
from daemon import Daemon

from node_tools.ctlr_funcs import gen_netobj_queue
from node_tools.cache_funcs import delete_cache_entry
from node_tools.data_funcs import update_runner
from node_tools.helper_funcs import NODE_SETTINGS
from node_tools.helper_funcs import do_setup
from node_tools.helper_funcs import get_cachedir
from node_tools.helper_funcs import set_initial_role
from node_tools.helper_funcs import startup_handlers
from node_tools.helper_funcs import validate_role
from node_tools.logger_config import setup_logging
from node_tools.node_funcs import run_subscriber_daemon
from node_tools.node_funcs import wait_for_moon

try:
    from datetime import timezone
    utc = timezone.utc
except ImportError:
    from daemon.timezone import UTC
    utc = UTC()


logger = logging.getLogger('fpnd')
max_age = NODE_SETTINGS['max_cache_age']
timestamp = datetime.datetime.now(utc)  # use local time for console


def show_scheduled_jobs():
    """
    Show job info for all currently scheduled jobs.  Normally run
    once at startup.  Also shows tags for base jobs.
    """
    for job in schedule.jobs:
        logger.debug('JOBS: {}'.format(job))
        if 'base' in str(job.tags):
            logger.debug('TAGS: {}'.format(job.tags))


def setup_scheduling(max_age):
    """Initial setup for scheduled jobs"""
    sleep_time = max_age / 6

    baseUpdateJob = schedule.every(sleep_time).seconds
    baseUpdateJob.do(update_runner).tag('base-tasks', 'get-updates')

    show_scheduled_jobs()
    logger.debug('Leaving setup_scheduling: {}'.format(baseUpdateJob))


def do_scheduling():
    set_initial_role()
    schedule.run_all(1, 'base-tasks')
    validate_role()
    node_role = NODE_SETTINGS['node_role']

    if node_role is None:
        try:
            wait_for_moon()
        except Exception as exc:
            logger.error('ENODATA exception {}'.format(exc))
        startup_handlers()

    elif node_role == 'controller':
        netobj_q = dc.Deque(directory=get_cachedir('netobj_queue'))
        gen_netobj_queue(netobj_q, ipnet='192.168.10.0/24')
        cache = dc.Index(get_cachedir())
        for key_str in ['peer', 'moon', 'mstate']:
            delete_cache_entry(cache, key_str)
        run_subscriber_daemon()

    logger.debug('ROLE: startup role {}'.format(node_role))

    while True:
        schedule.run_pending()
        time.sleep(1)


# Inherit from Daemon class
class fpnDaemon(Daemon):
    # implement run method
    def run(self):

        do_scheduling()


if __name__ == "__main__":
    home, pid_file, log_file, debug, msg = do_setup()
    setup_logging(debug, log_file)
    logger.debug('do_setup returned Home: {} and debug: {}'.format(home, debug))
    setup_scheduling(max_age)
    if not home:
        home = '.'

    if len(sys.argv) == 2:
        arg = sys.argv[1]
        if arg in ('start'):
            logger.info(msg)
        if arg in ('start', 'stop', 'restart'):
            d = fpnDaemon(pid_file, home_dir=home, verbose=0)
            getattr(d, arg)()
    else:
        print("usage: %s start|stop|restart" % sys.argv[0])
        sys.exit(2)
