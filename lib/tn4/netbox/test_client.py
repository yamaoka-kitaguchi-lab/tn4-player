from pprint import pprint
import unittest
import sys
sys.path.append('lib')

from tn4.netbox.base import Context
from tn4.netbox.client import Client


class TestClient(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.ctx = Context(
            "http://localhost:18000",                   # NetBox URL
            "0123456789abcdef0123456789abcdef01234567"  # NetBox API Token
        )
        cli = Client()
        cls.interfaces = cli.interfaces.fetch_interfaces(cls.ctx, use_cache=True)


if __name__ == "__main__":
    t = TestClient()
    t.setUpClass()
