"""
    zbx.config.models.screen
    ~~~~~~~~~~~~~~~~~~~~~~~~

"""

__all__ = ['Graph', 'GraphItem']

import logging

from .bases import Model
from .fields import Field, SetField, ColorField, ReferenceField
from zbx.util import load


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

    def children(self):
        graph_items = None
        for key, value in super(Graph, self).children():
            if key == 'graph_items':
                graph_items = value
            else:
                yield key, value

        # TODO move this logic somewhere else
        for i, item in enumerate(graph_items):
            item.sortorder = i

        yield 'graph_items', graph_items

    def reference(self):
        response = {
            'name': self.name,
        }

        Host = load('Host', __package__)
        Template = load('Template', __package__)
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
