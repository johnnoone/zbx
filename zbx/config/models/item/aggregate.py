"""

    zbx.config.models.item.aggregate
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    https://www.zabbix.com/documentation/2.0/manual/config/items/itemtypes/aggregate

"""

__all__ = ['AggregateItem', 'AvgItem', 'SumItem']

import logging

from . import Item
from ..fields import Field


class AggregatedKey(object):
    def __init__(self, key, groups, groupfunc, itemfunc, timeperiod=None):
        self.key = key

        if isinstance(groups, (list, tuple, set)):
            self.groups.update(groups)
        else:
            self.groups.add(groups)

        self.groupfunc = groupfunc
        self.itemfunc = itemfunc
        self._period = Timeperiod()
        self.period = timeperiod

    @property
    def groups(self):
        if not hasattr(self, '_groups'):
            self._groups = ComaDelimitedArgument()
        return self._groups

    @property
    def period(self):
        return self._period

    @period.setter
    def period(self, value):
        self._period.update(value)

    def __str__(self):
        return "{groupfunc}[{groups!s}, ze {key!r}, {itemfunc}, {timeperiod}]".format(
            key=self.key,
            groupfunc=self.groupfunc,
            itemfunc=self.itemfunc,
            timeperiod=self.period or 0,
            groups=self.groups
        )


class AggregateKeyField(Field):
    def __get__(self, obj, type=None):
        tpl = '{groupfunc}[{groups}, {key}, {itemfunc}, {timeperiod}]'

        groups = obj.groups or ['<not set>']
        if len(groups) > 1:
            groups = '[{}]'.format(','.join(repr(group) for group in groups))
        elif len(groups) == 1:
            for e in groups:
                groups = repr(e)
                break

        timeperiod = obj.timeperiod or 0
        groupfunc = obj.groupfunc
        itemfunc = obj.itemfunc
        key = obj._values[self.key]

        return tpl.format(groupfunc=groupfunc,
                          groups=groups,
                          key=key,
                          itemfunc=itemfunc,
                          timeperiod=timeperiod)

    def contribute_to_class(self, cls, name):
        # TODO declare virtual keys
        super(AggregateKeyField, self).contribute_to_class(cls, name)
        # setattr(cls, 'set_')


class AggregateItem(Item):
    key = AggregateKeyField()

    def __init__(self, name, groups, groupfunc, itemfunc, timeperiod, **fields):
        logging.debug('__init__ %s', self)

        self.groupfunc = groupfunc
        self.itemfunc = itemfunc
        self.timeperiod = timeperiod
        self.groups = set()

        if isinstance(groups, (list, tuple, set)):
            self.groups.update(groups)
        else:
            self.groups.add(groups)

        super(AggregateItem, self).__init__(name, **fields)


class AvgItem(AggregateItem):
    def __init__(self, name, groups, **fields):
        if not name.endswith(' (avg)'):
            name += ' (avg)'

        fields.setdefault('groupfunc', 'grpavg')
        fields.setdefault('itemfunc', 'avg')
        fields.setdefault('timeperiod', '1m')

        super(AvgItem, self).__init__(name, groups, **fields)


class SumItem(AggregateItem):
    def __init__(self, name, groups, **fields):
        if not name.endswith(' (sum)'):
            name += ' (sum)'

        fields.setdefault('groupfunc', 'grpavg')
        fields.setdefault('itemfunc', 'avg')
        fields.setdefault('timeperiod', '1m')

        super(AvgItem, self).__init__(name, groups, **fields)
