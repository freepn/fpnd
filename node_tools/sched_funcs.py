# coding: utf-8

"""Scheduler helper/decorator functions."""

import logging
import functools
import schedule


logger = logging.getLogger(__name__)


def check_return_status(obj):
    # ordering is important here (silly ad-hoc function)
    if obj is False:
        return False
    # we want to accept '0' as Success, otherwise 'not' is False
    if isinstance(obj, (bool, int)):
        if obj == 0 or obj is True:
            return True
        elif obj != 0:
            return False
    if not obj:
        return False
    # now handle a (small) list of everything else
    good_list = ['OK', 'Success', 'UP', 'good']
    if isinstance(obj, str):
        for thing in good_list:
            if thing in obj:
                return True
    elif isinstance(obj, (list, tuple)):
        for item in obj:
            for thing in good_list:
                if item is True:
                    return True
                elif isinstance(item, str):
                    if thing in item:
                        return True
    else:
        return False


def catch_exceptions(cancel_on_failure=False):
    """
    decorator for running a suspect job with cancel_on_failure option
    """
    def catch_exceptions_decorator(job_func):
        @functools.wraps(job_func)
        def wrapper(*args, **kwargs):
            try:
                return job_func(*args, **kwargs)
            except:
                import traceback
                logger.debug(traceback.format_exc())
                if cancel_on_failure:
                    return schedule.CancelJob
        return wrapper
    return catch_exceptions_decorator


def run_until_success(max_retry=2):
    """
    decorator for running a single job until success with retry limit
    * will unschedule itself on success
    * will reschedule on failure until max retry is exceeded
    :requirements:
    * the job function must return something to indicate success/failure
      or raise an exception on non-success
    :param max_retry: max number of times to reschedule the job on failure,
                      balance this with the job interval for best results
    """
    def run_until_success_decorator(job_func):
        @functools.wraps(job_func)
        def wrapper(*args, **kwargs):
            current = min(job for job in schedule.jobs)
            num_try = int(max((tag for tag in current.tags if tag.isdigit()), default=0))
            tries_left = max_retry - num_try
            next_try = num_try + 1

            try:
                result = job_func(*args, **kwargs)

            except Exception as exc:
                # import traceback
                result = None
                logger.error('JOB: {} failed on try number: {}'.format(current, num_try))
                logger.error('JOB: exception is: {}'.format(exc))
                # logger.error(traceback.format_exc())

            finally:
                if check_return_status(result):
                    logger.debug('JOB: {} claims success: {}'.format(current, result))
                    return schedule.CancelJob
                elif tries_left == 0:
                    logger.debug('JOB: {} failed with result: {}'.format(current, result))
                    return schedule.CancelJob
                else:
                    logger.debug('JOB: {} failed with {} try(s) left, trying again'.format(current, tries_left))
                    current.tags.update(str(next_try))
                    return result

        return wrapper
    return run_until_success_decorator


def show_job_tags():
    """
    decorator to show job name and tags for current job
    """
    def show_job_tags_decorator(job_func):
        @functools.wraps(job_func)
        def wrapper(*args, **kwargs):
            current_job = min(job for job in schedule.jobs)
            job_tags = current_job.tags
            logger.info('JOB: {}'.format(current_job))
            logger.info('TAGS: {}'.format(job_tags))
            return job_func(*args, **kwargs)
        return wrapper
    return show_job_tags_decorator
