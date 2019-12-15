#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Target:   Python 3.6

import sys
import time
import datetime
import logging

from daemon import Daemon
from daemon.parent_logger import setup_logging

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
timestamp = datetime.datetime.now()  # use local time for console


def config_from_ini():
    config = SafeConfigParser()
    candidates = ['/etc/fpnd/settings.ini',
                  'member_settings.ini',
                  ]
    found = config.read(candidates)

    if not found:
        message = 'No usable cfg found, files in /tmp/ dir.'
        return None, message

    for tgt_ini in found:
        if 'fpnd' in tgt_ini and config.has_option('Options', 'prefix'):
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
    if my_conf is not None:
        debug = my_conf.getboolean('Options', 'debug')
        prefix = my_conf['Options']['prefix']
        pid_file = my_conf['Paths']['pid_path'] + prefix + my_conf['Options']['pid_name']
        log_file = my_conf['Paths']['log_path'] + prefix + my_conf['Options']['log_name']
    else:
        debug = False
        pid_file = '/tmp/fpnd.pid'
        log_file = '/tmp/fpnd.log'
    return pid_file, log_file, debug, msg


# Inherit from Daemon class
class fpnDaemon(Daemon):
    # implement run method
    def run(self):

        # Wait
        time.sleep(30)


if __name__ == "__main__":
    pid_file, log_file, debug, msg = do_setup()
    setup_logging(debug, log_file)
    logger = logging.getLogger("fpnd")

    if len(sys.argv) == 2:
        arg = sys.argv[1]
        if arg in ('start'):
            logger.info(msg)
        if arg in ('start', 'stop', 'restart'):
            d = fpnDaemon(pid_file, verbose=0)
            getattr(d, arg)()
    else:
        print("usage: %s start|stop|restart" % sys.argv[0])
        sys.exit(2)
