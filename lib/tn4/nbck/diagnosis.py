from tn4.nbck.state import DeviceState, InterfaceState


class NetBoxDiagnosis:
    def __init__(self, ctx):
        self.nb_vlan_objs      = ctx.vlans
        self.nb_device_objs    = ctx.devices
        self.nb_interface_objs = ctx.interfaces


    def check_wifi_tag_consistency(self):
        for hostname, interfaces in self.nb_interface_objs.items():
            for ifname, interface in interfaces.items():
                not interface["is_to_ap"] and continue  # skip if the interface is not for AP





    def check_hosting_tag_consistency(self):
        pass


