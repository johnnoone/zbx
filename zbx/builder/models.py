__all__ = ['Application', 'DiscoveryRule', 'Document', 'Graph', 'GraphItem',
           'Group', 'Host', 'Interface', 'Item', 'Macro', 'Screen',
           'ScreenItem', 'Template', 'Trigger', 'Valuemap']

from collections import OrderedDict, MutableSet
from copy import copy
import datetime
import logging
import importlib
import math
from itertools import cycle
from six import add_metaclass

from zbx.exceptions import *
from zbx.validators import *


class Field(object):
    validators = []

    def __init__(self, default=None, choices=None, description=None, validators=None):
        if description:
            self.__doc__ = description
        self.validators = list(self.__class__.validators) + list(validators or [])
        if choices:
            self.validators.append(ChoiceValidator(choices))
        if default is not None:
            self.default = self.validate(default)
        else:
            self.default = None

    def __get__(self, obj, type=None):
        return obj._values[self.key]

    def __set__(self, obj, value):
        obj._values[self.key] = self.validate(value)

    def __delete__(self, obj):
        del obj._values[self.key]

    def validate(self, value):
        for validator in self.validators:
            value = validator(value)
        return value

    def contribute_to_class(self, cls, name):
        self.key = name
        cls._fields[name] = self

    def get_default(self, parent):
        return self.default


class SetField(Field):
    def __init__(self, model, xml_tag=None, **kwargs):
        self.model = model
        self.xml_tag = xml_tag
        super(SetField, self).__init__(**kwargs)

    def __set__(self, obj, value):
        obj._values[self.key].clear()
        obj._values[self.key].update(value or [])

    def __delete__(self, obj):
        obj._values[self.key].clear()

    def get_default(self, parent):
        logging.debug('sf: %s > %s', parent, self.model)
        return Collection(self.model, parent, self.default)

    def contribute_to_class(self, cls, name):
        super(SetField, self).contribute_to_class(cls, name)


class ReferenceField(Field):
    def __init__(self, model, **kwargs):
        self.model = model
        super(ReferenceField, self).__init__(**kwargs)

    def __set__(self, obj, value):
        obj._values[self.key].update(value)

    def __delete__(self, obj):
        obj._values[self.key].clear()

    def get_default(self, parent):
        return Reference(self.model, parent, self.default)


class FixedSizeField(Field):
    validators = []

    def __init__(self, min, **kwargs):
        validators = kwargs.pop('validators', []) or []
        validators.append(MinIntValidator(min))
        default = kwargs.pop('default', min)
        kwargs['validators'] = validators
        kwargs['default'] = default
        super(FixedSizeField, self).__init__(**kwargs)

    def contribute_to_class(self, cls, name):
        super(FixedSizeField, self).contribute_to_class(cls, name)


class ElasticField(Field):
    def __init__(self, hsize_field, items_field, **kwargs):
        self.hsize_field = hsize_field
        self.items_field = items_field
        super(ElasticField, self).__init__(**kwargs)

    def __get__(self, obj, type=None):
        value = obj._values[self.key]
        if value <= 0:
            # value must be guessed from hsize_field and items_field
            a = len(getattr(obj, self.items_field))
            b = getattr(obj, self.hsize_field) or 1
            try:
                value = int(math.ceil(float(a) / b))
            except TypeError:
                logging.error('failed with items:%s %s', a, b)
        return value

    def __set__(self, obj, value):
        obj._values[self.key] = self.validate(value)

    def __delete__(self, obj):
        del obj._values[self.key]

    def contribute_to_class(self, cls, name):
        super(ElasticField, self).contribute_to_class(cls, name)


class ColorField(Field):
    colors = cycle(['C80000', '009600', '000096', '960096', '009696', '969600', '969696', 'FF0000', '00FF00', '0000FF'])

    def __get__(self, obj, type=None):
        return obj._values[self.key] or self.colors.next()

class Reference(object):
    def __init__(self, model, parent, default=None):
        if isinstance(model, str):
            mod, sep, cls = model.rpartition('.')
            m = importlib.import_module(mod or __package__)
            model = getattr(m, cls)
        self.model = model
        self.parent = parent
        if default:
            self.update(default)
            self.instance = default
            self.value = default

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
        return self.value or self.instance.reference()


class Collection(MutableSet):
    def __init__(self, model, parent, instances=None):
        logging.debug('p: %s m: %s', parent.__class__, model.__class__)
        if isinstance(model, str):
            mod, sep, cls = model.rpartition('.')
            m = importlib.import_module(mod or __package__)
            model = getattr(m, cls)
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
            else:
                obj = obj.clone()
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


