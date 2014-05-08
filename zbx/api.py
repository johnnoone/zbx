"""
    zbx.api
    ~~~~~~~
"""

__all__ = ['Api', 'RPCException', 'cast',
           'authenticate', 'request', 'configure']

import json
import logging

from six import PY3

if PY3:
    import urllib
    _request_context = urllib.urlopen
else:
    import contextlib
    import functools
    import urllib2 as urllib

    @functools.wraps(urllib.urlopen)
    def _request_context(request):
        return contextlib.closing(urllib.urlopen(request))

from zbx.exceptions import RPCException

logger = logging.getLogger(__name__)


# list of methods which does not require authentication
WITHOUT_AUTH = set([
    'user.login',
    'user.checkAuthentication',
    'apiinfo.version',
])


def cast(data):
    """ensure int are int..."""
    if isinstance(data, dict):
        return data.__class__((key, cast(value)) for key, value in data.items())  # NOQA
    if isinstance(data, (list, set, tuple)):
        return data.__class__(cast(value) for value in data)
    try:
        if data.isdigit():
            return int(data)
    except AttributeError:
        pass
    return data


class Api(object):
    def __init__(self, user, password, url):
        self.user = user
        self.password = password
        self.url = url
        self.auth_token = None

    def request(self, method, params=None, auth_token=None, **api_args):
        params = params or []

        if not method in WITHOUT_AUTH:
            auth_token = auth_token or self.authenticate(**api_args)

        return cast(self._caller(method, params, auth_token, **api_args))

    def authenticate(self, reset=False, **api_args):
        """
        Authenticates to the api.

        """

        if not reset and self.auth_token:
            return self.auth_token
        try:
            method = 'user.login'
            params = {'user': self.user, 'password': self.password}
            result = self._caller(method, params,  **api_args)
            self.auth_token = result
        except:
            pass
        return result

    def _caller(self, method, params, auth_token=None, **api_args):
        data = {
            'jsonrpc': '2.0',
            'id': 1,
            'method': method,
            'params': params or [],
        }
        if auth_token:
            data['auth'] = auth_token

        query = json.dumps(data)

        request = urllib.Request(self.url, query, {
            'Content-Type': 'application/json'
        })

        logger.debug('Zabbix API --> %s %s', method,
                     json.dumps(params, sort_keys=True))

        with _request_context(request) as contents:

            if not contents:
                logger.debug('Zabbix API <-- no result')
                return None

            data = json.load(contents)

            if 'error' in data:
                error = data['error']
                logger.debug('Zabbix API <-- error %s',
                             json.dumps(error, sort_keys=True))
                raise RPCException(**data['error'])

            result = data.get('result', None)
            logger.debug('Zabbix API <-- result %s',
                         json.dumps(result, sort_keys=True))
            return result


_instance = Api(None, None, None)

authenticate = _instance.authenticate

request = _instance.request


def configure(**attrs):
    for attr, value in attrs.items():
        if attr in ('url', 'user', 'password', 'auth_token'):
            setattr(_instance, attr, value)
