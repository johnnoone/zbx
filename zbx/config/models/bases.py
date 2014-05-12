"""
    zbx.config.models.bases
    ~~~~~~~~~~~~~~~~~~~~~~~

"""

__all__ = ['ModelBase', 'Model']

from six import add_metaclass
from collections import OrderedDict
import logging

from zbx.util import load


class ModelBase(type):
    def __new__(cls, name, bases, attrs):
        attrs.setdefault(
            '_fields', OrderedDict()
        )
        new_class = super(ModelBase, cls).__new__(cls, name, bases, attrs)

        logging.debug('nc: %s', new_class)

        for base in bases:
            if hasattr(base, '_fields'):
                new_class._fields.update(base._fields)
            # print name, attrs, bases

        for name, value in attrs.items():
            if hasattr(value, 'contribute_to_class'):
                value.contribute_to_class(new_class, name)

        # keep _field sorted by there _pos
        new_class._fields = OrderedDict(sorted(new_class._fields.items(),
                                        key=lambda x: x[1]._pos))

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
            field.set_default(self, value)

    def children(self):
        fields = self._fields.keys()
        for key in fields:
            value = getattr(self, key)
            if value is not None:
                yield key, value

    def ancestors(self):
        """Returns all ancestors"""
        parent = self.parent
        while parent:
            yield parent
            parent = parent.parent

    def document_host(self):
        """Returns the document host (used into references...)
        """
        # TODO fix this
        Config = load('zbx.config.models.Config')

        for parent in self.ancestors():
            if isinstance(parent.parent.parent, Config):
                return parent

    def reference(self):
        raise NotImplementedError

    def extract(self, model):
        """Extract model from me and descendant
        """
        if not issubclass(model, Model):
            raise ValueError('must be a Model type !')

        # TODO fix this
        Host = load('zbx.config.models.Host')

        groups = set()
        for key, value in super(Host, self).children():
            groups.update(self._extract(value, model))
        return groups

    def _extract(self, obj, model):

        # TODO fix this
        Collection = load('zbx.config.models.Collection')

        if isinstance(obj, model):
            yield obj
        if isinstance(obj, Model):
            for key, value in obj.children():
                for group in self._extract(value, model):
                    yield group
        if isinstance(obj, (Collection, set, list, tuple)):
            for value in obj:
                for group in self._extract(value, model):
                    yield group

    def __repr__(self):
        return '<{}({}, parent={})>'.format(
            self.__class__.__name__,
            id(self),
            self.parent.__class__.__name__)
