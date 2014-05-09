"""
    zbx.config.models
    ~~~~~~~~~~~~~~~~~

"""

__all__ = ['Application', 'DiscoveryRule', 'Document', 'Graph', 'GraphItem',
           'Group', 'Host', 'Interface', 'Item', 'Macro', 'Screen',
           'ScreenItem', 'Template', 'Trigger', 'Valuemap']

from collections import MutableSet
import logging

from zbx.exceptions import *  # NOQA
from zbx.validators import *  # NOQA
from .bases import *  # NOQA
from .fields import *  # NOQA


class Reference(object):
    def __init__(self, model, parent, default=None, append_host=False):
        self.append_host = append_host
        if isinstance(model, str):
            model = load(model, __package__)
        self.model = model
        self.parent = parent
        self.instance = None
        self.value = None
        if default:
            self.update(default)

    def update(self, obj):
        if obj is None:
            self.instance = None
            self.value = None
        elif isinstance(obj, self.model):
            self.instance = obj
            self.value = None
        elif isinstance(obj, dict):
            self.instance = None
            self.value = obj
        else:
            raise ValueError('obj must be a {}'.format(self.model))

    def get_reference(self):
        value = self.value or self.instance.reference()
        if self.append_host:
            value.setdefault('host', self.parent.document_host().name)
        return value


class Collection(MutableSet):
    def __init__(self, model, parent, instances=None):
        logging.debug('p: %s m: %s', parent.__class__, model.__class__)
        if isinstance(model, str):
            model = load(model, __package__)
        self.model = model
        self.parent = parent
        self.instances = []
        if instances:
            self.update(instances)

    def __contains__(self, item):
        """descriptionstring for fname"""

    def __iter__(self):
        return iter(self.instances)

    def __len__(self):
        return len(self.instances)

    def new(self, *args, **kwargs):
        """Instanciate new model, and attach it to the collection.
        """
        instance = self.model(*args, **kwargs)
        return self.add(instance)

    def add(self, obj):
        """add obj to the current collection.

        obj must be a valid instance of model,
        or maybe a dict (if model permits it).
        """
        try:
            obj = self.validate(obj)
            obj.parent = self
            if obj not in self.instances:
                self.instances.append(obj)
        except Exception as error:
            logging.exception(error)
            raise Exception("Unable to add a new {} with {}".format(self.model, obj))  # NOQA
        return obj

    def discard(self, obj):
        obj = self.validate(obj)
        try:
            self.instances.remove(obj)
        except:
            pass

    def update(self, instances):
        for instance in instances:
            self.add(instance)

    def clear(self):
        del self.instances[:]

    def validate(self, obj):
        """Validate value when setting field
        """
        try:
            if isinstance(obj, dict):
                obj = self.model(**obj)
            elif isinstance(obj, str):
                obj = self.model(obj)
            elif not isinstance(obj, self.model):
                raise ValidationError('obj is not a {}'.format(self.model))
        except ValidationError:
            raise
        except Exception as error:
            logging.exception(error)
            raise ValidationError(error.message)

        return obj

    def __repr__(self):
        return '<Collection({}, {}, parent={})>'.format(
            id(self),
            self.model.__name__,
            self.parent.__class__.__name__)


class Application(Model):
    xml_tag = 'application'

    name = Field()

    def __init__(self, name, **fields):
        self.name = name
        self.update(fields)

    def __eq__(self, other):
        return isinstance(other, Application) and other.name == self.name

    def __cmp__(self, other):
        if not isinstance(other, Application):
            raise TypeError('you cannot compare these 2 objects')

        if other.name == self.name:
            return 0
        if other.name < self.name:
            return -1
        return 1

    def __hash__(self):
        return id(self.name)


class Group(Model):
    xml_tag = 'group'

    name = Field()

    def __init__(self, name, **fields):
        self.name = name
        self.update(fields)

    def __eq__(self, other):
        return isinstance(other, Group) and other.name == self.name

    def __cmp__(self, other):
        if not isinstance(other, Group):
            raise TypeError('you cannot compare these 2 objects')

        if other.name == self.name:
            return 0
        if other.name < self.name:
            return -1
        return 1

    def __hash__(self):
        return id(self.name)


