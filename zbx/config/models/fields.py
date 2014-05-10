from itertools import cycle
import math
from six import add_metaclass
import logging

from zbx.exceptions import *  # NOQA
from zbx.validators import *  # NOQA
from zbx.util import load


class FieldBase(type):
    def increment(start=0, step=1):
        i = start
        while True:
            yield i
            i += step

    _pos = increment()


@add_metaclass(FieldBase)
class Field(object):
    validators = []
    _pos = None

    def __new__(cls, *args, **kwargs):
        try:
            instance = object.__new__(cls, *args, **kwargs)
        except TypeError as error:
            raise Exception(cls.__name__, error.message)
        instance._pos = FieldBase._pos.next()

        return instance

    def __init__(self, default=None, choices=None, description=None, validators=None):  # NOQA
        if description:
            self.__doc__ = description
        self.validators = list(self.__class__.validators)
        self.validators += list(validators or [])
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
        try:
            for validator in self.validators:
                value = validator(value)
        except ValidationError as error:
            msg = '{} does not validate: {}'.format(self.key, error.message)
            raise ValidationError(msg)
        return value

    def contribute_to_class(self, cls, name):
        self.key = name
        cls._fields[name] = self

    def get_default(self, parent):
        return self.default

    def set_default(self, parent, value):
        return self.__set__(parent, value)


class SetField(Field):
    def __init__(self, model, xml_tag=None, allow_empty=False, **kwargs):
        self.model = model
        self.xml_tag = xml_tag
        self.allow_empty = allow_empty
        super(SetField, self).__init__(**kwargs)

    def __set__(self, obj, value):
        obj._values[self.key].clear()
        obj._values[self.key].update(value or [])

    def __delete__(self, obj):
        obj._values[self.key].clear()

    def get_default(self, parent):
        logging.debug('sf: %s > %s', parent, self.model)

        # TODO fix this
        Collection = load('zbx.config.models.Collection')

        value = Collection(self.model, parent, self.default)
        value.allow_empty = self.allow_empty
        return value

    def set_default(self, parent, value):
        return self.__get__(parent).update(value or [])


class ReferenceField(Field):
    def __init__(self, model, append_host=False, **kwargs):
        self.model = model
        self.append_host = append_host
        super(ReferenceField, self).__init__(**kwargs)

    def __set__(self, obj, value):
        obj._values[self.key].update(value)

    def __delete__(self, obj):
        obj._values[self.key].clear()

    def get_default(self, parent):
        """Initialise a value will Model hydratation
        """

        # TODO fix this
        Reference = load('zbx.config.models.Reference')

        return Reference(self.model, parent, self.default, self.append_host)


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
        return max(1, value)

    def __set__(self, obj, value):
        obj._values[self.key] = self.validate(value)

    def __delete__(self, obj):
        del obj._values[self.key]

    def contribute_to_class(self, cls, name):
        super(ElasticField, self).contribute_to_class(cls, name)


class ColorField(Field):
    colors = cycle(['C80000', '009600', '000096',
                    '960096', '009696', '969600',
                    '969696', 'FF0000', '00FF00', '0000FF'])

    def __get__(self, obj, type=None):
        return obj._values[self.key] or self.colors.next()
