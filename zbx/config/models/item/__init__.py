"""
    zbx.config.models.item
    ~~~~~~~~~~~~~~~~~~~~~~

"""

__all__ = ['Item', 'ValueMap']

import logging

from ..bases import Model
from ..fields import Field, SetField
from zbx.util import load


class ValueMap(Model):
    xml_tag = 'valuemap'


class Item(Model):
    xml_tag = 'item'

    name = Field(description='Item name')
    key = Field(description='Item key')
    description = Field(description='Item description')
    type = Field(2, choices=(
        (0, 'Zabbix agent'),
        (1, 'SNMPv1'),
        (2, 'Trapper'),
        (3, 'Simple check'),
        (4, 'SNMPv2'),
        (5, 'Internal'),
        (6, 'SNMPv3'),
        (7, 'Active check'),
        (8, 'Aggregate'),
        (9, 'HTTP test (web monitoring scenario step)'),
        (10, 'External'),
        (11, 'Database monitor'),
        (12, 'IPMI'),
        (13, 'SSH'),
        (14, 'telnet'),
        (15, 'Calculated'),
        (16, 'JMX'),
        (17, 'SNMP trap'),
    ), description='Item type')
    data_type = Field(0, choices=(
        (0, 'decimal'),
        (1, 'octal'),
        (2, 'hexadecimal'),
        (3, 'boolean'),
    ), description='Data type of the item')
    delay = Field(60, description='Check interval')
    history = Field(7, description='How long to keep item history (days)')
    trends = Field(365, description='How long to keep item trends (days)')
    status = Field(0, choices=(
        (0, 'enabled item'),
        (1, 'disabled item'),
        (3, 'unsupported item')
    ), description='Item status')
    value_type = Field(3, choices=(
        (0, 'numeric_float'),
        (1, 'character'),
        (2, 'log'),
        (3, 'numeric_unsigned'),
        (4, 'text')
    ), description='Value type')
    units = Field('', description='Value units')
    multiplier = Field(0, description='Value multiplier')
    delta = Field(0, choices=(
        (0, 'as_is'),
        (1, 'delta_per_second'),
        (2, 'delta_simple')
    ), description='Store values as delta')
    formula = Field(1, description='')
    delay_flex = Field(description='Flexible delay')
    trapper_hosts = Field(description='')
    snmp_community = Field(description='SNMP Community name')
    snmp_oid = Field(description='SNMP OID')
    port = Field(description='Item custom port')
    snmpv3_securityname = Field(description='SNMPv3 security name')
    snmpv3_securitylevel = Field(description='SNMPv3 security level')
    snmpv3_authpassphrase = Field(description='SNMPv3 authentication phrase')
    snmpv3_privpassphrase = Field(description='SNMPv3 private phrase')
    params = Field(description='')
    ipmi_sensor = Field(description='IPMI sensor')
    authtype = Field(0, choices=(
        (0, 'password'),
        (1, 'public key')
    ), description='SSH authentication method. '
                   'Used only by SSH agent item prototypes')
    username = Field(description='')
    password = Field(description='')
    publickey = Field(description='')
    privatekey = Field(description='')
    interface_ref = Field(description='Reference to host interface')
    inventory_link = Field(0, description='Host inventory field number, '
                                          'that will be updated with the '
                                          'value returned by the item')
    applications = SetField(model='Application')
    valuemap = SetField(model=ValueMap,
                        description='Value map assigned to item',
                        allow_empty=True)

    def __init__(self, name, **fields):
        logging.debug('__init__ %s', self)
        self.name = name
        self.update(fields)

    def reference(self):
        response = {
            'key': self.key,
        }

        Host = load('Host', __package__.rpartition('.')[0])
        Template = load('Template', __package__.rpartition('.')[0])
        chaining = [self]
        for parent in self.ancestors():
            chaining.append(parent)
            if isinstance(parent, (Host, Template)):
                response['host'] = parent.name
                break
        logging.debug('chaining: %s', ' > '.join(repr(p) for p in chaining))
        return response

    def expression(self):
        reference = self.reference()

        if 'host' in reference:
            return '{host}:{key}'.format(**reference)
        else:
            return '{}'.format(reference['key'])
