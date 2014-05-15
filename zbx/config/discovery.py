"""

    zbx.config.discovery
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""

from .bases import Model
from .fields import Field, SetField


class DiscoveryRule(Model):
    """
    DiscoveryRule model
    """

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
    applications = SetField(model='Application')
    templates = SetField(model='Template')
    groups = SetField(model='Group')
    interfaces = SetField(model='Interface')
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
