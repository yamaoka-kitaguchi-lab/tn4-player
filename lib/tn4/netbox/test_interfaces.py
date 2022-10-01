from pprint import pprint
import unittest
import sys
sys.path.append('lib')

from tn4.netbox.base import Context
from tn4.netbox.interfaces import Interfaces


class TestInterfaces(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        self.ctx = Context(
            "http://localhost:18000",                   # NetBox URL
            "0123456789abcdef0123456789abcdef01234567"  # NetBox API Token
        )
        self.interfaces = Interfaces.fetch_interfaces(self.ctx)

    def test_netbox_query(self):
        pprint(self.interfaces)


if __name__ == "__main__":
    unittest.main()

