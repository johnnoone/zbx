"""
    zbx.validators
    ~~~~~~~~~~~~~~
"""

from .exceptions import ValidationError


class ChoiceValidator(object):
    def __init__(self, choices):
        if isinstance(choices, dict):
            self.choices = choices.items()
        else:
            self.choices = choices

    def __call__(self, value):
        for k, v in self.choices:
            if value == k:
                return k
            if value == v:
                return k
        else:
            raise ValidationError('value {} is not allowed'.format(value))

class MinIntValidator(object):
    def __init__(self, min):
        self.min = min

    def __call__(self, value):
        if value < self.min:
            raise ValidationError('value {} must be greater than'.format(value, self.min))
        return value