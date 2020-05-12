#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Target:   Python 3.6

import os
import sys
import time
import datetime
import logging
import logging.handlers

from daemon import Daemon

from node_tools.helper_funcs import NODE_SETTINGS
from node_tools.network_funcs import do_net_check
from node_tools.state_data import net_health


logger = logging.getLogger(__name__)

# set log level and handler/formatter
logger.setLevel(logging.DEBUG)
logging.getLogger('node_tools.network_funcs').level = logging.DEBUG

handler = logging.handlers.SysLogHandler(address='/dev/log', facility='daemon')
formatter = logging.Formatter('%(module)s.%(funcName)s +%(lineno)s: %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

pid_file = '/tmp/health_check.pid'
std_out = '/tmp/health_check.log'
std_err = '/tmp/health_check_err.log'

# needs a new param here
max_age = NODE_SETTINGS['max_cache_age']


def show_scheduled_jobs():
    """
    Show job info for all currently scheduled jobs.  Normally run
    once at startup.  Also shows tags for base jobs.
    """
    for job in schedule.jobs:
        logger.debug('JOBS: {}'.format(job))
        if 'health' in str(job.tags):
            logger.debug('TAGS: {}'.format(job.tags))


def setup_scheduling(max_age):
    """Initial setup for scheduled jobs"""
    sleep_time = max_age

    baseCheckJob = schedule.every(sleep_time).seconds
    baseCheckJob.do(do_net_check).tag('health_check', 'geoip')

    show_scheduled_jobs()
    logger.debug('Leaving setup_scheduling: {}'.format(baseCheckob))


def do_scheduling():
    schedule.run_all(1, 'health_check')

    while True:
        schedule.run_pending()
        time.sleep(1)


# Inherit from Daemon class
class subDaemon(Daemon):
    # implement run method
    def run(self):
        do_scheduling()


if __name__ == "__main__":

    daemon = subDaemon(pid_file, stdout=std_out, stderr=std_err, verbose=1)
    if len(sys.argv) == 2:
        if 'start' == sys.argv[1]:
            logger.info('Starting')
            daemon.start()
        elif 'stop' == sys.argv[1]:
            logger.info('Stopping')
            daemon.stop()
        elif 'restart' == sys.argv[1]:
            logger.info('Restarting')
            daemon.restart()
        elif 'status' == sys.argv[1]:
            res = daemon.status()
            logger.info('Status is {}'.format(res))
        else:
            print("Unknown command")
            sys.exit(2)
        sys.exit(0)
    else:
        print("usage: {} start|stop|restart|status".format(sys.argv[0]))
        sys.exit(2)
