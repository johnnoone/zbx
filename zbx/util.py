from functools import wraps
import importlib


def memoize(func):
    """Memoize single argument functions"""

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
            raise ValueError('class_path must be absolute')
    else:
        if '.' not in path:
            path = '{}.{}'.format(start_package, path)
        elif path.startswith('.'):
            path = '{}{}'.format(start_package, path)

    # if it fails, it must be an attr loading
    path, _, attr = path.rpartition('.')

    mod = importlib.import_module(path)
    return getattr(mod, attr)
