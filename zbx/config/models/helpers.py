"""
    zbx.config.models.helpers
    ~~~~~~~~~~~~~~~~~~~~~~~~~
"""

__all__ = ['Reference', 'Collection']

from collections import MutableSet
import logging

from zbx.exceptions import ValidationError
from zbx.util import load


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

    def __contains__(self, obj):
        obj = self.validate(obj)
        return obj in self.instances

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
