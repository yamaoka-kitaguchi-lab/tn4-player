from copy import deepcopy
from functools import reduce
from pprint import pprint
import operator

from tn4.netbox.slug import Slug
from tn4.doctor.cv import Condition as Cond
from tn4.doctor.cv import ConditionalValue as CV
from tn4.doctor.base import Vlans, Devices, Interfaces
from tn4.doctor.state import DeviceState, InterfaceState
from tn4.doctor.karte import InterfaceCondition, KarteType, Karte, Annotation


class Diagnose():
    def __init__(self, ctx):
        self.nb_vlans      = Vlans(ctx.vlans)
        self.nb_devices    = Devices(ctx.devices_by_hostname)
        self.nb_interfaces = Interfaces(ctx.interfaces)

        self.device_annotations = {}
        self.interface_annotations = {}
        self.interface_conditions = {}
        self.is_manual_repair_interface = {}  # set true to skip remaining consistency check

        for hostname, device_interfaces in self.nb_interfaces.all.items():
            self.device_annotations[hostname] = []
            for ifname, interface in device_interfaces.items():
                self.interface_conditions.setdefault(hostname, {})[ifname] = []
                self.interface_annotations.setdefault(hostname, {})[ifname] = []
                self.is_manual_repair_interface.setdefault(hostname, {})[ifname] = False


    def __build_desired(self, current, condition):
        is_ok = Cond.CONFLICT not in [ condition.is_enabled.condition,
                                       condition.description.condition,
                                       condition.tags.condition,
                                       condition.interface_mode.condition,
                                       condition.tagged_oids.condition,
                                       condition.untagged_oid.condition,
                                       condition.delete.condition, ]

        if not is_ok:
            return None, False

        desired = deepcopy(current)

        desired.is_enabled     = condition.is_enabled.to_value(current.is_enabled, value_type=bool)
        desired.description    = condition.description.to_value(current.description, value_type=str)
        desired.tags           = condition.tags.to_value(current.tags, default=[])
        desired.interface_mode = condition.interface_mode.to_value(current.interface_mode, value_type=str)
        desired.tagged_oids    = condition.tagged_oids.to_value(current.tagged_oids)
        desired.untagged_oid   = condition.untagged_oid.to_value(current.untagged_oid, value_type=int)
        desired.delete         = condition.delete.to_value(current.delete, value_type=bool)

        return desired, True


    def __list_interface_violations(self, current, conditions):
        arguments = []

        for condition in conditions:
            is_ok = condition.is_enabled.is_satisfied_by(current.is_enabled) \
                and condition.description.is_satisfied_by(current.description) \
                and condition.tags.is_satisfied_by(current.tags) \
                and condition.interface_mode.is_satisfied_by(current.interface_mode) \
                and condition.tagged_oids.is_satisfied_by(current.tagged_oids) \
                and condition.untagged_oid.is_satisfied_by(current.untagged_oid) \
                and condition.delete.is_satisfied_by(current.delete)

            if not is_ok:
                arguments.append(condition.argument)  # violation

        return arguments


    def summarize(self):
        kartes    = []

        has_annotation = lambda h, i: h in self.interface_annotations and i in self.interface_annotations[h]
        has_condition  = lambda h, i: h in self.interface_conditions and i in self.interface_conditions[h]

        for hostname, device_interfaces in self.nb_interfaces.all.items():

            if len(self.device_annotations[hostname]) > 0:
                kartes.append(Karte(
                    karte_type=KarteType.WARN,
                    hostname=hostname,
                    #current=DeviceState(self.nb_devices.all[hostname]),
                    current=None,
                    desired=None,
                    arguments=None,
                    annotations=self.device_annotations[hostname],
                ))

            for ifname, interface in device_interfaces.items():

                if not has_condition(hostname, ifname):
                    continue

                current    = InterfaceState(self.nb_interfaces.all[hostname][ifname])
                conditions = self.interface_conditions[hostname][ifname]

                if len(conditions) == 0:
                    if has_annotation(hostname, ifname):
                        kartes.append(Karte(
                            karte_type=karte_type,
                            hostname=hostname,
                            ifname=ifname,
                            current=current,
                            desired=None,
                            arguments=None,
                            annotations=self.interface_annotations[hostname][ifname],
                        ))

                    continue

                arguments = self.__list_interface_violations(current, conditions)

                condition   = reduce(operator.add, conditions)
                desired, ok = self.__build_desired(current, condition)
                delete      = False
                skip        = False

                if self.is_manual_repair_interface[hostname][ifname]:
                    desired = None
                    self.interface_annotations[hostname][ifname].append(
                        Annotation("Manual repair needed", severity=3)
                    )

                if ok:
                    karte_type  = KarteType.UPDATE
                    delete      = desired.delete
                    annotations = []

                    if has_annotation(hostname, ifname):
                        annotations = self.interface_annotations[hostname][ifname]

                    if current.is_equal(desired):
                        skip = True
                    elif len(arguments) == 0:
                        arguments = [ "Auto-removed out-of-use entries" ]

                    skip &= len(annotations) == 0

                else:
                    karte_type  = KarteType.WARN
                    annotations = [
                        Annotation("CV calculation failed", severity=3),
                    ]

                if not skip:
                    kartes.append(Karte(
                        karte_type=karte_type,
                        hostname=hostname,
                        ifname=ifname,
                        current=current,
                        desired=desired,
                        arguments=arguments,
                        annotations=annotations,
                        delete=delete,
                    ))

        return kartes


    def check_exclusive_tag_conflict(self):
        exclusive_tags = set([
            Slug.Tag.CoreMaster, Slug.Tag.CoreOokayamaMaster, Slug.Tag.CoreSuzukakeMaster,
            Slug.Tag.CoreBackup, Slug.Tag.CoreOokayamaBackup, Slug.Tag.CoreSuzukakeBackup,
            Slug.Tag.Wifi, Slug.Tag.Hosting,
        ])

        for hostname, device_interfaces in self.nb_interfaces.all.items():

            ## skip if the device is not Core SW or Edge SW
            if self.nb_devices.all[hostname]["role"] not in [ Slug.Role.CoreSW, Slug.Role.EdgeSW ]:
                continue

            for ifname, interface in device_interfaces.items():
                current       = InterfaceState(interface)
                current_tags  = set(current.tags)
                attached_tags = exclusive_tags & current_tags

                if len(attached_tags) > 1:
                    self.interface_annotations[hostname][ifname].extend([
                        Annotation(message=f"MCLAG/Wi-Fi/Hosting tags are exclusive", severity=3),
                        Annotation(message="Manual repair needed"),
                    ])
                    self.is_manual_repair_interface[hostname][ifname] = True


    def check_and_clear_incomplete_interfaces(self):
        has_empty_vlan = lambda s: s.tagged_oids is None and s.untagged_oid is None
        has_empty_desc = lambda s: s.description in [ None, '' ]

        for hostname, device_interfaces in self.nb_interfaces.all.items():

            ## skip if the device is not Core SW or Edge SW
            if self.nb_devices.all[hostname]["role"] not in [ Slug.Role.CoreSW, Slug.Role.EdgeSW ]:
                continue

            for ifname, interface in device_interfaces.items():
                current = InterfaceState(interface)
                condition = InterfaceCondition("Incomplete interface")

                ## skip if the interface needs manual repair
                if self.is_manual_repair_interface[hostname][ifname]:
                    continue

                ## skip if the interface has 'Keep' tag
                if current.has_tag(Slug.Tag.Keep):
                    continue

                ## skip if the interface has 'Wi-Fi' tag
                if current.has_tag(Slug.Tag.Wifi):
                    continue

                ## skip if the interface has 'Hosting' tag
                if current.has_tag(Slug.Tag.Hosting):
                    continue

                ## skip if the interface is a LAG child
                if current.is_lag_member:
                    continue

                is_to_reset  = current.interface_mode is None and current.is_enabled
                is_to_reset |= current.interface_mode in ["tagged", "access"] and has_empty_vlan(current)
                is_to_reset |= current.has_tag(Slug.Tag.Obsoleted)

                if not is_to_reset:
                    continue

                condition.is_enabled     = CV(False, Cond.IS)
                condition.description    = CV(None, Cond.IS)
                condition.tags           = CV(None, Cond.IS)
                condition.interface_mode = CV(None, Cond.IS)
                condition.tagged_oids    = CV(None, Cond.IS)
                condition.untagged_oid   = CV(None, Cond.IS)

                self.interface_conditions[hostname][ifname].append(condition)


    def check_and_clear_obsoleted_interfaces(self):
        has_empty_vlan = lambda s: s.tagged_oids is None and s.untagged_oid is None
        has_empty_desc = lambda s: s.description in [ None, '' ]

        for hostname, device_interfaces in self.nb_interfaces.all.items():

            ## skip if the device is not Core SW or Edge SW
            if self.nb_devices.all[hostname]["role"] not in [ Slug.Role.CoreSW, Slug.Role.EdgeSW ]:
                continue

            for ifname, interface in device_interfaces.items():
                current = InterfaceState(interface)
                condition = InterfaceCondition("Termination by Obsoleted tag")

                ## skip if the interface needs manual repair
                if self.is_manual_repair_interface[hostname][ifname]:
                    continue

                ## skip if the interface is a LAG child
                if current.is_lag_member:
                    continue

                if not current.has_tag(Slug.Tag.Obsoleted):
                    continue

                condition.is_enabled     = CV(False, Cond.IS, priority=999)
                condition.description    = CV(None, Cond.IS, priority=999)
                condition.tags           = CV(None, Cond.IS, priority=999)
                condition.interface_mode = CV(None, Cond.IS, priority=999)
                condition.tagged_oids    = CV(None, Cond.IS, priority=999)
                condition.untagged_oid   = CV(None, Cond.IS, priority=999)

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
                    cplane_oid, dplane_oids = wifi_o1_cplane_oid, wifi_o_dplane_oids
                case "O2":
                    cplane_oid, dplane_oids = wifi_o2_cplane_oid, wifi_o_dplane_oids
                case "S":
                    cplane_oid, dplane_oids = wifi_s_cplane_oid,  wifi_s_dplane_oids

            for ifname, interface in device_interfaces.items():
                current = InterfaceState(interface)
                condition = InterfaceCondition("By Wi-Fi tag")

                ## skip if the interface needs manual repair
                if self.is_manual_repair_interface[hostname][ifname]:
                    continue

                ## skip if the interface is not for AP
                if not current.has("is_to_ap"):
                    continue

                ## must be enabled
                condition.is_enabled = CV(True, Cond.IS, priority=900)

                ## must be 'tagged' mode
                condition.interface_mode = CV("tagged", Cond.IS, priority=900)

                ## must have all D-Plane VLANs
                condition.tagged_oids = CV([*dplane_oids, *cplane_oid], Cond.IS, priority=900)
                #condition.tagged_oids = CV(dplane_oids, Cond.IS, priority=900)

                ## must be C-Plane VLAN
                condition.untagged_oid = CV(cplane_oid, Cond.IS, priority=900)

                self.interface_conditions[hostname][ifname].append(condition)


    def check_hosting_tag_consistency(self):
        hosting_oids = self.nb_vlans.with_tags(Slug.Tag.Hosting).oids

        for hostname, device_interfaces in self.nb_interfaces.all.items():

            ## skip if the device is not Edge SW
            if self.nb_devices.all[hostname]["role"] != Slug.Role.EdgeSW:
                continue

            for ifname, interface in device_interfaces.items():
                current = InterfaceState(interface)
                condition = InterfaceCondition("By Hosting tag")

                ## skip if the interface needs manual repair
                if self.is_manual_repair_interface[hostname][ifname]:
                    continue

                ## skip if the interface is not for hosting
                if not current.has_tag(Slug.Tag.Hosting):
                    continue

                ## must be enabled
                condition.is_enabled = CV(True, Cond.IS, priority=900)

                ## must be 'tagged' mode
                condition.interface_mode = CV("tagged", Cond.IS, priority=900)

                ## must have all hosting VLANs
                condition.tagged_oids = CV(hosting_oids, Cond.IS, priority=900)

                ## must not have untagged VLAN
                condition.untagged_oid = CV(None, Cond.IS, priority=900)

                self.interface_conditions[hostname][ifname].append(condition)


    def check_vlan_group_consistency(self):
        titanet_oids = self.nb_vlans.with_groups(Slug.VLANGroup.Titanet).oids
        titanet_oids.append(None)

        for hostname, device_interfaces in self.nb_interfaces.all.items():

            ## skip if the device is not Core SW or Edge SW
            if self.nb_devices.all[hostname]["role"] not in [ Slug.Role.CoreSW, Slug.Role.EdgeSW ]:
                continue

            for ifname, interface in device_interfaces.items():
                condition = InterfaceCondition("Outside of Titanet VLANs")

                ## skip if the interface needs manual repair
                if self.is_manual_repair_interface[hostname][ifname]:
                    continue

                ## must be included in the VLAN group "Titanet"
                condition.tagged_oids  = CV(titanet_oids, Cond.INCLUDED)
                condition.untagged_oid = CV(titanet_oids, Cond.INCLUDED)

                self.interface_conditions[hostname][ifname].append(condition)


    def check_and_remove_empty_irb(self):
        has_vlan = lambda s: s.tagged_oids is not None or s.untagged_oid is not None

        for hostname, device_interfaces in self.nb_interfaces.all.items():

            ## skip if the device is not Core SW or Edge SW
            if self.nb_devices.all[hostname]["role"] not in [ Slug.Role.CoreSW, Slug.Role.EdgeSW ]:
                continue

            for ifname, interface in device_interfaces.items():
                current = InterfaceState(interface)
                condition = InterfaceCondition("Auto-delete empty irb")

                ## skip if the interface needs manual repair
                if self.is_manual_repair_interface[hostname][ifname]:
                    continue

                ## skip if the interface has VLANs
                if ifname[:4] != "irb." or has_vlan(current):
                    continue

                ## remove empty or invalid irb inteface from NetBox
                condition.delete = CV(True, Cond.IS, priority=100)

                self.interface_conditions[hostname][ifname].append(condition)


    def check_edge_core_consistency(self):
        titanet_oids = set(self.nb_vlans.with_groups(Slug.VLANGroup.Titanet).oids)
        uplink_oids  = {}
        edges        = set()

        ## collect all active VLANs of desired edge state
        for hostname, device_interfaces in self.nb_interfaces.all.items():
            if self.nb_devices.all[hostname]["role"] != Slug.Role.EdgeSW:
                continue

            uplink_oids[hostname] = set()

            for ifname, interface in device_interfaces.items():
                current     = InterfaceState(interface)
                conditions  = self.interface_conditions[hostname][ifname]

                if len(conditions) > 0:
                    condition   = reduce(operator.add, conditions)
                    desired, ok = self.__build_desired(current, condition)

                    if ok:
                        tagged_oids  = desired.tagged_oids
                        untagged_oid = desired.untagged_oid
                    else:
                        continue

                else:
                    tagged_oids  = current.tagged_oids
                    untagged_oid = current.untagged_oid

                if tagged_oids is not None:
                    uplink_oids[hostname] |= set(tagged_oids)

                if untagged_oid is not None:
                    uplink_oids[hostname] |= { untagged_oid }

        for hostname, device_interfaces in self.nb_interfaces.all.items():
            if self.nb_devices.all[hostname]["role"] != Slug.Role.CoreSW:
                continue

            for ifname, interface in device_interfaces.items():
                current = InterfaceState(interface)
                condition = InterfaceCondition("Core/Edge consistency")

                ## skip if the interface needs manual repair
                if self.is_manual_repair_interface[hostname][ifname]:
                    continue

                if not current.has_tag(Slug.Tag.CoreDownstream):
                    continue

                edgename = current.description
                edges.add(edgename)

                if edgename not in uplink_oids:
                    continue  # neglected edges

                invalid_uplink_oids   = uplink_oids[edgename] - titanet_oids
                validated_uplink_oids = uplink_oids[edgename] - invalid_uplink_oids

                ## pass only in-used VLANs belonging the Titanet Group
                condition.is_enabled     = CV(True, Cond.IS)
                condition.interface_mode = CV("tagged", Cond.IS)
                condition.tagged_oids    = CV(validated_uplink_oids, Cond.IS)
                condition.untagged_oid   = CV(None, Cond.IS)

                self.interface_conditions[hostname][ifname].append(condition)

        ## edges registered in NB but not appeared in cores' downlinks
        neglected_edges = set(uplink_oids.keys()) - edges
        for edgename in neglected_edges:
            annotation = Annotation("Neglected edge")
            self.device_annotations[edgename].append(annotation)


    def check_master_backup_tag_consistency(self):
        desired_backup = {}
        desired_backup_o = {}
        desired_backup_s = {}

        for hostname, device_interfaces in self.nb_interfaces.all.items():
            if self.nb_devices.all[hostname]["role"] != Slug.Role.CoreSW:
                continue

            for ifname, interface in device_interfaces.items():
                current      = InterfaceState(interface)
                master_state = current
                conditions   = self.interface_conditions[hostname][ifname]

                if len(conditions) > 0:
                    condition   = reduce(operator.add, conditions)
                    desired, ok = self.__build_desired(current, condition)

                    if ok:
                        master_state = desired

                if master_state.has_tag(Slug.Tag.CoreMaster):
                    desired_backup[ifname] = deepcopy(master_state)
                    desired_backup[ifname].tags = set(desired_backup[ifname].tags)
                    desired_backup[ifname].tags -= { Slug.Tag.CoreMaster }
                    desired_backup[ifname].tags |= { Slug.Tag.CoreBackup }

                if master_state.has_tag(Slug.Tag.CoreOokayamaMaster):
                    desired_backup_o[ifname] = deepcopy(master_state)
                    desired_backup_o[ifname].tags = set(desired_backup_o[ifname].tags)
                    desired_backup_o[ifname].tags -= { Slug.Tag.CoreOokayamaMaster }
                    desired_backup_o[ifname].tags |= { Slug.Tag.CoreOokayamaBackup }

                if master_state.has_tag(Slug.Tag.CoreSuzukakeMaster):
                    desired_backup_s[ifname] = deepcopy(master_state)
                    desired_backup_s[ifname].tags = set(desired_backup_s[ifname].tags)
                    desired_backup_s[ifname].tags -= { Slug.Tag.CoreSuzukakeMaster }
                    desired_backup_s[ifname].tags |= { Slug.Tag.CoreSuzukakeBackup }

        for hostname, device_interfaces in self.nb_interfaces.all.items():
            if self.nb_devices.all[hostname]["role"] != Slug.Role.CoreSW:
                continue

            for ifname, interface in device_interfaces.items():
                current = InterfaceState(interface)
                desired = None

                ## skip if the interface needs manual repair
                if self.is_manual_repair_interface[hostname][ifname]:
                    continue

                try:
                    if current.has_tag(Slug.Tag.CoreBackup):
                        desired = desired_backup[ifname]

                    if current.has_tag(Slug.Tag.CoreOokayamaBackup):
                        desired = desired_backup_o[ifname]

                    if current.has_tag(Slug.Tag.CoreSuzukakeBackup):
                        desired = desired_backup_s[ifname]

                except KeyError:
                    annotation = Annotation("Neglected backup")
                    self.interface_annotations[hostname][ifname].append(annotation)
                    continue

                if desired is None:
                    continue

                condition = InterfaceCondition("Master/Backup consistency")

                ## copy interface settings but keep original tags
                condition.is_enabled     = CV(desired.is_enabled, Cond.IS, priority=20)
                condition.description    = CV(desired.description, Cond.IS, priority=20)
                condition.interface_mode = CV(desired.interface_mode, Cond.IS, priority=20)
                condition.tagged_oids    = CV(desired.tagged_oids, Cond.IS, priority=20)
                condition.untagged_oid   = CV(desired.untagged_oid, Cond.IS, priority=20)
                condition.tags           = CV(desired.tags, Cond.IS, priority=20)

                self.interface_conditions[hostname][ifname].append(condition)

