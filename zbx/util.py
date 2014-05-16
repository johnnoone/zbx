"""

    zbx.util
    ~~~~~~~~

"""

__all__ = ['copied', 'escape', 'format_timeperiod', 'parse_timeperiod',
           'load', 'memoize']

from copy import deepcopy
from datetime import timedelta
from functools import wraps
import importlib
import re
try:
    import simple_json as json
except ImportError:
    import json

from six import integer_types
from six import string_types


def escape(value):
    """escape value for zabbix"""
    return json.dumps(value, separators=',:')


TIMEPERIOD_PATTERN = re.compile(r'^(?P<time>\d+)(?P<resolution>[smhdw])?$')


def format_timeperiod(value):
    """
    Format value to a suffixed time unit.

    For example, it will convert `str('86400')` to `str('1d')`.

    The available suffixes are:

    :s: seconds
    :m: minutes
    :h: hours
    :d: days
    :w: weeks

    """

    time, resolution = parse_timeperiod(value)

    for current_resolution, next_resolution, div in (
        ('s', 'm', 60),
        ('m', 'h', 60),
        ('h', 'd', 24),
        ('d', 'w', 7),
    ):

        # try to compress as possible:
        if resolution == current_resolution and not time % div:
            time /= div
            resolution = next_resolution

    return '{}{}'.format(time, resolution)


def parse_timeperiod(value):
    if isinstance(value, timedelta):
        time = value.total_seconds()
        resolution = 's'
    elif isinstance(value, string_types):
        try:
            time, resolution = TIMEPERIOD_PATTERN.search(value).groups()
            time = int(time)
        except:
            raise ValueError('{value} cannot be parsed as a timeperiod'.format(value))  # NOQA
    elif isinstance(value, integer_types):
            time, resolution = value, 's'
    else:
        raise ValueError('{!r} cannot be casted as a timeperiod'.format(value))

    return time, resolution or 's'


def memoize(func):
    """Memoize arguments functions"""

    memoized = {}

    @wraps(func)
    def wrapper(*args):
        if args in memoized:
            return memoized[args]
        value = memoized[args] = func(*args)
        return value

    wrapper.memoized = memoized
    return wrapper


@memoize
def load(path, start_package=None):
    """Load by absolute path"""

    if not start_package:
        if '.' not in path or path.startswith('.'):
            raise ValueError('class_path must be absolute', path)
    else:
        if '.' not in path:
            path = '{}.{}'.format(start_package, path)
        elif path.startswith('.'):
            path = '{}{}'.format(start_package, path)

    # if it fails, it must be an attr loading
    path, _, attr = path.rpartition('.')

    mod = importlib.import_module(path)
    return getattr(mod, attr)


def copied(func):
    """
    Decorator that cache and returns copy of results.
    """

    func = memoize(func)

    @wraps(func)
    def wrapper(*args):
        return deepcopy(func(*args))

    return wrapper
