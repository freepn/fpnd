"""Unit tests for sched_funcs.py decorators"""

import os
import sys
import datetime
import logging
import functools
import unittest

import mock
import pytest
import schedule
from schedule import every

from node_tools.network_funcs import get_net_cmds
from node_tools.network_funcs import run_net_cmd
from node_tools.sched_funcs import catch_exceptions
from node_tools.sched_funcs import run_until_success
from node_tools.sched_funcs import show_job_tags

try:
    from datetime import timezone
    utc = timezone.utc
except ImportError:
    from schedule.timezone import UTC
    utc = UTC()


def make_mock_job(name=None):
    job = mock.Mock()
    job.__name__ = name or 'job'
    return job


class mock_datetime(object):
    """
    Monkey-patch datetime for predictable results
    """
    def __init__(self, year, month, day, hour, minute, second=0):
        self.year = year
        self.month = month
        self.day = day
        self.hour = hour
        self.minute = minute
        self.second = second

    def __enter__(self):
        class MockDate(datetime.datetime):
            @classmethod
            def today(cls):
                return cls(self.year, self.month, self.day)

            @classmethod
            def now(cls, tz=None):
                return cls(self.year, self.month, self.day,
                           self.hour, self.minute, self.second).replace(tzinfo=tz)

        self.original_datetime = datetime.datetime
        datetime.datetime = MockDate

    def __exit__(self, *args, **kwargs):
        datetime.datetime = self.original_datetime


class SchedulerTests(unittest.TestCase):
    def setUp(self):
        self.bin_dir = os.path.join(os.getcwd(), 'test/fpnd/')
        schedule.clear()

    def test_job_info(self):
        with mock_datetime(2010, 1, 6, 14, 16):
            mock_job = make_mock_job(name='info_job')
            info_job = every().minute.do(mock_job, 1, 7, 'three')
            schedule.run_all()
            assert len(schedule.jobs) == 1
            assert schedule.jobs[0] == info_job
            assert repr(info_job)
            assert info_job.job_name is not None
            s = info_job.info
            assert 'info_job' in s
            assert 'three' in s
            assert '2010' in s
            assert '14:16' in s

    def test_cancel_job(self):
        @show_job_tags
        def stop_job():
            return schedule.CancelJob
        mock_job = make_mock_job()

        every().second.do(stop_job)
        mj = every().second.do(mock_job)
        assert len(schedule.jobs) == 2

        schedule.run_all()
        assert len(schedule.jobs) == 1
        assert schedule.jobs[0] == mj

        schedule.cancel_job('Not a job')
        assert len(schedule.jobs) == 1
        schedule.default_scheduler.cancel_job('Not a job')
        assert len(schedule.jobs) == 1

        schedule.cancel_job(mj)
        assert len(schedule.jobs) == 0

    def test_run_net_cmd_sched_up(self):
        cmd_up0 = get_net_cmds(self.bin_dir, 'fpn0', True)
        cmd_up1 = get_net_cmds(self.bin_dir, 'fpn1', True)

        every().second.do(run_net_cmd, cmd_up0).tag('net-change')
        every().second.do(run_net_cmd, cmd_up1).tag('net-change')

        self.assertEqual(len(schedule.jobs), 2)

        schedule.run_all(0, 'net-change')
        self.assertEqual(len(schedule.jobs), 0)

    def test_run_net_cmd_sched_down(self):
        cmd_down0 = get_net_cmds(self.bin_dir, 'fpn0', False)
        cmd_down1 = get_net_cmds(self.bin_dir, 'fpn1', False)

        every().second.do(run_net_cmd, cmd_down0).tag('net-change')
        every().second.do(run_net_cmd, cmd_down1).tag('net-change')
        self.assertEqual(len(schedule.jobs), 2)

        schedule.run_all(0, 'net-change')
        self.assertEqual(len(schedule.jobs), 2)

        schedule.run_all(0, 'net-change')
        schedule.run_all(0, 'net-change')
        self.assertEqual(len(schedule.jobs), 0)


class NetCmdTests(unittest.TestCase):
    """
    Slightly better tests (than NetCmdTest) using schedule.
    """
    def setUp(self):
        self.bin_dir = os.path.join(os.getcwd(), 'test/fpnd/')
        schedule.clear()

    def test_run_net_cmd_false(self):
        mock_job = make_mock_job()
        tj = every().second.do(mock_job)

        cmd = ['/bin/false']
        state, res, ret = run_net_cmd(cmd)
        self.assertFalse(state)
        self.assertEqual(res, b'')

    def test_run_net_cmd_not_found(self):
        mock_job = make_mock_job()
        tj = every().second.do(mock_job)

        cmd = ['/bin/tuna']
        state, res, ret = run_net_cmd(cmd)
        self.assertFalse(state)
        self.assertRaises(FileNotFoundError)

    def test_run_net_cmd_up0(self):
        # expected command result is 'Success' so the return
        # result is actually <schedule.CancelJob>
        mock_job = make_mock_job()
        cmd = get_net_cmds(self.bin_dir, 'fpn0', True)
        tj = every().second.do(mock_job)

        result = run_net_cmd(cmd)
        self.assertIsInstance(result, type)
        self.assertIn('CancelJob', str(result))

    def test_run_net_cmd_down0(self):
        # expected command result is 'Fail' so the return
        # result is the output of run_net_cmd()
        mock_job = make_mock_job()
        cmd = get_net_cmds(self.bin_dir, 'fpn0', False)
        tj = every().second.do(mock_job)

        state, res, ret = run_net_cmd(cmd)
        self.assertFalse(state)
        self.assertEqual(res, b'')
        self.assertEqual(ret, 1)
