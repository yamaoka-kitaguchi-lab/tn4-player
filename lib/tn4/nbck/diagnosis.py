from tn4.netbox.slug import Slug
from tn4.nbck.base import Base, Vlans, Devices, Interfaces
from tn4.nbck.state import DeviceState, InterfaceState


class Diagnosis(Base):
    def __init__(self, ctx):
        self.nb_vlans      = Vlans(ctx.vlans)
        self.nb_devices    = Devices(ctx.devices)
        self.nb_interfaces = Interfaces(ctx.interfaces)


    def check_wifi_tag_consistency(self):
        wifi_dplane_vids = self.nb_vlans.with_tags(Slug.Tag.Wifi)

        for hostname, interfaces in self.nb_interfaces.all.items():


            for ifname, interface in interfaces.items():
                not interface["is_to_ap"] and continue  # skip if the interface is not for AP






    def check_hosting_tag_consistency(self):
        pass


