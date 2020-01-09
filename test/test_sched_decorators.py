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
        self.bin_dir = os.path.join(os.getcwd(), 'bin')
        schedule.clear()

    def test_run_tag(self):
        with mock_datetime(2010, 1, 6, 12, 15):
            mock_job = make_mock_job()
            assert schedule.last_run() is None
            job1 = every().hour.do(mock_job(name='job1')).tag('tag1')
            job2 = every().hour.do(mock_job(name='job2')).tag('tag1', 'tag2')
            job3 = every().hour.do(mock_job(name='job3')).tag('tag3', 'tag3',
                                                              'tag3', 'tag2')
            assert len(schedule.jobs) == 3
            schedule.run_all(0, 'tag1')
            assert 'tag1' in str(job1.tags)
            assert 'tag1' not in str(job3.tags)
            assert 'tag1' in str(job2.tags)
            assert job1.last_run.minute == 15
            assert job2.last_run.hour == 12
            assert job3.last_run is None

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

    def test_clear_by_tag(self):
        every().second.do(make_mock_job(name='job1')).tag('tag1')
        every().second.do(make_mock_job(name='job2')).tag('tag1', 'tag2')
        every().second.do(make_mock_job(name='job3')).tag('tag3', 'tag3',
                                                          'tag3', 'tag2')
        assert len(schedule.jobs) == 3
        schedule.run_all()
        assert len(schedule.jobs) == 3
        schedule.clear('tag3')
        assert len(schedule.jobs) == 2
        schedule.clear('tag1')
        assert len(schedule.jobs) == 0
        every().second.do(make_mock_job(name='job1'))
        every().second.do(make_mock_job(name='job2'))
        every().second.do(make_mock_job(name='job3'))
        schedule.clear()
        assert len(schedule.jobs) == 0

    @pytest.mark.xfail(raises=ValueError)
    def test_run_net_cmd_false(self):
        cmd = ['/bin/false']
        state, res, ret = run_net_cmd(cmd)
        self.assertFalse(state)
        self.assertEqual(res, b'')
        # print(ret)

    @pytest.mark.xfail(raises=ValueError)
    def test_run_net_cmd_not_found(self):
        cmd = ['/bin/tuna']
        state, res, ret = run_net_cmd(cmd)
        self.assertFalse(state)
        self.assertRaises(FileNotFoundError)
        # print(ret)

    @pytest.mark.xfail(raises=ValueError)
    def test_run_net_cmd_full(self):
        cmd, down0, up1, down1 = get_net_cmds(self.bin_dir)

        state, res, ret = run_net_cmd(cmd)
        self.assertFalse(state)
        self.assertEqual(res, b'')
        self.assertEqual(ret, 1)
