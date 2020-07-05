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

from node_tools import __version__ as fpnd_version

from node_tools.ctlr_funcs import gen_netobj_queue
from node_tools.cache_funcs import delete_cache_entry
from node_tools.data_funcs import update_runner
from node_tools.helper_funcs import NODE_SETTINGS
from node_tools.helper_funcs import do_setup
from node_tools.helper_funcs import get_cachedir
from node_tools.helper_funcs import network_cruft_cleaner
from node_tools.helper_funcs import set_initial_role
from node_tools.helper_funcs import startup_handlers
from node_tools.helper_funcs import validate_role
from node_tools.logger_config import setup_logging
from node_tools.network_funcs import run_net_check
from node_tools.node_funcs import do_cleanup
from node_tools.node_funcs import do_startup
from node_tools.node_funcs import handle_moon_data
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


def check_daemon_status(script='msg_responder.py'):
    """
    Scheduling wrapper for managing rsp/sub daemons.
    """
    from node_tools.node_funcs import check_daemon
    from node_tools.node_funcs import control_daemon

    res = check_daemon(script)
    logger.debug('{} daemon status is {}'.format(script, res))

    if script == 'msg_responder.py':
        if not res:
            res = control_daemon('start', script)
            logger.debug('Starting {} daemon'.format(script))
    else:
        if not res:
            res = control_daemon('start', script)
            logger.debug('Starting {} daemon'.format(script))

    return res


def setup_scheduling(max_age):
    """Initial setup for scheduled jobs"""
    sleep_time = int(max_age / 6)

    baseUpdateJob = schedule.every(sleep_time).seconds
    baseUpdateJob.do(update_runner).tag('base-tasks', 'get-updates')

    show_scheduled_jobs()
    logger.debug('Leaving setup_scheduling')


def do_scheduling():
    set_initial_role()
    network_cruft_cleaner()
    schedule.run_all(1, 'base-tasks')
    validate_role()
    node_role = NODE_SETTINGS['node_role']
    mode = NODE_SETTINGS['mode']

    if mode == 'peer':
        if node_role is None:
            check_time = 33
            baseCheckJob = schedule.every(check_time).seconds
            baseCheckJob.do(run_net_check).tag('base-tasks', 'route-status')
            try:
                data = wait_for_moon(timeout=30)
            except Exception as exc:
                logger.error('ENODATA exception {}'.format(exc))
            if data == []:
                logger.error('NETSTATE: no moon data; network unreachable?')
            handle_moon_data(data)
            startup_handlers()

        else:
            if node_role == 'controller':
                netobj_q = dc.Deque(directory=get_cachedir('netobj_queue'))
                gen_netobj_queue(netobj_q)
                cache = dc.Index(get_cachedir())
                for key_str in ['peer', 'moon', 'mstate']:
                    delete_cache_entry(cache, key_str)

            elif node_role == 'moon':
                schedule.every(15).minutes.do(check_daemon_status).tag('chk-tasks', 'responder')

            schedule.every(15).minutes.do(check_daemon_status, script='msg_subscriber.py').tag('chk-tasks', 'subscriber')
            schedule.run_all(1, 'chk-tasks')

    elif mode == 'adhoc':
        logger.debug('Running in adhoc mode...')
        if NODE_SETTINGS['nwid']:
            logger.debug('ADHOC: found network {}'.format(NODE_SETTINGS['nwid']))
            do_startup(NODE_SETTINGS['nwid'])
        else:
            logger.error('No network ID found in NODE_SETTINGS!!')
            logger.error('Have you created a network yet?')

    logger.debug('MODE: startup mode is {} and role is {}'.format(mode, node_role))
    logger.info('You are running fpnd/node_tools version {}'.format(fpnd_version))

    while True:
        schedule.run_pending()
        time.sleep(1)


# Inherit from Daemon class
class fpnDaemon(Daemon):
    def cleanup(self):

        do_cleanup()

    # implement run method
    def run(self):

        do_scheduling()


if __name__ == "__main__":
    home, pid_file, log_file, debug, msg, mode, role = do_setup()
    setup_logging(debug, log_file)
    logger.debug('fpnd.ini set startup mode: {} and role: {}'.format(mode, role))
    if not home:
        home = '.'
    setup_scheduling(max_age)

    if len(sys.argv) == 2:
        arg = sys.argv[1]
        if arg in ('start'):
            logger.info(msg)
        if arg in ('start', 'stop', 'restart', 'status'):
            d = fpnDaemon(pid_file, home_dir=home, verbose=0, use_cleanup=True)
            getattr(d, arg)()
    else:
        print("usage: %s start|stop|restart|status" % sys.argv[0])
        sys.exit(2)
