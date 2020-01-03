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
from node_tools.logger_config import setup_logging
from node_tools.node_funcs import get_moon_data
from node_tools.node_funcs import run_moon_cmd

try:
    from datetime import timezone
    utc = timezone.utc
except ImportError:
    from daemon.timezone import UTC
    utc = UTC()

if sys.hexversion >= 0x3020000:
    from configparser import ConfigParser as SafeConfigParser
else:
    from configparser import SafeConfigParser


logger = logging.getLogger(__name__)

max_age = NODE_SETTINGS['max_cache_age']
moons = NODE_SETTINGS['moon_list']  # list of fpn moons to orbiit
timestamp = datetime.datetime.now(utc)  # use local time for console


# use with the following to cancel a failed job function
#   @catch_exceptions(cancel_on_failure=True)
def catch_exceptions(cancel_on_failure=False):
    def catch_exceptions_decorator(job_func):
        @functools.wraps(job_func)
        def wrapper(*args, **kwargs):
            try:
                return job_func(*args, **kwargs)
            except:
                import traceback
                logger.error(traceback.format_exc())
                if cancel_on_failure:
                    return schedule.CancelJob
        return wrapper
    return catch_exceptions_decorator


def show_scheduled_jobs():
    """
    Show job info for all currently scheduled jobs.  Normally run
    once at startup.  Also shows tags for base jobs.
    """
    for job in schedule.jobs:
        logger.debug('JOBS: {}'.format(job))
        if 'base' in str(job.tags):
            logger.debug('TAGS: {}'.format(job.tags))


def config_from_ini():
    config = SafeConfigParser()
    candidates = ['/etc/fpnd.ini',
                  '/etc/fpnd/fpnd.ini',
                  '/usr/lib/fpnd/fpnd.ini',
                  'member_settings.ini',
                  ]
    found = config.read(candidates)

    if not found:
        message = 'No usable cfg found, files in /tmp/ dir.'
        return False, message

    for tgt_ini in found:
        if 'fpnd' in tgt_ini:
            message = 'Found system settings...'
            return config, message
        if 'member' in tgt_ini and config.has_option('Options', 'prefix'):
            message = 'Found local settings...'
            config['Paths']['log_path'] = ''
            config['Paths']['pid_path'] = ''
            config['Options']['prefix'] = 'local_'
            return config, message


def do_setup():
    my_conf, msg = config_from_ini()
    if my_conf:
        debug = my_conf.getboolean('Options', 'debug')
        home = my_conf['Paths']['home_dir']
        if 'system' not in msg:
            prefix = my_conf['Options']['prefix']
        else:
            prefix = ''
        pid_path = my_conf['Paths']['pid_path']
        log_path = my_conf['Paths']['log_path']
        pid_file = my_conf['Options']['pid_name']
        log_file = my_conf['Options']['log_name']
        pid = os.path.join(pid_path, prefix, pid_file)
        log = os.path.join(log_path, prefix, log_file)

    else:
        debug = False
        home = False
        pid = '/tmp/fpnd.pid'
        log = '/tmp/fpnd.log'
    return home, pid, log, debug, msg


def setup_scheduling(max_age):
    """Initial setup for scheduled jobs"""
    sleep_time = max_age / 6

    baseUpdateJob = schedule.every(sleep_time).seconds
    baseUpdateJob.do(update_runner).tag('base-tasks', 'get-updates')

    show_scheduled_jobs()
    logger.debug('Leaving setup_scheduling: {}'.format(baseUpdateJob))


def do_scheduling():
    schedule.run_all(10, 'base-tasks')
    # time.sleep(3)

    for moon in moons:
        res = run_moon_cmd(moon, action='orbit')

    moon_metadata = get_moon_data()
    logger.debug('Moon data size: {}'.format(len(moon_metadata)))

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
    logger = logging.getLogger("fpnd")
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
