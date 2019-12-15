# -*- coding: utf-8 -*-
"""Exceptions for FPN nodes."""

__all__ = (
    'MemberNodeError',
    'MemberNodeNoDataError',)


class MemberNodeError(Exception):
    """Base class for general FPN MemberNode errors."""


class MemberNodeNoDataError(MemberNodeError):
    """No data error when (external) API data is not available."""