class ModelBase(type):
    def __new__(cls, name, bases, attrs):
        attrs.setdefault(
            '_fields', OrderedDict()
        )
        new_class = super(ModelBase, cls).__new__(cls, name, bases, attrs)

        logging.debug('nc: %s', new_class)

        for name, value in attrs.items():
            if hasattr(value, 'contribute_to_class'):
                value.contribute_to_class(new_class, name)

        return new_class


@add_metaclass(ModelBase)
class Model(object):
    """The mother of all models"""

    def __new__(cls, *args, **kwargs):
        try:
            instance = object.__new__(cls, *args, **kwargs)
        except TypeError as error:
            raise Exception(cls.__name__, error.message)

        logging.debug('__new__ %s', instance)

        instance._values = OrderedDict()
        instance.parent = None
        for name, field in instance._fields.items():
            instance._values[name] = field.get_default(instance)

        return instance

    def update(self, fields):
        """hydrate model with these fields"""
        logging.debug('update %s', self)
        for key, value in fields.items():
            try:
                field = self._fields[key]
            except KeyError:
                raise ValueError('Field {} for {} is not defined'.format(
                                 key, self.__class__.__name__))
            if isinstance(field, SetField):
                field.__get__(self).update(value or [])
            else:
                field.__set__(self, value)

    def children(self):
        fields = self._values.keys()
        for key in fields:
            yield key, getattr(self, key)

    def clone(self):
        return copy(self)

    def reference(self):
        raise NotImplementedError

    def __repr__(self):
        return '<{}({}, parent={})>'.format(
            self.__class__.__name__,
            id(self),
            self.parent.__class__.__name__)


class Application(Model):
    xml_tag = 'application'

    name = Field()

    def __init__(self, name, **fields):
        self.name = name
        self.update(fields)


class Group(Model):
    xml_tag = 'group'

    name = Field()

    def __init__(self, name, **fields):
        self.name = name
        self.update(fields)


class Valuemap(Model):
    xml_tag = 'valuemap'


class Item(Model):
    xml_tag = 'item'

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
    snmp_community = Field(description='SNMP Community name')
    snmp_oid = Field(description='SNMP OID')
    port = Field(description='Item custom port')
    name = Field(description='Item name')
    key = Field(description='Item key')
    delay = Field(description='Check interval')
    history = Field(description='How long to keep item history (days)')
    trends = Field(description='How long to keep item trends (days)')
    status = Field(description='Item status')
    value_type = Field(3, choices=(
        (3, 'numeric_unsigned'),
        (0, 'numeric_float'),
        (1, 'character'),
        (2, 'log'),
        (4, 'text')
    ), description='Value type')
    trapper_hosts = Field(description='')
    units = Field(description='Value units')
    multiplier = Field(description='Value multiplier')
    delta = Field(0, choices=(
        (0, 'as_is'),
        (1, 'delta_per_second'),
        (2, 'delta_simple')
    ), description='Store values as delta')
    snmpv3_securityname = Field(description='SNMPv3 security name')
    snmpv3_securitylevel = Field(description='SNMPv3 security level')
    snmpv3_authpassphrase = Field(description='SNMPv3 authentication phrase')
    snmpv3_privpassphrase = Field(description='SNMPv3 private phrase')
    formula = Field(description='')
    delay_flex = Field(description='Flexible delay')
    params = Field(description='')
    ipmi_sensor = Field(description='IPMI sensor')
    data_type = Field(0, choices=(
        (0, 'decimal'),
        (1, 'octal'),
        (2, 'hexadecimal'),
        (3, 'boolean'),
    ), description='Data type of the item')
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
    description = Field(description='Item description')
    inventory_link = Field(description='Host inventory field number, '
                                       'that will be updated with the '
                                       'value returned by the item')
    applications = SetField(model=Application, description='Item applications')
    valuemap = SetField(model=Valuemap,
                        description='Value map assigned to item')

    def __init__(self, name, **fields):
        logging.debug('__init__ %s', self)
        self.name = name
        self.update(fields)

    def reference(self):
        response = {
            'key': self.key
        }

        parent = self.parent
        print self, '>',
        while parent:
            print parent, '>',
            if isinstance(parent, (Host, Template)):
                response['host'] = parent.name
                break
            else:
                parent = parent.parent
        print
        return response

    def expression(self):
        reference = self.reference()

        if 'host' in reference:
            return '{host}:{key}'.format(**reference)
        else:
            return '{}'.format(reference['key'])


