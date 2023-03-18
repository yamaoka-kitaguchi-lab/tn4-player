from copy import deepcopy
from functools import reduce
from pprint import pprint
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


    def __build_desired(self, current, condition):
        is_ok = Cond.CONFLICT not in [ condition.is_enabled.condition,
                                       condition.description.condition,
                                       condition.tags.condition,
                                       condition.interface_mode.condition,
                                       condition.tagged_oids.condition,
                                       condition.untagged_oid.condition, ]
        if not is_ok:
            return None, is_ok

        desired = deepcopy(current)

        desired.is_enabled     = condition.is_enabled.to_value(current.is_enabled, value_type=bool)
        desired.description    = condition.description.to_value(current.description, value_type=str)
        desired.tags           = condition.tags.to_value(current.tags, default=[])
        desired.interface_mode = condition.interface_mode.to_value(current.interface_mode, value_type=str)
        desired.tagged_oids    = condition.tagged_oids.to_value(current.tagged_oids)
        desired.untagged_oid   = condition.untagged_oid.to_value(current.untagged_oid, value_type=int)

        return desired, is_ok


    def __list_interface_violations(self, current, conditions):
        arguments = []

        for condition in conditions:
            is_ok = condition.is_enabled.is_satisfied_by(current.is_enabled) \
                and condition.description.is_satisfied_by(current.description) \
                and condition.tags.is_satisfied_by(current.tags) \
                and condition.interface_mode.is_satisfied_by(current.interface_mode) \
                and condition.tagged_oids.is_satisfied_by(current.tagged_oids) \
                and condition.untagged_oid.is_satisfied_by(current.untagged_oid)

            if not is_ok:
                arguments.append(condition.argument)

        return arguments


    def summarize(self):
        device_karte    = Karte(karte_type=KarteType.DEVICE)
        interface_karte = Karte(karte_type=KarteType.INTERFACE)

        has_annotation = lambda h, i: h in self.interface_annotations and i in self.interface_annotations[h]
        has_condition  = lambda h, i: h in self.interface_conditions and i in self.interface_conditions[h]

        for hostname, device_interfaces in self.nb_interfaces.all.items():

            if len(self.device_annotations[hostname]) > 0:
                device_karte.add(Assessment(
                    category=Category.WARN,
                    keys=[hostname],
                    current=DeviceState(self.nb_devices.all[hostname]),
                    desired=None,
                    arguments=None,
                    annotations=self.device_annotations[hostname],
                ))

            for ifname, interface in device_interfaces.items():

                if not has_condition(hostname, ifname):
                    continue

                conditions = self.interface_conditions[hostname][ifname]

                if len(conditions) == 0:
                    continue

                current   = InterfaceState(self.nb_interfaces.all[hostname][ifname])
                arguments = self.__list_interface_violations(current, conditions)

                condition   = reduce(operator.add, conditions)
                desired, ok = self.__build_desired(current, condition)

                category    = Category.UPDATE
                annotations = None
                if has_annotation(hostname, ifname):
                    annotations = self.interface_annotations[hostname][ifname]

                if not ok:
                    category    = Category.WARN
                    annotations = [ Annotation("CONFLICTED!") ]

                if not current.is_equal(desired) or len(annotations) > 0:
                    interface_karte.add(Assessment(
                        category=category,
                        keys=[hostname, ifname],
                        current=current,
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
                condition.tagged_oids    = CV(None, Cond.IS, priority=2)
                condition.untagged_oid   = CV(None, Cond.IS, priority=2)

                self.interface_conditions[hostname][ifname].append(condition)


    def check_wifi_tag_consistency(self):
        wifi_o1_cplane_oid = self.nb_vlans.with_tags(Slug.Tag.WifiMgmtVlanOokayama1).oids
        wifi_o2_cplane_oid = self.nb_vlans.with_tags(Slug.Tag.WifiMgmtVlanOokayama2).oids
        wifi_s_cplane_oid  = self.nb_vlans.with_tags(Slug.Tag.WifiMgmtVlanSuzukake).oids
        wifi_o_dplane_oids = self.nb_vlans.with_tags(Slug.Tag.Wifi, Slug.Tag.VlanOokayama).oids
        wifi_s_dplane_oids = self.nb_vlans.with_tags(Slug.Tag.Wifi, Slug.Tag.VlanSuzukake).oids

        for hostname, device_interfaces in self.nb_interfaces.all.items():

            ## skip if the device is not Core SW or Edge SW
            if self.nb_devices.all[hostname]["role"] not in [ Slug.Role.CoreSW, Slug.Role.EdgeSW ]:
                continue

            device = self.nb_devices.all[hostname]

            cplane_oid, dplane_oids = None, None
            match device["wifi_area_group"]:
                case "O1":
                    cplane_oid, dplane_oids = wifi_o1_cplane_oid, set(wifi_o_dplane_oids)
                case "O2":
                    cplane_oid, dplane_oids = wifi_o2_cplane_oid, set(wifi_o_dplane_oids)
                case "S":
                    cplane_oid, dplane_oids = wifi_s_cplane_oid, set(wifi_s_dplane_oids)

            for ifname, interface in device_interfaces.items():
                current = InterfaceState(interface)
                condition = InterfaceCondition("tag violation (Wi-Fi)")

                ## skip if the interface is not for AP
                if not current.has("is_to_ap"):
                    continue

                ## must be 'tagged' mode
                condition.interface_mode = CV("tagged", Cond.IS)

                ## must have all D-Plane VLANs
                condition.tagged_oids = CV(dplane_oids, Cond.INCLUDE)

                ## must be C-Plane VLAN
                condition.untagged_oid = CV(cplane_oid, Cond.IS)

                self.interface_conditions[hostname][ifname].append(condition)


    def check_hosting_tag_consistency(self):
        hosting_oids = self.nb_vlans.with_tags(Slug.Tag.Hosting).oids

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
                condition.tagged_oids = CV(hosting_oids, Cond.INCLUDE)

                self.interface_conditions[hostname][ifname].append(condition)


    def check_vlan_group_consistency(self):
        titanet_oids = self.nb_vlans.with_groups(Slug.VLANGroup.Titanet).oids
        titanet_oids.append(None)

        for hostname, device_interfaces in self.nb_interfaces.all.items():

            ## skip if the device is not Core SW or Edge SW
            if self.nb_devices.all[hostname]["role"] not in [ Slug.Role.CoreSW, Slug.Role.EdgeSW ]:
                continue

            for ifname, interface in device_interfaces.items():
                condition = InterfaceCondition("VLAN group violation", manual_repair=True)

                ## must be included in the VLAN group "Titanet"
                condition.tagged_oids  = CV(titanet_oids, Cond.INCLUDED)
                condition.untagged_oid = CV(titanet_oids, Cond.INCLUDED)

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
                if len(current.tagged_oids) == 0 and untagged_oid == None:
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
        uplink_oids = {}
        edges = set()

        ## collect all active VLANs of each edge
        for hostname, device_interfaces in self.nb_interfaces.all.items():
            if self.nb_devices.all[hostname]["role"] != Slug.Role.EdgeSW:
                continue

            uplink_oids[hostname] = set()

            for _, interface in device_interfaces.items():
                current = InterfaceState(interface)

                if current.tagged_oids is not None:
                    uplink_oids[hostname] |= set(current.tagged_oids)

                if current.untagged_oid is not None:
                    uplink_oids[hostname] |= { current.untagged_oid }

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

                if edgename not in uplink_oids:
                    continue  # neglected edges

                ## pass only in-used VLANs
                condition.is_enabled     = CV(True, Cond.IS)
                condition.interface_mode = CV("tagged", Cond.IS)
                condition.tagged_oids    = CV(uplink_oids[edgename], Cond.IS)
                condition.untagged_oid   = CV(None, Cond.IS)

                self.interface_conditions[hostname][ifname].append(condition)

        ## edges registered in NB but not appeared in cores' downlinks
        neglected_edges = set(uplink_oids.keys()) - edges
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
                condition.tagged_oids    = CV(desired.tagged_oids, Cond.IS, priority=20)
                condition.untagged_oid   = CV(desired.untagged_oid, Cond.IS, priority=20)

