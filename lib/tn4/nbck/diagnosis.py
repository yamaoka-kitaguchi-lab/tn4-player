from tn4.netbox.slug import Slug
from tn4.nbck.base import Base, Vlans, Devices, Interfaces
from tn4.nbck.state import ConditionalValue as CV
from tn4.nbck.state import Condition as Cond
from tn4.nbck.state import InterfaceCondition
from tn4.nbck.state import DeviceState, InterfaceState, NbckReport, ReportCategory


class Diagnosis(Base):
    def __init__(self, ctx):
        self.nb_vlans      = Vlans(ctx.vlans)
        self.nb_devices    = Devices(ctx.devices)
        self.nb_interfaces = Interfaces(ctx.interfaces)

        self.interface_conditions = {}
        for hostname, device_interfaces in self.nb_interfaces.all.items():
            for ifname, interface in device_interfaces.items():
                self.interface_conditions.setdefault(hostname, {})[ifname] = []


    def check_wifi_tag_consistency(self):
        wifi_o1_cplane_vid = self.nb_vlans.with_tags(Slug.Tag.WifiMgmtVlanOokayama1).vids
        wifi_o2_cplane_vid = self.nb_vlans.with_tags(Slug.Tag.WifiMgmtVlanOokayama2).vids
        wifi_s_cplane_vid  = self.nb_vlans.with_tags(Slug.Tag.WifiMgmtVlanSuzukake).vids
        wifi_o_dplane_vids = self.nb_vlans.with_tags(Slug.Tag.Wifi, Slug.Tag.VlanOokayama).vids
        wifi_s_dplane_vids = self.nb_vlans.with_tags(Slug.Tag.Wifi, Slug.Tag.Suzukake).vids

        for hostname, device_interfaces in self.nb_interfaces.all.items():
            device = self.nb_devices.all[hostname]

            cplane_vid, dplane_vids = None, None
            match device["wifi_area_group"]:
                case "O1":
                    cplane_vid, dplane_vids = wifi_o1_cplane_vid, set(wifi_o_dplane_vids)
                case "O2":
                    cplane_vid, dplane_vids = wifi_o2_cplane_vid, set(wifi_o_dplane_vids)
                case "S":
                    cplane_vid, dplane_vids = wifi_s_cplane_vid, set(wifi_s_dplane_vids)

            for ifname, interface in device_interfaces.items():
                current = InterfaceState(interface)
                condition = InterfaceCondition("Wi-Fi Tag Violation")

                ## skip if the interface is not for AP
                current.has("is_to_ap") or continue

                ## must be 'tagged' mode
                condition.is_tagged_vlan_mode = CV(True, Cond.IS)

                ## must have all D-Plane VLANs
                condition.tagged_vids = CV(dplane_vids, Cond.INCLUDE)

                ## must be C-Plane VLAN
                condition.untagged_vid = CV(cplane_vid, Cond.IS)

                self.interface_conditions[hostname][ifname].append(condition)


    def check_hosting_tag_consistency(self):
        hosting_vids = self.nb_vlans.with_tags(Slug.Tag.Hosting).vids

        for hostname, device_interfaces in self.nb_interfaces.all.items():
            for ifname, interface in device_interfaces.items():
                current = InterfaceState(interface)
                condition = InterfaceCondition("Hosting Tag Violation")

                ## skip if the interface is not for hosting
                current.has_tag(Slug.Tag.Hosting) or continue

                ## must be 'tagged' mode
                condition.is_tagged_vlan_mode = CV(True, Cond.IS)

                ## must have all hosting VLANs
                condition.tagged_vids = CV(hosting_vids, Cond.INCLUDE)

                self.interface_conditions[hostname][ifname].append(condition)


    def check_vlan_group(self):
        titanet_vids = self.nb_vlans.with_groups(Slug.VLANGroup.Titanet).vids

        for hostname, device_interfaces in self.nb_interfaces.all.items():
            ## skip if the device is not Core SW or Edge SW
            self.nb_devices[hostname]["role"] in [ Slug.Role.CoreSW, Slug.Role.EdgeSW ] or continue


            for ifname, interface in device_interfaces.items():
                condition = InterfaceCondition("VLAN Group Violation")

                ## must be included in the Titanet VLAN group
                condition.tagged_vids  = CV(titanet_vids, Cond.INCLUDED)
                condition.untagged_vid = CV(titanet_vids, Cond.INCLUDED)

                self.interface_conditions[hostname][ifname].append(condition)