class Interface(Model):
    xml_tag = 'interface'

    default = Field(0, choices=(
        (0, 'Not default interface'),
        (1, 'Default interface')
    ), description='Interface status')
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
    ip = Field(description='IP address, can be either IPv4 or IPv6')
    dns = Field(description='DNS name')
    port = Field(description='Port number')
    interface_ref = Field(description='Interface reference name '
                                      'to be used in items.')

    def __init__(self, ident, **fields):
        ip, port, dns = None, None, None
        if ':' in ident:
            ident, sep, b = ident.rpartition(':')
            port = int(port)

        if ident:
            if ident.split('.')[-1].isdigit():
                ip = ident
            else:
                dns = ident

        fields.setdefault('ip', ip)
        fields.setdefault('dns', dns)
        fields.setdefault('port', port)

        self.update(fields)


class Template(Model):
    xml_tag = 'template'

    name = Field()
    groups = SetField(model=Group)
    applications = SetField(model=Application)
    items = SetField(model=Item)
    screens = SetField(model='Screen')
    discovery_rules = SetField(model='DiscoveryRule')

    def __init__(self, name, **fields):
        self.name = name
        self.update(fields)


class Host(Model):
    xml_tag = 'host'

    host = Field(description='Host name')
    name = Field(description='Visible host name')
    description = Field()
    status = Field(description='Host Status')
    proxy = Field(description='Proxy name')
    ipmi_authtype = Field(description='IPMI authentication type')
    ipmi_privilege = Field(description='IPMI privilege')
    ipmi_username = Field(description='IPMI username')
    ipmi_password = Field(description='IPMI password')
    applications = SetField(model=Application)
    templates = SetField(model='Template')
    groups = SetField(model=Group)
    interfaces = SetField(model=Interface)
    items = SetField(model=Item)
    discovery_rules = SetField(model='DiscoveryRule')
    macros = SetField(model='Macro')

    def __init__(self, name, **fields):
        self.name = name
        self.update(fields)


class DiscoveryRule(Model):
    xml_tag = 'discovery_rule'

    key = Field()
    name = Field(description='Visible discovery rule name')
    description = Field()
    type = Field(2)
    status = Field(description='Host Status')
    proxy = Field(description='Proxy name')
    ipmi_authtype = Field(description='IPMI authentication type')
    ipmi_privilege = Field(description='IPMI privilege')
    ipmi_username = Field(description='IPMI username')
    ipmi_password = Field(description='IPMI password')
    applications = SetField(model=Application)
    templates = SetField(model=Template)
    groups = SetField(model=Group)
    interfaces = SetField(model=Interface)
    filter = Field()
    delay = Field()
    delay_flex = Field()
    lifetime = Field()
    item_prototypes = SetField(model='Item', xml_tag='item_prototype')
    trigger_prototypes = SetField(model='Trigger', xml_tag='trigger_prototype')
    graph_prototypes = SetField(model='Graph', xml_tag='graph_prototype')

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
    ymax_item_1 = Field()
    graph_items = SetField(model='GraphItem')

    def __init__(self, name, **fields):
        self.name = name
        self.update(fields)

    def reference(self):
        response = {
            'name': self.name
        }

        parent = self.parent
        while parent:
            if isinstance(parent, (Host, Template)):
                response['host'] = parent.name
                break
            else:
                parent = parent.parent

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
    graphs = SetField(model=Graph)

    def __init__(self):
        self.date = datetime.datetime.now()

    def children(self):
        yield 'version', '2.0'
        yield 'date', self.date.isoformat()
        for key, value in super(Document, self).children():
            yield key, value
        yield 'groups', self.groups

    @property
    def groups(self):
        """Extract groups from descendant
        """
        def extract(obj):
            if isinstance(obj, Group):
                yield obj
            if isinstance(obj, Model):
                for key, value in obj.children():
                    for group in extract(value):
                        yield group
            if isinstance(obj, (Collection, set, list, tuple)):
                for value in obj:
                    for group in extract(value):
                        yield group

        groups = set()
        for key, value in super(Document, self).children():
            groups.update(extract(value))
        return groups

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

    resourcetype = Field(1, choices=(
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
    resource = ReferenceField(model='Graph')
    x = Field() # virtual field, it will be overridden by parent!
    y = Field() # virtual field, it will be overridden by parent!

    def __init__(self, graph=None, **fields):
        resource = fields.pop('resource', None)
        fields['resource'] = graph or resource
        self.update(fields)