class Valuemap(Model):
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
    applications = SetField(model=Application, description='Item applications')
    valuemap = SetField(model=Valuemap,
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


class Interface(Model):
    xml_tag = 'interface'

    ip = Field(description='IP address, can be either IPv4 or IPv6')
    dns = Field('', description='DNS name')
    port = Field(description='Port number')
    type = Field(1, choices=(
        (1, 'agent'),
        (2, 'SNMP'),
        (3, 'IPMI'),
        (4, 'JMX')
    ), description='Interface type')
    useip = Field(0, choices=(
        (0, 'connect to the host using DNS name'),
        (1, 'connect to the host using IP address')
    ), description='How to connect to the host')
    default = Field(0, choices=(
        (0, 'Not default interface'),
        (1, 'Default interface')
    ), description='Interface status')
    interface_ref = Field('if1', description='Interface reference name '
                                             'to be used in items.')

    def __init__(self, ident, **fields):
        ip, port, dns = '', '', ''
        if ':' in ident:
            ident, sep, b = ident.rpartition(':')
            port = int(b)

        if ident:
            if ident.split('.')[-1].isdigit():
                ip = ident
            else:
                dns = ident

        fields.setdefault('ip', ip)
        fields.setdefault('dns', dns)
        fields.setdefault('port', port)
        fields.setdefault('useip', False if fields['dns'] else True)
        self.update(fields)


class Template(Model):
    xml_tag = 'template'

    name = Field()
    template = Field()
    groups = SetField(model=Group)
    applications = SetField(model=Application)
    items = SetField(model=Item)
    discovery_rules = SetField(model='DiscoveryRule')
    macros = SetField(model='Macro', allow_empty=True)
    screens = SetField(model='Screen')
    graphs = SetField(model='Graph')

    def __init__(self, name, **fields):
        self.name = name
        fields.setdefault('template', name)
        self.update(fields)


class Host(Model):
    xml_tag = 'host'

    host = Field(description='Host name')
    name = Field(description='Visible host name')
    proxy = Field('', description='Proxy name')
    status = Field(0, choices=(
        (0, 'monitored'),
        (1, 'unmonitored'),
    ), description='Host Status')
    ipmi_authtype = Field(-1, description='IPMI authentication type')
    ipmi_privilege = Field(2, description='IPMI privilege')
    ipmi_username = Field('', description='IPMI username')
    ipmi_password = Field('', description='IPMI password')
    templates = SetField(model='Template', allow_empty=True)
    groups = SetField(model=Group)
    interfaces = SetField(model=Interface)
    applications = SetField(model=Application)
    items = SetField(model=Item, allow_empty=True)
    discovery_rules = SetField(model='DiscoveryRule', allow_empty=True)
    description = Field()
    graphs = SetField(model='Graph')
    macros = SetField(model='Macro', allow_empty=True)
    inventory = Field('')

    def __init__(self, name, **fields):
        self.name = name
        self.host = fields.pop('host', self.name)
        self.update(fields)


class DiscoveryRule(Model):
    xml_tag = 'discovery_rule'

    key = Field()
    name = Field(description='Visible discovery rule name')
    description = Field()
    type = Field(2)
    status = Field(0, choices=(
        (0, 'Zabbix agent'),
        (1, 'SNMPv1 agent'),
        (2, 'Zabbix trapper'),
        (3, 'simple check'),
        (4, 'SNMPv2 agent'),
        (5, 'Zabbix internal'),
        (6, 'SNMPv3 agent'),
        (7, 'Zabbix agent (active)'),
        (8, 'Zabbix aggregate'),
        (10, 'external check'),
        (11, 'database monitor'),
        (12, 'IPMI agent'),
        (13, 'SSH agent'),
        (14, 'TELNET agent'),
        (15, 'calculated'),
        (16, 'JMX agent'),
    ), description='Host Status')
    proxy = Field(description='Proxy name')
    applications = SetField(model=Application)
    templates = SetField(model=Template)
    groups = SetField(model=Group)
    interfaces = SetField(model=Interface)
    filter = Field(':')
    delay = Field(3600)
    delay_flex = Field()
    lifetime = Field(30)
    item_prototypes = SetField(model='Item', xml_tag='item_prototype')
    trigger_prototypes = SetField(model='Trigger', xml_tag='trigger_prototype')
    graph_prototypes = SetField(model='Graph', xml_tag='graph_prototype')

    allowed_hosts = Field()

    ipmi_authtype = Field(description='IPMI authentication type')
    ipmi_password = Field(description='IPMI password')
    ipmi_privilege = Field(description='IPMI privilege')
    ipmi_sensor = Field()
    ipmi_username = Field(description='IPMI username')

    snmp_community = Field()
    snmp_oid = Field()

    snmpv3_contextname = Field()
    snmpv3_securityname = Field()
    snmpv3_securitylevel = Field(0)
    snmpv3_authprotocol = Field(0)
    snmpv3_authpassphrase = Field()
    snmpv3_privprotocol = Field(0)
    snmpv3_privpassphrase = Field()

    params = Field()

    authtype = Field(0, choices=(
        (0, 'password'),
        (1, 'public key')
    ), description='SSH authentication method. '
                   'Used only by SSH agent item prototypes')
    username = Field()
    password = Field()
    publickey = Field()
    privatekey = Field()
    port = Field()
    host_prototypes = SetField(model='Graph', xml_tag='host_prototype')

    def __init__(self, name, **fields):
        self.name = name
        self.update(fields)


class Trigger(Model):
    xml_tag = 'trigger'

    name = Field()
    expression = Field()
    status = Field()
    priority = Field()
    type = Field()

    def __init__(self, name, **fields):
        self.name = name
        self.update(fields)


class Graph(Model):
    xml_tag = 'graph'

    name = Field()
    width = Field(900)
    height = Field(200)
    yaxismin = Field(0.0)
    yaxismax = Field(0.0)
    show_work_period = Field(1, choices=(
        (0, 'hide'),
        (1, 'show')
    ))
    show_triggers = Field(1, choices=(
        (0, 'hide'),
        (1, 'show')
    ))
    type = Field('normal', choices=(
        (0, 'normal'),
        (1, 'stacked'),
        (2, 'pie'),
        (3, 'exploded')
    ))
    show_legend = Field(1, choices=(
        (0, 'hide'),
        (1, 'show')
    ))
    show_3d = Field(0, choices=(
        (0, '2d'),
        (1, '3d')
    ))
    percent_left = Field(0.0)
    percent_right = Field(0.0)
    ymin_type = Field(0, choices=(
        (0, 'calculated'),
        (1, 'fixed'),
        (2, 'item')
    ))
    ymin_item_1 = Field(0)
    ymax_item_1 = Field(0)
    graph_items = SetField(model='GraphItem')

    def __init__(self, name, **fields):
        self.name = name
        self.update(fields)

    def reference(self):
        response = {
            'name': self.name,
        }

        chaining = [self]
        for parent in self.ancestors():
            chaining.append(parent)
            if isinstance(parent, (Host, Template)):
                response['host'] = parent.name
                break
        logging.debug('chaining: %s', ' > '.join(repr(p) for p in chaining))
        return response


class GraphItem(Model):
    xml_tag = 'graph_item'

    sortorder = Field(0)
    color = ColorField()
    yaxisside = Field(1, choices=(
        (0, 'left side'),
        (1, 'right side')
    ))
    calc_fnc = Field(2, choices={
        (1, 'minimum value'),
        (2, 'average value'),
        (4, 'maximum value'),
        (9, 'last value, used only by pie and exploded graphs')
    })
    drawtype = Field(0, choices=(
        (0, 'line'),
        (1, 'filled region'),
        (2, 'bold line'),
        (3, 'dot'),
        (4, 'dashed line'),
        (5, 'gradient line'),
    ))
    type = Field(0, choices=(
        (0, 'simple'),
        (2, 'graph sum, used only by pie and exploded graphs')
    ))

    item = ReferenceField(model='Item')

    def __init__(self, item=None, **fields):
        if item:
            self.item = item
        self.update(fields)


class Macro(Model):
    xml_tag = 'macro'

    macro = Field()
    value = Field()

    def __init__(self, **fields):
        self.update(fields)


class Document(Model):
    xml_tag = 'zabbix_export'

    templates = SetField(model=Template)
    graphs = SetField(model='Graph')
    hosts = SetField(model='Host')
    screens = SetField(model='Screen')


class Screen(Model):
    xml_tag = 'screen'

    name = Field()
    screen_items = SetField(model='ScreenItem')
    hsize = FixedSizeField(min=3)
    vsize = ElasticField(hsize_field='hsize', items_field='screen_items')

    def __init__(self, name, **fields):
        self.name = name
        self.update(fields)

    def children(self):
        screen_items = None
        for key, value in super(Screen, self).children():
            if key == 'screen_items':
                screen_items = value
            else:
                yield key, value

        # TODO move this logic somewhere else
        x, y = 0, 0
        for item in screen_items:
            item.x = x
            item.y = y
            x += 1
            if x >= self.hsize:
                x, y = 0, y + 1

        yield 'screen_items', screen_items


class ScreenItem(Model):
    xml_tag = 'screen_item'

    # TODO make resourcetype dynamic
    resourcetype = Field(0, choices=(
        (0, 'graph'),
        (1, 'simple graph'),
        (2, 'map'),
        (3, 'plain text'),
        (4, 'hosts info'),
        (5, 'triggers info'),
        (6, 'server info'),
        (7, 'clock'),
        (8, 'screen'),
        (9, 'triggers overview'),
        (10, 'data overview'),
        (11, 'URL'),
        (12, 'history of actions'),
        (13, 'history of events'),
        (14, 'status of host group triggers'),
        (15, 'system status'),
        (16, 'status of host triggers')
    ))
    width = Field(320)
    height = Field(320)
    x = Field()  # virtual field, it will be overridden by parent!
    y = Field()  # virtual field, it will be overridden by parent!
    colspan = Field(1)
    rowspan = Field(1)
    resource = ReferenceField(model='Graph', append_host=True)

    def __init__(self, graph=None, **fields):
        # alias graph to resource
        resource = fields.pop('resource', None)
        fields['resource'] = graph or resource
        self.update(fields)
