from copy import deepcopy
from functools import reduce
import operator

from tn4.netbox.slug import Slug
from tn4.doctor.cv import Condition as Cond
from tn4.doctor.cv import ConditionalValue as CV
from tn4.doctor.base import Base, Vlans, Devices, Interfaces
from tn4.doctor.state import DeviceState, InterfaceState
from tn4.doctor.karte import InterfaceCondition, Category, Assessment, Annotation, Karte, KarteType


class Diagnose(Base):
    def __init__(self, ctx):
        self.nb_vlans      = Vlans(ctx.vlans)
        self.nb_devices    = Devices(ctx.inventory_devices)
        self.nb_interfaces = Interfaces(ctx.interfaces)

        self.device_annotations = {}
        self.interface_annotations = {}
        self.interface_conditions = {}

        for hostname, device_interfaces in self.nb_interfaces.all.items():
            self.device_annotations[hostname] = []
            for ifname, interface in device_interfaces.items():
                self.interface_conditions.setdefault(hostname, {})[ifname] = []
                self.interface_annotations.setdefault(hostname, {})[ifname] = []


    def __interface_condition_to_desired_state(self, hostname, ifname, condition):
        is_ok = Cond.CONFLICT in [ condition.is_enabled.condition,
                                   condition.description.condition,
                                   condition.tags.condition,
                                   condition.is_tagged_vlan_mode.condition,
                                   condition.tagged_vids.condition,
                                   condition.untagged_vid.condition, ]
        if not is_ok:
            return None, is_ok

        desired = InterfaceState(self.nb_interfaces.all[hostname][ifname])
        desired.is_enabled          = condition.is_enabled.value
        desired.description         = condition.description.value
        desired.tags                = condition.tags.value
        desired.is_tagged_vlan_mode = condition.is_tagged_vlan_mode.value
        desired.tagged_vids         = condition.tagged_vids.value
        desired.untagged_vid        = condition.untagged_vid.value

        return desired, is_ok


    def full_check(self):
        device_karte    = Karte(karte_type=KarteType.DEVICE)
        interface_karte = Karte(karte_type=KarteType.INTERFACE)

        has_annotation = lambda h, i: h in self.interface_annotations and i in self.interface_annotations[h]
        has_condition  = lambda h, i: h in self.interface_conditions and i in self.interface_conditions[h]

        for hostname, device_interfaces in self.nb_interfaces.all.items():

            if hostname in self.device_annotations:
                device_karte.add(Assessment(
                    category=Category.WARN,
                    keys=[hostname],
                    current=DeviceState(self.nb_devices.all[hostname]),
                    desired=None,
                    arguments=None,
                    annotations=self.device_annotations[hostname],
                ))

            for ifname, interface in device_interfaces.items():
                annotations = None
                if has_annotation(hostname, ifname):
                    annotations = self.interface_annotations[hostname][ifname]

                if not has_condition(hostname, ifname):
                    continue

                conditions = self.interface_conditions[hostname][ifname]

                if len(conditions) == 0:
                    continue

                condition = reduce(operator.add, conditions)
                desired, ok = self.__interface_condition_to_desired_state(hostname, ifname, condition)

                category = Category.UPDATE
                annotations = self.device_annotations[hostname]

                if not ok:
                    category = Category.WARN
                    annotations = [ "invalid condition" ]

                arguments = condition.argument
                interface_karte.add(Assessment(
                    category=category,
                    keys=[hostname, ifname],
                    current=InterfaceState(self.nb_interfaces.all[hostname][ifname]),
                    desired=desired,
                    arguments=arguments,
                    annotations=annotations,
                ))

        return device_karte, interface_karte


    def check_tag_to_tag_consistency(self):
        for hostname, device_interfaces in self.nb_interfaces.all.items():

            ## skip if the device is not Core SW or Edge SW
            if self.nb_devices.all[hostname]["role"] not in [ Slug.Role.CoreSW, Slug.Role.EdgeSW ]:
                continue

            for ifname, interface in device_interfaces.items():
                current = InterfaceState(interface)

                if Slug.Tag.Keep in current.tags and Slug.Tag.Obsoleted in current.tags:
                    annotation = Annotation("tag contradiction (Keep/Obsoleted)")
                    self.interface_annotations[hostname][ifname].append(annotation)


    def check_keep_tag_consistency(self):
        for hostname, device_interfaces in self.nb_interfaces.all.items():

            ## skip if the device is not Core SW or Edge SW
            if self.nb_devices.all[hostname]["role"] not in [ Slug.Role.CoreSW, Slug.Role.EdgeSW ]:
                continue

            for ifname, interface in device_interfaces.items():
                current = InterfaceState(interface)
                condition = InterfaceCondition("tag operation (Keep)")

                ## skip if the interface does not have 'keep' tag
                if not current.has_tag(Slug.Tag.Keep):
                    continue

                ## must be disabled
                condition.is_enabled = CV(False, Cond.IS, priority=1)

                ## must not have 'keep' tag
                condition.tags = CV(Slug.Tag.Keep, Cond.EXCLUDE, priority=1)

                self.interface_conditions[hostname][ifname].append(condition)


    def check_obsoleted_tag_consistency(self):
        for hostname, device_interfaces in self.nb_interfaces.all.items():

            ## skip if the device is not Core SW or Edge SW
            if self.nb_devices.all[hostname]["role"] not in [ Slug.Role.CoreSW, Slug.Role.EdgeSW ]:
                continue

            for ifname, interface in device_interfaces.items():
                current = InterfaceState(interface)
                condition = InterfaceCondition("tag operation (Obsoleted)")

                ## skip if the interface does not have 'obsoleted' tag
                if not current.has_tag(Slug.Tag.Obsoleted):
                    continue

                ## must be cleared
                condition.is_enabled     = CV(False, Cond.IS, priority=2)
                condition.description    = CV(None, Cond.IS, priority=2)
                condition.tags           = CV(None, Cond.IS, priority=2)
                condition.interface_mode = CV(None, Cond.IS, priority=2)
                condition.tagged_vids    = CV(None, Cond.IS, priority=2)
                condition.untagged_vid   = CV(None, Cond.IS, priority=2)

                self.interface_conditions[hostname][ifname].append(condition)


    def check_wifi_tag_consistency(self):
        wifi_o1_cplane_vid = self.nb_vlans.with_tags(Slug.Tag.WifiMgmtVlanOokayama1).vids
        wifi_o2_cplane_vid = self.nb_vlans.with_tags(Slug.Tag.WifiMgmtVlanOokayama2).vids
        wifi_s_cplane_vid  = self.nb_vlans.with_tags(Slug.Tag.WifiMgmtVlanSuzukake).vids
        wifi_o_dplane_vids = self.nb_vlans.with_tags(Slug.Tag.Wifi, Slug.Tag.VlanOokayama).vids
        wifi_s_dplane_vids = self.nb_vlans.with_tags(Slug.Tag.Wifi, Slug.Tag.VlanSuzukake).vids

        for hostname, device_interfaces in self.nb_interfaces.all.items():

            ## skip if the device is not Core SW or Edge SW
            if self.nb_devices.all[hostname]["role"] not in [ Slug.Role.CoreSW, Slug.Role.EdgeSW ]:
                continue

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
                if not current.has("is_to_ap"):
                    continue

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

            ## skip if the device is not Core SW or Edge SW
            if self.nb_devices.all[hostname]["role"] not in [ Slug.Role.CoreSW, Slug.Role.EdgeSW ]:
                continue

            for ifname, interface in device_interfaces.items():
                current = InterfaceState(interface)
                condition = InterfaceCondition("tag violation (Hosting)")

                ## skip if the interface is not for hosting
                if not current.has_tag(Slug.Tag.Hosting):
                    continue

                ## must be 'tagged' mode
                condition.interface_mode = CV("tagged", Cond.IS)

                ## must have all hosting VLANs
                condition.tagged_vids = CV(hosting_vids, Cond.INCLUDE)

                self.interface_conditions[hostname][ifname].append(condition)


    def check_vlan_group_consistency(self):
        titanet_vids = self.nb_vlans.with_groups(Slug.VLANGroup.Titanet).vids

        for hostname, device_interfaces in self.nb_interfaces.all.items():

            ## skip if the device is not Core SW or Edge SW
            if self.nb_devices.all[hostname]["role"] not in [ Slug.Role.CoreSW, Slug.Role.EdgeSW ]:
                continue

            for ifname, interface in device_interfaces.items():
                condition = InterfaceCondition("VLAN group violation", manual_repair=True)

                ## must be included in the Titanet VLAN group
                condition.tagged_vids  = CV(titanet_vids, Cond.INCLUDED)
                condition.untagged_vid = CV(titanet_vids, Cond.INCLUDED)

                self.interface_conditions[hostname][ifname].append(condition)


    def check_interface_mode_consistency(self):
        for hostname, device_interfaces in self.nb_interfaces.all.items():

            ## skip if the device is not Core SW or Edge SW
            if self.nb_devices.all[hostname]["role"] not in [ Slug.Role.CoreSW, Slug.Role.EdgeSW ]:
                continue

            for ifname, interface in device_interfaces.items():
                current = InterfaceState(interface)
                condition = InterfaceCondition("interface mode inconsistency")

                if current.interface_mode is None:
                    continue

                ## interface mode must be cleared if no VLANs are attached
                if len(current.tagged_vids) == 0 and untagged_vid == None:
                    condition.interface_mode = CV(None, Cond.IS)

                self.interface_conditions[hostname][ifname].append(condition)


    def check_and_remove_empty_irb(self):
        for hostname, device_interfaces in self.nb_interfaces.all.items():

            ## skip if the device is not Core SW or Edge SW
            if self.nb_devices.all[hostname]["role"] not in [ Slug.Role.CoreSW, Slug.Role.EdgeSW ]:
                continue

            for ifname, interface in device_interfaces.items():
                current = InterfaceState(interface)
                condition = InterfaceCondition("obsoleted interface")

                if ifname[:4] != "irb." or current.interface_mode is not None:
                    continue

                ## remove empty irb inteface from NetBox
                condition.remove_from_nb = CV(True, Cond.IS)


    def check_edge_core_consistency(self):
        uplink_vids = {}
        edges = set()

        ## collect all active VLANs of each edge
        for hostname, device_interfaces in self.nb_interfaces.all.items():
            if self.nb_devices.all[hostname]["role"] != Slug.Role.EdgeSW:
                continue

            uplink_vids[hostname] = set()

            for _, interface in device_interfaces.items():
                current = InterfaceState(interface)

                if current.tagged_vids is not None:
                    uplink_vids[hostname] |= set(current.tagged_vids)

                if current.untagged_vid is not None:
                    uplink_vids[hostname] |= { current.untagged_vid }

        for hostname, device_interfaces in self.nb_interfaces.all.items():
            if self.nb_devices.all[hostname]["role"] != Slug.Role.CoreSW:
                continue

            for ifname, interface in device_interfaces.items():
                current = InterfaceState(interface)
                condition = InterfaceCondition("uplink/downlink inconsistency")

                if not current.has_tag(Slug.Tag.CoreDownstream):
                    continue

                edgename = current.description
                edges.add(edgename)

                if edgename not in uplink_vids:
                    continue  # neglected edges

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
            if self.nb_devices.all[hostname]["role"] != Slug.Role.CoreSW:
                continue

            for ifname, interface in device_interfaces.items():
                current = InterfaceState(interface)

                if current.has_tag(Slug.Tag.CoreMaster):
                    desired_slave[ifname] = deepcopy(current)

                if current.has_tag(Slug.Tag.CoreOokayamaMaster):
                    desired_slave_o[ifname] = deepcopy(current)

                if current.has_tag(Slug.Tag.CoreSuzukakeMaster):
                    desired_slave_s[ifname] = deepcopy(current)

        for hostname, device_interfaces in self.nb_interfaces.all.items():
            if self.nb_devices.all[hostname]["role"] != Slug.Role.CoreSW:
                continue

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

                if desired is None:
                    continue

                condition = InterfaceCondition("master/slave inconsistency")

                ## copy interface settings but keep original tags
                condition.is_enabled     = CV(desired.is_enabled, Cond.IS, priority=20)
                condition.description    = CV(desired.description, Cond.IS, priority=20)
                condition.interface_mode = CV(desired.interface_mode, Cond.IS, priority=20)
                condition.tagged_vids    = CV(desired.tagged_vids, Cond.IS, priority=20)
                condition.untagged_vid   = CV(desired.untagged_vid, Cond.IS, priority=20)

