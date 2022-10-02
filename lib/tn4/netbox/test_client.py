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
        cls.nbdata = {}
        cls.nbdata |= cli.sites.fetch_all(cls.ctx, use_cache=True)
        cls.nbdata |= cli.devices.fetch_all(cls.ctx, use_cache=True)     # depending on sites
        cls.nbdata |= cli.vlans.fetch_all(cls.ctx, use_cache=True)
        cls.nbdata |= cli.addresses.fetch_all(cls.ctx, use_cache=True)
        cls.nbdata |= cli.interfaces.fetch_all(cls.ctx, use_cache=True)  # depending on devices, vlans, addresses

        #pprint(cls.nbdata["lag_members"])
        #pprint(cls.nbdata["interfaces"].keys())
        cls.pprint_interface(cls.nbdata["interfaces"]["minami3"], names=["et-1/2/1"])


    @staticmethod
    def pprint_interface(interfaces, names=None):
        keys = ["all_vids", "all_vlans", "untagged_vid", "untagged_vlan", "tagged_vids", "tagged_vlans", "absent_vids"]
        for interface in interfaces.values():
            for key in keys:
                interface[key] = None

        if names is not None:
            for name in names:
                pprint(interfaces[name])
        else:
            pprint(interfaces)


if __name__ == "__main__":
    t = TestClient()
    t.setUpClass()

