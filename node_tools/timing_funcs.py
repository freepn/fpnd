# coding: utf-8

"""Timing helper functions (some borrowed from NTPsec utils.py)."""

import time
import logging


logger = logging.getLogger(__name__)


def monoclock():
    "Try to get a monotonic clock value from python3"
    try:
        # Available in Python 3.3 and up.
        return time.monotonic()
    except AttributeError:
        return time.time()


class Cache:
    "Simple time-based expiring cache"

    def __init__(self, defaultTimeout=300):  # 5 min default TTL
        self.defaultTimeout = int(defaultTimeout)
        self._cache = {}

    def get(self, key):
        if key in self._cache:
            value, settime, ttl = self._cache[key]
            if settime >= monoclock() - ttl:
                return value
            else:  # key expired, delete it
                del self._cache[key]
                return None
        else:
            return None

    def set(self, key, value, customTTL=None):
        ttl = self.defaultTimeout if customTTL is None else int(customTTL)
        self._cache[key] = (value, monoclock(), ttl)
