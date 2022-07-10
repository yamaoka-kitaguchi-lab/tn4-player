from tn4.dcim import Sites, Devices, Interfaces
from tn4.ipam import Vlans, Addresses


class Client:
    def __init__(self):
        self.sites = Site()
        self.devices = Devices()
        self.interfaces = Interfaces()
        self.vlans = Vlans()
        self.addresses = Addresses()

