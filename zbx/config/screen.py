"""

    zbx.config.screen
    ~~~~~~~~~~~~~~~~~

"""

__all__ = ['Screen', 'ScreenItem']

from .bases import Model
from .fields import FixedSizeField, ElasticField
from .fields import Field, SetField, ReferenceField


class Screen(Model):
    """
    Screen model
    """

    xml_tag = 'screen'

    name = Field()
    screen_items = SetField(model='ScreenItem')
    hsize = FixedSizeField(default=3, min=1)
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
    """
    ScreenItem model
    """

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
    height = Field(200)
    x = Field()  # virtual field, it will be overridden by parent!
    y = Field()  # virtual field, it will be overridden by parent!
    colspan = Field(1)
    rowspan = Field(1)
    resource = ReferenceField(model='Graph', append_host=True)
    dynamic = Field(0, choices=(
        (0, 'not dynamic'),
        (1, 'dynamic')
    ))
    elements = Field(25)
    halign = Field(0, choices=(
        (0, 'center'),
        (1, 'left'),
        (1, 'right'),
    ))
    valign = Field(0, choices=(
        (0, 'center'),
        (1, 'top'),
        (1, 'bottom'),
    ))

    sort_triggers = Field(0, choices=(
        # Possible values for status of host group
        # triggers and status of host triggers screen items
        (0, '(default) last change, descending'),
        (1, 'severity, descending'),
        (2, 'host, ascending'),

        # Possible values for history of actions screen elements
        (3, 'time, ascending'),
        (4, 'time, descending'),
        (5, 'type, ascending'),
        (6, 'type, descending'),
        (7, 'status, ascending'),
        (8, 'status, descending'),
        (9, 'retries left, ascending'),
        (10, 'retries left, descending'),
        (11, 'recipient, ascending'),
        (12, 'recipient, descending'),
    ))
    style = Field(0)

    def __init__(self, graph=None, **fields):
        # alias graph to resource
        resource = fields.pop('resource', None)
        fields['resource'] = graph or resource
        self.update(fields)
