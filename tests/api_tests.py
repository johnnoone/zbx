import unittest
from zbx.api import *

class ApiTestCase(unittest.TestCase):

    def test_cast(self):
        assert cast('1') == 1
        assert cast(1) == 1
        assert cast({'foo': '1', 'bar': 1}) == {'foo': 1, 'bar': 1}
        assert cast(['1', 1]) == [1, 1]
        assert cast({'foo': '1', 'bar': 1}) == {'foo': 1, 'bar': 1}
        assert cast({'foo': ['1']}) == {'foo': [1]}
