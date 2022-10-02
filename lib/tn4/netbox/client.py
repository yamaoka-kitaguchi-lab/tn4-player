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


    def fetch_as_inventory(self, ctx, use_cache=False):
        nbdata = {}
        nbdata |= self.sites.fetch_as_inventory(ctx, use_cache=use_cache)
        nbdata |= self.vlans.fetch_as_inventory(ctx, use_cache=use_cache)
        nbdata |= self.addresses.fetch_as_inventory(ctx, use_cache=use_cache)
        nbdata |= self.devices.fetch_as_inventory(ctx, use_cache=use_cache)     # depending on sites
        nbdata |= self.interfaces.fetch_as_inventory(ctx, use_cache=use_cache)  # depending on devices, vlans, and addresses

        return nbdata
