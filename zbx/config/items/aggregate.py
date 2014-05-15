"""

    zbx.config.item.aggregate
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    see https://www.zabbix.com/documentation/2.0/manual/config/items/itemtypes/aggregate  # NOQA

"""

__all__ = ['AggregateItem', 'AvgItem', 'SumItem']

import logging

from . import Item
from ..fields import Field
from zbx.util import escape
from zbx.util import format_timeperiod


class AggregateKeyField(Field):
    def __get__(self, obj, type=None):
        groups = obj.groups or ['<not set>']
        if len(groups) > 1:
            groups = escape(groups)
        elif len(groups) == 1:
            for e in groups:
                groups = escape(e)
                break

        tpl = '{groupfunc}[{groups},{key},{itemfunc},{timeperiod}]'
        timeperiod = format_timeperiod(obj.timeperiod or 0)
        groupfunc = obj.groupfunc
        itemfunc = obj.itemfunc
        key = obj._values[self.key]

        return tpl.format(groupfunc=groupfunc,
                          groups=groups,
                          key=escape(key),
                          itemfunc=itemfunc,
                          timeperiod=timeperiod)


class AggregateItem(Item):
    """
    AggregateItem model
    """

    key = AggregateKeyField()

    def __init__(self, name, groups, groupfunc, itemfunc, timeperiod, **fields):  # NOQA
        logging.debug('__init__ %s', self)

        self.groupfunc = groupfunc
        self.itemfunc = itemfunc
        self.timeperiod = timeperiod
        self.groups = set()

        if isinstance(groups, (list, tuple, set)):
            self.groups.update(groups)
        else:
            self.groups.add(groups)

        fields.setdefault('type', 8)
        fields.setdefault('data_type', 'decimal')

        super(AggregateItem, self).__init__(name, **fields)


def AvgItem(name, groups, **fields):
    """
    Helper for average items.
    """
    if not name.endswith(' (avg)'):
        name += ' (avg)'

    fields.setdefault('groupfunc', 'grpavg')
    fields.setdefault('itemfunc', 'avg')
    fields.setdefault('timeperiod', '1m')

    return AggregateItem(name, groups, **fields)


def SumItem(name, groups, **fields):
    """
    Helper for sum items.
    """
    if not name.endswith(' (sum)'):
        name += ' (sum)'

    fields.setdefault('groupfunc', 'grpavg')
    fields.setdefault('itemfunc', 'avg')
    fields.setdefault('timeperiod', '1m')
    return AggregateItem(name, groups, **fields)
