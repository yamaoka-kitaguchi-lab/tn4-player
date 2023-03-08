from copy import deepcopy

from tn4.netbox.slug import Slug
from tn4.nbck.base import Base, Vlans, Devices, Interfaces
from tn4.nbck.base import Condition as Cond
from tn4.nbck.base import ConditionalValue as CV
from tn4.nbck.state import InterfaceCondition
from tn4.nbck.state import DeviceState, InterfaceState
from tn4.nbck.state import NbckReport, ReportCategory


class Diagnose(Base):
    def __init__(self, ctx):
        self.nb_vlans      = Vlans(ctx.vlans)
        self.nb_devices    = Devices(ctx.devices)
        self.nb_interfaces = Interfaces(ctx.interfaces)

        self.device_annotations = {}
        self.interface_annotations = {}
        self.interface_conditions = {}

        for hostname, device_interfaces in self.nb_interfaces.all.items():
            self.device_annotations[hostname] = []
            for ifname, interface in device_interfaces.items():
                self.interface_conditions.setdefault(hostname, {})[ifname] = []
                self.interface_annotations.setdefault(hostname, {})[ifname] = []


    def check_among_tag_consistency(self):
        for hostname, device_interfaces in self.nb_interfaces.all.items():
            for ifname, interface in device_interfaces.items():
                current = InterfaceState(interface)

                if Slug.Tag.Keep in current.tags and Slug.Tag.Obsoleted in current.tags:
                    annotation = Annotation("tag contradiction (Keep/Obsoleted)")
                    self.interface_annotations[hostname][ifname].append(annotation)


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
        edges = set()

        ## collect all active VLANs of each edge
        for hostname, device_interfaces in self.nb_interfaces.all.items():
            self.nb_devices[hostname]["role"] == Slug.Role.EdgeSW or continue
            uplink_vids[hostname] = set()

            for _, interface in device_interfaces.items():
                current = InterfaceState(interface)
                uplink_vids[hostname] |= set(current.tagged_vids)
                uplink_vids[hostname] |= set(current.untagged_vid)

        for hostname, device_interfaces in self.nb_interfaces.all.items():
            self.nb_devices[hostname]["role"] == Slug.Role.CoreSW or continue

            for _, interface in device_interfaces.items():
                current = InterfaceState(interface)
                condition = InterfaceCondition("uplink/downlink inconsistency")

                current.has_tag(Slug.Tag.CoreDownstream) or continue
                edgename = current.description
                edges.add(edgename)

                ## pass only in-used VLANs
                condition.is_enabled     = CV(True, Cond.IS)
                condition.interface_mode = CV("tagged", Cond.IS)
                condition.tagged_vids    = CV(uplink_vids[edgename], Cond.IS)
                condition.untagged_vid   = CV(None, Cond.IS)

                self.interface_conditions[hostname][ifname].append(condition)

        ## edges registered in NB but not appeared in cores' downlinks
        neglected_edges = set(uplink_vids.keys()) - edges
        for edgename in neglected_edges:
            annotation = Annotation(f"neglected edge ({edgename})")
            self.device_annotations[edgename].append(annotation)


    def check_master_slave_tag_consistency(self):
        desired_slave = {}
        desired_slave_o = {}
        desired_slave_s = {}

        for hostname, device_interfaces in self.nb_interfaces.all.items():
            self.nb_devices[hostname]["role"] == Slug.Role.CoreSW or continue

            for ifname, interface in device_interfaces.items():
                current = InterfaceState(interface)

                if current.has_tag(Slug.Tag.CoreMaster):
                    desired_slave[ifname] = deepcopy(current)

                if current.has_tag(Slug.Tag.CoreOokayamaMaster):
                    desired_slave_o[ifname] = deepcopy(current)

                if current.has_tag(Slug.Tag.CoreSuzukakeMaster):
                    desired_slave_s[ifname] = deepcopy(current)

        for hostname, device_interfaces in self.nb_interfaces.all.items():
            self.nb_devices[hostname]["role"] == Slug.Role.CoreSW or continue

            for ifname, interface in device_interfaces.items():
                current = InterfaceState(interface)
                desired = None

                try:
                    if current.has_tag(Slug.Tag.CoreSlave):
                        desired = desired_slave[ifname]

                    if current.has_tag(Slug.Tag.CoreOokayamaSlave):
                        desired = desired_slave_o[ifname]

                    if current.has_tag(Slug.Tag.CoreSuzukakeSlave):
                        desired = desired_slave_s[ifname]

                except KeyError:
                    annotation = Annotation("'slave' specified but no 'master' found")
                    self.interface_annotations[hostname][ifname].append(annotation)
                    continue

                desired is not None or continue

                condition = InterfaceCondition("master/slave inconsistency", priority=20)

                ## copy interface settings but keep original tags
                condition.is_enabled     = CV(desired.is_enabled, Cond.IS)
                condition.description    = CV(desired.description, Cond.IS)
                condition.interface_mode = CV(desired.interface_mode, Cond.IS)
                condition.tagged_vids    = CV(desired.tagged_vids, Cond.IS)
                condition.untagged_vid   = CV(desired.untagged_vid, Cond.IS)


    def generate_nbck_report(self):
        device_reports    = []
        interface_reports = []

        has_annotation = lambda h, i: h in self.interface_annotations and i in self.interface_annotations[h]
        has_condition  = lambda h, i: h in self.interface_conditions and i in self.interface_conditions[h]

        for hostname, device_interfaces in self.nb_interfaces.all.items():

            if hostname in self.device_annotations:
                device_reports.append(NbckReport(
                    category=ReportCategory.WARN,
                    current=DeviceState(self.nb_devices.all[hostname]),
                    desired=None,
                    arguments=None,
                    annotations=self.device_annotations[hostname],
                ))

            for ifname, interface in device_interfaces.items():
                annotations = None
                if has_annotation(hostname, ifname):
                    annotations = self.interface_annotations[hostname][ifname]

                has_condition(hostname, ifname) or continue

                condition = sum(self.interface_conditions[hostname][ifname])

                interface_reports.append(NbckReport(
                    category=ReportCategory.WARN,
                    current=DeviceState(self.nb_devices.all[hostname]),
                    desired=None,
                    arguments=None,
                    annotations=self.device_annotations[hostname],
                ))


