# coding: utf-8

import time
import logging


def setup_logging(debug, filename, fmt=None):
    """
    Can be imported by ``<my_package>`` to create a log file for logging
    ``<my_package>`` class output.  In this example we use a ``debug``
    flag set in ``<my_package>`` to change the Log Level and ``filename``
    to set log path.  We also use UTC time and force the name in ``datefmt``.
    """
    if debug:
        log_level = logging.getLevelName('DEBUG')
    else:
        log_level = logging.getLevelName('INFO')

    # process format:
    #   '%(asctime)s %(name)s[%(process)d] %(levelname)s - %(message)s'
    # alt format
    #   '%(asctime)s %(levelname)s %(filename)s(%(lineno)d) %(message)s'
    # long format
    #   '%(asctime)s %(name)s.%(funcName)s +%(lineno)s: %(levelname)s [%(process)d] %(message)s'
    format = '%(asctime)s %(name)s.%(funcName)s +%(lineno)s: %(levelname)s [%(process)d] %(message)s'

    if not fmt:
        fmt = format

    logging.basicConfig(level=log_level,
                        format=fmt,
                        datefmt='%Y-%m-%d %H:%M:%S UTC',
                        filename=filename)

    # BUG: This does not print the TZ name because logging module uses
    #      time instead of tz-aware datetime objects (so we force the
    #      correct name in datefmt above).
    logging.Formatter.converter = time.gmtime

    # To also log parent info, try something like this
    # global logger
    # logger = logging.getLogger("my_package")
