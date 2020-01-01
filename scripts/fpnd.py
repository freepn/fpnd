#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Target:   Python 3.6

import os
import sys
import time
import datetime
import logging
import schedule

from daemon import Daemon
from daemon.parent_logger import setup_logging

from node_tools.data_funcs import update_runner
from node_tools.helper_funcs import NODE_SETTINGS
from node_tools.network_funcs import get_net_cmds
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
    sleep_time = max_age / 2
    stateJob = schedule.every(sleep_time).seconds
    stateJob.do(update_runner)
    logger.debug('Leaving setup_scheduling: {}'.format(stateJob))


def do_scheduling():
    logger.debug('Entering do_scheduling')
    schedule.run_all(10)
    time.sleep(5)

    for moon in moons:
        res = run_moon_cmd(moon, action='orbit')

    moon_metadata = get_moon_data()
    logger.debug('Moon data size: {}'.format(len(moon_metadata)))
    logger.debug('Moon data type is: {}'.format(type(moon_metadata)))

    logger.debug('Entering schedule.run_pending loop')
    while True:
        schedule.run_pending()
        time.sleep(1)


# Inherit from Daemon class
class fpnDaemon(Daemon):
    # implement run method
    def run(self):
        up0, down0, up1, down1 = get_net_cmds(self.home_dir)
        # logger.debug('up0 is: {}'.format(up0))
        do_scheduling()


if __name__ == "__main__":
    home, pid_file, log_file, debug, msg = do_setup()
    setup_logging(debug, log_file)
    logger = logging.getLogger("fpnd")
    setup_scheduling(max_age)
    if not home:
        home = '.'

    logger.debug('Leaving main, max_age is: {}'.format(max_age))

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
