#!/usr/bin/env python3

import time
import datetime
import logging
import functools
import schedule

from node_tools.sched_funcs import catch_exceptions
from node_tools.sched_funcs import run_until_success
from node_tools.sched_funcs import show_job_tags


logger = logging.getLogger(__name__)


@show_job_tags()
@run_until_success()
def good_task():
    print('I am good')
    return 0


@run_until_success()
def good_returns():
    print("I'm good too")
    return True, 'Success', 0


@run_until_success()
def bad_returns():
    print("I'm not so good")
    return False, 'blah', 1


@show_job_tags()
@catch_exceptions(cancel_on_failure=True)
def bad_task():
    print('I am bad')
    raise Exception('Something went wrong!')


# schedule.every(3).seconds.do(good_task).tag('1')
schedule.every(5).seconds.do(good_task).tag('good')
schedule.every(8).seconds.do(bad_task).tag('bad')
schedule.every(3).seconds.do(good_returns)
schedule.every(5).seconds.do(bad_returns)

while True:
    schedule.run_pending()
    time.sleep(1)
