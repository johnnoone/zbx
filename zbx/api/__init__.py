"""
    zbx.api
    ~~~~~~~

    Access to zabbix api as described here:
    https://www.zabbix.com/documentation/2.2/manual/api

"""

__all__ = ['Api', 'RPCException', 'cast',
           'authenticate', 'request', 'configure']

import json
import logging

from six import PY3
from six.moves.urllib.request import urlopen, Request

if PY3:
    _request_context = urlopen
else:
    import contextlib
    import functools

    @functools.wraps(urlopen)
    def _request_context(request):
        return contextlib.closing(urlopen(request))

from zbx.exceptions import RPCException

logger = logging.getLogger(__name__)


#: list of methods which does not require authentication
WITHOUT_AUTH = set([
    'user.login',
    'user.checkAuthentication',
    'apiinfo.version',
])


def cast(data):
    """Ensure that int are int etc..."""

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
    """
    Main api object
    """

    def __init__(self, user, password, url, auth_token=None):
        self.user = user
        self.password = password
        self.url = url
        self.auth_token = None

    def request(self, method, params=None, auth_token=None):
        """
        Handle a request to the api.

        It will authenticate automatically if auth_token was not provided
        """

        params = params or []

        if not method in WITHOUT_AUTH:
            auth_token = auth_token or self.authenticate()

        return cast(self._caller(method, params, auth_token))

    def authenticate(self, reset=False):
        """
        Authenticates to the api.

        """

        if not reset and self.auth_token:
            return self.auth_token
        try:
            method = 'user.login'
            params = {'user': self.user, 'password': self.password}
            result = self._caller(method, params)
            self.auth_token = result
        except RPCException:
            pass
        return result

    def _caller(self, method, params, auth_token=None):
        data = {
            'jsonrpc': '2.0',
            'id': 1,
            'method': method,
            'params': params or [],
        }
        if auth_token:
            data['auth'] = auth_token

        query = json.dumps(data)

        request = Request(self.url, query, {
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

#: authenticate with the global api instance
authenticate = _instance.authenticate

#: request with the global api instance
request = _instance.request


def configure(**attrs):
    """
    Configure the global api instance.

    """
    for attr, value in attrs.items():
        if attr in ('url', 'user', 'password', 'auth_token'):
            setattr(_instance, attr, value)
