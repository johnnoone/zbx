import struct
try:
    import simplejson as json
except ImportError:
    import json


class Metric(object):
    def __init__(self, key, value, host=None, clock=None):
        self.key = key
        self.value = value
        self.host = host
        self.clock = clock


def send(metrics):
    """docstring for send

    http://zabbix.org/wiki/Docs/protocols/zabbix_sender/2.0
    """

    now = time.time.now()

    def format(metric):
        host = metric.host
        if host in (None, '-'):
            host = 'localhost'

        return {
            'host': host,
            'key': metric.key,
            'value': str(metric.value or '-'),
            'clock': int(metric.clock or now),
        }

    contents = json.dumps({
        'request': 'sender data',
        'data': [format(metric) for metric in metrics],
        'clock': int(now)
    })

    data_len = struct.pack('<Q', len(contents))
    packet = 'ZBXD\1{}{}'.format(data_len, contents)

    # TODO send and return data
    zabbix = socket.socket()
    zabbix.connect((zabbix_host, zabbix_port))
    zabbix.sendall(packet)
    resp_hdr = _recv_all(zabbix, 13)
    if not resp_hdr.startswith('ZBXD\1') or len(resp_hdr) != 13:
        logger.error('Wrong zabbix response')
        return False
    resp_body_len = struct.unpack('<Q', resp_hdr[5:])[0]
    resp_body = zabbix.recv(resp_body_len)
    zabbix.close()

    resp = json.loads(resp_body)
    if resp.get('response') != 'success':
        raise Exception(resp.get('info', 'Error from zabbix server'))
    return resp.get('info')
