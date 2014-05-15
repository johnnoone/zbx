"""

    zbx.config.hosts
    ~~~~~~~~~~~~~~~~~~~~~~~

"""

__all__ = ['Host', 'Interface', 'Template']

from .bases import Model
from .fields import Field, SetField


class Template(Model):
    """
    Template model
    """

    xml_tag = 'template'

    name = Field()
    template = Field()
    groups = SetField(model='Group')
    applications = SetField(model='Application')
    items = SetField(model='Item')
    discovery_rules = SetField(model='DiscoveryRule')
    macros = SetField(model='Macro', allow_empty=True)
    screens = SetField(model='Screen')
    graphs = SetField(model='Graph')
    triggers = SetField(model='Trigger')

    def __init__(self, name, **fields):
        self.name = name
        fields.setdefault('template', name)
        self.update(fields)


class Host(Model):
    """
    Host model
    """

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
    groups = SetField(model='Group')
    interfaces = SetField(model='Interface')
    applications = SetField(model='Application')
    items = SetField(model='Item', allow_empty=True)
    discovery_rules = SetField(model='DiscoveryRule', allow_empty=True)
    description = Field()
    graphs = SetField(model='Graph')
    macros = SetField(model='Macro', allow_empty=True)
    inventory = Field('')

    def __init__(self, name, **fields):
        self.name = name
        self.host = fields.pop('host', self.name)
        self.update(fields)


class Interface(Model):
    """
    Interface model
    """

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
