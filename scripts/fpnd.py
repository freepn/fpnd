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

from daemon import Daemon

from node_tools.data_funcs import update_runner
from node_tools.helper_funcs import NODE_SETTINGS
from node_tools.helper_funcs import do_setup
from node_tools.helper_funcs import startup_handlers
from node_tools.logger_config import setup_logging
from node_tools.node_funcs import get_moon_data
from node_tools.node_funcs import run_moon_cmd

try:
    from datetime import timezone
    utc = timezone.utc
except ImportError:
    from daemon.timezone import UTC
    utc = UTC()


logger = logging.getLogger('fpnd')
max_age = NODE_SETTINGS['max_cache_age']
moons = NODE_SETTINGS['moon_list']  # list of fpn moons to orbiit
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
    schedule.run_all(10, 'base-tasks')
    time.sleep(1)

    for moon in moons:
        res = run_moon_cmd(moon, action='orbit')

    moon_metadata = get_moon_data()
    logger.debug('Moon data size: {}'.format(len(moon_metadata)))

    schedule.run_all(10, 'base-tasks')
    startup_handlers()

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
