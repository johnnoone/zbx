"""

    zbx.config.tagging
    ~~~~~~~~~~~~~~~~~~

"""

__all__ = ['Application', 'Group']

from .bases import Model
from .fields import Field


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
