"""
    zbx.builder.defaults
    ~~~~~~~~~~~~~~~~~~~~

    Defines all zabbix defaults
"""

__all__ = ['rules', 'RuleSet']

from abc import ABCMeta
from itertools import chain

from six import add_metaclass


@add_metaclass(ABCMeta)
class RuleSet(object):
    def __init__(self, path, rules):
        self.path = path
        self.rules = rules

    def __iter__(self):
        try:
            rules = self.rules.items()
        except AttributeError:
            rules = self.rules

        for rule in rules:
            try:
                if isinstance(rule, RuleSet):
                    for endpath, value in rule:
                        yield self.format_path(endpath), value
                else:
                    endpath, value = rule
                    yield self.format_path(endpath), value
            except Exception:
                raise

    def format_path(self, path):
        if self.path:
            return '{}/{}'.format(self.path, path)
        return path

    def __add__(self, other):
        return RuleSet(None, chain(self, other))


RuleSet.register(list)


def scope(path, rules):
    return RuleSet(path, rules)

rules = scope('host', [
    ('ipmi_authtype', -1),
    ('ipmi_available', 0),
    ('ipmi_privilege', 2),
    ('ipmi_username', ''),
    ('ipmi_password', ''),
    ('maintenance_status', 0),
    ('snmp_available', 0),
    ('status', 0),
    scope('inventory', [
        ('inventory_mode', 0)
    ]),
])

rules += scope('host_prototype', [
    ('ipmi_authtype', -1),
    ('ipmi_available', 0),
    ('ipmi_privilege', 2),
    ('maintenance_status', 0),
    ('snmp_available', 0),
    ('status', 0),
    scope('inventory', [
        ('inventory_mode', 0)
    ]),
])

rules += scope('item', [
    ('authtype', 0),
    ('data_type', 0),
    ('delta', 0),
    ('formula', 1),
    ('history', 90),
    ('inventory_link', 0),
    ('state', 0),
    ('status', 0),
    ('trends', 365),
    ('units', ''),
    ('snmpv3_authprotocol', 0),
    ('snmpv3_privprotocol', 0),
    ('multiplier', 0),
])

rules += scope('screen', [
    # ('hsize', 1),
    ('vsize', 1)
])

rules += scope('screen_item', [
    ('dynamic', 0),
    ('elements', 25),
    ('halign', 0),
    ('height', 200),
    ('sort_triggers', 0),
    ('style', 0),
    ('valign', 0),
    ('width', 320),
    # ('x', 0),
    # ('y', 0),
    ('colspan', 1),
    ('rowspan', 1),
])


rules += scope('action', [
    ('recovery_msg', 0),
    ('status', 0),
    scope('condition', [
        ('operator', 0)
    ]),
    scope('operation', [
        ('esc_period', 0),
        ('esc_step_from', 1),
        ('esc_step_to', 1),
        ('evaltype', 0),
    ]),
    scope('message', [
        ('default_msg', 0)
    ]),
    scope('operation', [
        ('operator', 0)
    ])
])

rules += scope('graph', [
    ('type', 0),
    ('percent_left', 0.),
    ('percent_right', 0.),
    ('show_3d', 0),
    ('show_legend', 1),
    ('show_work_period', 1),
    ('show_triggers', 1),
    ('yaxismax', 100.0),
    ('yaxismin', 0.0),
    ('ymax_type', 0),
    ('ymin_type', 0),
    ('ymin_item_1', 0),
    ('ymax_item_1', 0)
])

rules += scope('graph_item', [
    ('calc_fnc', 2),
    ('drawtype', 0),
    ('sortorder', 0),
    ('type', 0),
    ('yaxisside', 0)
])

rules += scope('trigger', [
    ('priority', 0),
    ('state', 0),
    ('status', 0),
    ('type', 0),
    ('value', 0)
])

rules += scope('discovery_rule', [
    ('authtype', 0),
    ('lifetime', 30),
    ('snmpv3_authprotocol', 0),
    ('snmpv3_privprotocol', 0),
    ('state', 0),
    ('status', 0),
])
