from pprint import pprint
import unittest
import sys
sys.path.append('lib')

from tn4.netbox.base import Context
from tn4.netbox.interfaces import Interfaces


class TestInterfaces(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.ctx = Context(
            "http://localhost:18000",                   # NetBox URL
            "0123456789abcdef0123456789abcdef01234567"  # NetBox API Token
        )
        i = Interfaces()
        cls.interfaces = i.fetch_interfaces(cls.ctx)

    def test_hoge(self):
        pass


if __name__ == "__main__":
    t = TestInterfaces()
    t.setUpClass()
    #pprint(t.interfaces)

