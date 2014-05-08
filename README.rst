===
ZBX
===

.. image:: https://badge.fury.io/py/zbx.png
    :target: http://badge.fury.io/py/zbx

.. image:: https://travis-ci.org/johnnoone/zbx.png?branch=master
        :target: https://travis-ci.org/johnnoone/zbx

.. image:: https://pypip.in/d/zbx/badge.png
        :target: https://pypi.python.org/pypi/zbx


Zabbix utilitary tools

* Free software: BSD license
* Documentation: http://zbx.rtfd.org.

Features
--------

zbx.api
~~~~~~~

.. code-block:: console

    from zb.api import *

    configure(user=YOUR_USER, password=YOUR_PASSWORD, url=YOUR_URL)
    reponse = request('history.get', {
        'output': 'extend',
        'history': 0,
        'itemids': '23296',
        'sortfield': 'clock',
        'sortorder': 'DESC',
        'limit': 10
    })
