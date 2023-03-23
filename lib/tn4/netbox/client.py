from copy import deepcopy

from tn4.netbox.sites import Sites
from tn4.netbox.vlans import Vlans
from tn4.netbox.addresses import Addresses
from tn4.netbox.prefixes import Prefixes
from tn4.netbox.fhrpgroups import FhrpGroups
from tn4.netbox.devices import Devices
from tn4.netbox.interfaces import Interfaces


class Client:
    def __init__(self):
        self.sites       = Sites()
        self.vlans       = Vlans()
        self.addresses   = Addresses()
        self.prefixes    = Prefixes()
        self.fhrp_groups = FhrpGroups()
        self.devices     = Devices()
        self.interfaces  = Interfaces()


    @staticmethod
    def merge_inventory(*inventories):
        merged = deepcopy(inventories[0])
        for inventory in inventories[1:]:
            for hostname in inventory.keys():
                merged[hostname] |= inventory[hostname]
        return merged


    def fetch_as_inventory(self, ctx, use_cache=False):
        self.sites.fetch_as_inventory(ctx, use_cache=use_cache)
        self.vlans.fetch_as_inventory(ctx, use_cache=use_cache)
        self.addresses.fetch_as_inventory(ctx, use_cache=use_cache)
        self.prefixes.fetch_as_inventory(ctx, use_cache=use_cache)
        self.fhrp_groups.fetch_as_inventory(ctx, use_cache=use_cache)

        return self.merge_inventory(
            self.devices.fetch_as_inventory(ctx, use_cache=use_cache),     # depending on sites
            self.interfaces.fetch_as_inventory(ctx, use_cache=use_cache),  # depending on devices, vlans, and addresses
        )

