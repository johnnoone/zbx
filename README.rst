===
ZBX
===

.. image:: https://badge.fury.io/py/zbx.png
    :target: http://badge.fury.io/py/zbx

.. image:: https://travis-ci.org/johnnoone/zbx.png?branch=master
        :target: https://travis-ci.org/johnnoone/zbx

.. image:: https://pypip.in/d/zbx/badge.png
        :target: https://pypi.python.org/pypi/zbx


This library let you to describe Zabbix configuration in pure Python.
This configuration can then be dumped in xml and imported into zabbix.

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


zbx.config
~~~~~~~~~~

.. code-block:: console

    from zb.api import *
    from zb.config.items.aggregate import AvgItem

    configuration = Config()
    template = configuration.templates.new('My template')
    classic_item = template.items.new('my item', key='my.item', applications=['my application'])
    average_item = template.items.add(AvgItem('my item',
                                              groups=['first group', 'second group'],
                                              key='my.item',
                                              applications=['my application']))
