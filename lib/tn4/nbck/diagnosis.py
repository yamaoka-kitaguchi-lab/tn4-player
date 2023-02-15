from tn4.netbox.slug import Slug
from tn4.nbck.base import Base, Vlans, Devices, Interfaces
from tn4.nbck.state import ConditionalValue as CV
from tn4.nbck.state import Condition as Cond
from tn4.nbck.state import InterfaceCondition
from tn4.nbck.state import DeviceState, InterfaceState
from tn4.nbck.state import NbckReport, ReportCategory


class Diagnosis(Base):
    def __init__(self, ctx):
        self.nb_vlans      = Vlans(ctx.vlans)
        self.nb_devices    = Devices(ctx.devices)
        self.nb_interfaces = Interfaces(ctx.interfaces)

        self.interface_conditions = {}
        for hostname, device_interfaces in self.nb_interfaces.all.items():
            for ifname, interface in device_interfaces.items():
                self.interface_conditions.setdefault(hostname, {})[ifname] = []


    def check_among_tag_consistency(self):
        for hostname, device_interfaces in self.nb_interfaces.all.items():
            for ifname, interface in device_interfaces.items():
                current = InterfaceState(interface)

                if Slug.Tag.Keep in current.tags and Slug.Tag.Obsoleted in current.tags:
                    condition = InterfaceCondition("tag contradiction (Keep/Obsoleted)", manual_repair=True)
                    self.interface_conditions[hostname][ifname].append(condition)


    def check_keep_tag_consistency(self):
        for hostname, device_interfaces in self.nb_interfaces.all.items():
            for ifname, interface in device_interfaces.items():
                current = InterfaceState(interface)
                condition = InterfaceCondition("tag operation (Keep)", priority=10)

                ## skip if the interface does not have 'keep' tag
                current.has_tag(Slug.Tag.Keep) or continue

                ## must be disabled
                condition.is_enabled = CV(False, Cond.IS)

                ## must not have 'keep' tag
                condition.tags = CV(Slug.Tag.Keep, Cond.EXCLUDE)

                self.interface_conditions[hostname][ifname].append(condition)


    def check_obsoleted_tag_consistency(self):
        for hostname, device_interfaces in self.nb_interfaces.all.items():
            for ifname, interface in device_interfaces.items():
                current = InterfaceState(interface)
                condition = InterfaceCondition("tag operation (Obsoleted)", priority=11)

                ## skip if the interface does not have 'obsoleted' tag
                current.has_tag(Slug.Tag.Obsoleted) or continue

                ## must be cleared
                condition.is_enabled = CV(False, Cond.IS)
                condition.description = CV(None, Cond.IS)
                condition.tags = CV(None, Cond.IS)
                condition.interface_mode = CV(None, Cond.IS)
                condition.tagged_vids = CV(None, Cond.IS)
                condition.untagged_vid = CV(None, Cond.IS)

                self.interface_conditions[hostname][ifname].append(condition)


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
                condition = InterfaceCondition("tag violation (Wi-Fi)")

                ## skip if the interface is not for AP
                current.has("is_to_ap") or continue

                ## must be 'tagged' mode
                condition.interface_mode = CV("tagged", Cond.IS)

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
                condition = InterfaceCondition("tag violation (Hosting)")

                ## skip if the interface is not for hosting
                current.has_tag(Slug.Tag.Hosting) or continue

                ## must be 'tagged' mode
                condition.interface_mode = CV("tagged", Cond.IS)

                ## must have all hosting VLANs
                condition.tagged_vids = CV(hosting_vids, Cond.INCLUDE)

                self.interface_conditions[hostname][ifname].append(condition)


    def check_vlan_group_consistency(self):
        titanet_vids = self.nb_vlans.with_groups(Slug.VLANGroup.Titanet).vids

        for hostname, device_interfaces in self.nb_interfaces.all.items():
            ## skip if the device is not Core SW or Edge SW
            self.nb_devices[hostname]["role"] in [ Slug.Role.CoreSW, Slug.Role.EdgeSW ] or continue

            for ifname, interface in device_interfaces.items():
                condition = InterfaceCondition("VLAN group violation", manual_repair=True)

                ## must be included in the Titanet VLAN group
                condition.tagged_vids  = CV(titanet_vids, Cond.INCLUDED)
                condition.untagged_vid = CV(titanet_vids, Cond.INCLUDED)

                self.interface_conditions[hostname][ifname].append(condition)


    def check_interface_mode_consistency(self):
        for hostname, device_interfaces in self.nb_interfaces.all.items():
            for ifname, interface in device_interfaces.items():
                current = InterfaceState(interface)
                condition = InterfaceCondition("interface mode inconsistency")

                current.interface_mode != None or continue

                ## interface mode must be cleared if no VLANs are attached
                if len(current.tagged_vids) == 0 and untagged_vid == None:
                    condition.interface_mode = CV(None, Cond.IS)

                self.interface_conditions[hostname][ifname].append(condition)


    def check_and_remove_empty_irb(self):
        for hostname, device_interfaces in self.nb_interfaces.all.items():
            for ifname, interface in device_interfaces.items():
                current = InterfaceState(interface)
                condition = InterfaceCondition("obsoleted interface")

                ifname[:4] == "irb." and current.interface_mode is None or continue

                ## remove empty irb inteface from NetBox
                condition.remove_from_nb = CV(True, Cond.IS)


    def check_edge_core_consistency(self):
        uplink_vids = {}

        ## collect all active VLANs of each edge
        for hostname, device_interfaces in self.nb_interfaces.all.items():
            self.nb_devices[hostname]["role"] == Slug.Role.EdgeSW or continue
            uplink_vids[hostname] = set()

            for _, interface in device_interfaces.items():
                current = InterfaceState(interface)
                uplink_vids[hostname] |= set(current.tagged_vids)
                uplink_vids[hostname] |= set(current.untagged_vid)





    def check_master_slave_tag_consistency(self):
        pass

