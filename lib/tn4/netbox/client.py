from tn4.netbox.sites import Sites
from tn4.netbox.devices import Devices
from tn4.netbox.vlans import Vlans
from tn4.netbox.addresses import Addresses
from tn4.netbox.interfaces import Interfaces

class Client:
    def __init__(self):
        self.sites      = Sites()
        self.devices    = Devices()
        self.vlans      = Vlans()
        self.addresses  = Addresses()
        self.interfaces = Interfaces()

