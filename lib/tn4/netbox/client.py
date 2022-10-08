from tn4.netbox.sites import Sites
from tn4.netbox.vlans import Vlans
from tn4.netbox.addresses import Addresses
from tn4.netbox.devices import Devices
from tn4.netbox.interfaces import Interfaces


class Client:
    def __init__(self):
        self.sites      = Sites()
        self.vlans      = Vlans()
        self.addresses  = Addresses()
        self.devices    = Devices()
        self.interfaces = Interfaces()


    @staticmethod
    def merge_inventory(*inventories):
        merged = inventories[0]
        for inventory in inventories[1:]:
            for hostname in inventory.keys():
                merged[hostname] |= inventory[hostname]
        return merged


    def fetch_as_inventory(self, ctx, use_cache=False, debug=False):
        dprint = lambda s: debug and print(s)

        dprint(f"fetching {self.sites.path}")
        self.sites.fetch_as_inventory(ctx, use_cache=use_cache)
        dprint(f"fetching {self.vlans.path}")
        self.vlans.fetch_as_inventory(ctx, use_cache=use_cache)
        dprint(f"fetching {self.addresses.path}")
        self.addresses.fetch_as_inventory(ctx, use_cache=use_cache)

        dprint(f"fetching {self.devices.path}")
        devices = self.devices.fetch_as_inventory(ctx, use_cache=use_cache)  # depending on sites
        dprint(f"fetching {self.interfaces.path}")
        interfaces = self.interfaces.fetch_as_inventory(ctx, use_cache=use_cache)  # depending on devices, vlans, and addresses

        return self.merge_inventory(devices, interfaces)

