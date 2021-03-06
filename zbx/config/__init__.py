"""

    zbx.config
    ~~~~~~~~~~

"""

from __future__ import absolute_import

__all__ = ['Application', 'DiscoveryRule', 'Config', 'Graph', 'GraphItem',
           'Group', 'Host', 'Interface', 'Item', 'Macro', 'Screen',
           'ScreenItem', 'Template', 'Trigger', 'ValueMap']

from .bases import *  # NOQA
from .discovery import *  # NOQA
from .fields import *  # NOQA
from .graph import *  # NOQA
from .helpers import *  # NOQA
from .hosts import *  # NOQA
from .items import *  # NOQA
from .screen import *  # NOQA
from .tagging import *  # NOQA
from zbx.exceptions import *  # NOQA
from zbx.validators import *  # NOQA


class Config(Model):
    """
    Main config model
    """

    xml_tag = 'zabbix_export'

    templates = SetField(model='Template')
    graphs = SetField(model='Graph')
    hosts = SetField(model='Host')
    screens = SetField(model='Screen')


class Trigger(Model):
    """
    Trigger model
    """

    xml_tag = 'trigger'

    name = Field()
    description = Field()
    expression = Field()
    status = Field(0, choices=(
        (0, 'enabled'),
        (1, 'disabled')
    ))
    priority = Field(0, choices=(
        (0, 'not classified'),
        (1, 'information'),
        (2, 'warning'),
        (3, 'average'),
        (4, 'high'),
        (5, 'disaster')
    ))
    type = Field(0, choices=(
        (0, 'do not generate multiple events'),
        (1, 'generate multiple events'),
    ))

    def __init__(self, name, **fields):
        self.name = name
        self.update(fields)


class Macro(Model):
    """
    Macro model
    """

    xml_tag = 'macro'

    macro = Field()
    value = Field()

    def __init__(self, **fields):
        self.update(fields)
