from tn4.netbox.base import ClientBase
from tn4.netbox.slug import Slug


class Interfaces(ClientBase):
    path = "/dcim/interfaces/"

    ## Slugs of interface type name
    allowed_types_virtual = ["lag"]  # ignore virtual type interfaces
    allowed_types_ethernet_utp = [
         "1000base-t", "2.5gbase-t", "5gbase-t", "10gbase-t",
    ]
    allowed_types_ethernet = [
        *allowed_types_ethernet_utp,
        "100base-tx", "1000base-x-gbic", "1000base-x-sfp", "10gbase-cx4", "10gbase-x-sfpp", "10gbase-x-xfp",
        "10gbase-x-xenpak", "10gbase-x-x2", "25gbase-x-sfp28", "40gbase-x-qsfpp", "50gbase-x-sfp28",
        "100gbase-x-cfp", "100gbase-x-cfp2", "100gbase-x-cfp4", "100gbase-x-cpak", "100gbase-x-qsfp28",
        "200gbase-x-cfp2", "200gbase-x-qsfp56", "400gbase-x-qsfpdd", "400gbase-x-osfp",
    ]
    allowed_types = [*allowed_types_virtual, *allowed_types_ethernet]

    def __init__(self):
        super().__init__()
        self.all_interfaces = None


    def lookup_vlan_name(self, vlanid, ctx):
        if vlanid in ctx.vlans.keys():
            return ctx.vlans[vlanid]["name"]
        return None


    def lookup_interface_address(self, ifid, ctx):
        addr4, addr6 = [], []
        for addr in ctx.addresses:
            if addr["assigned_object_id"] == ifid:
                if addr["family"]["label"] == "IPv4":
                    addr4.append(addr["address"])
                if addr["family"]["label"] == "IPv6":
                    addr6.append(addr["address"])
        return addr4, addr6


    def update(self, device_name, interface_name,
                         description=None, enabled=None, mode=None, untagged_vlanid=None, tagged_vlanids=None, tags=None):
        data = []
        body = {
            "id": self.all_interfaces[device_name][interface_name]["id"]
        }

        if description is not None:
            body["description"] = description

        if enabled is not None:
            body["enabled"] = enabled

        if tags is not None:
            body["tags"] = [{"slug": tag} for tag in tags]

        if mode is not None:
            if mode.lower() == "access":
                body["mode"] = "access"
            if mode.lower() in ["tagged", "trunk"]:
                body["mode"] = "tagged"

        if untagged_vlanid is not None:
            body["untagged_vlan"] = int(untagged_vlanid)

        if tagged_vlanids is not None:
            body["tagged_vlans"] = list(map(int, tagged_vlanids))

        data.append(body)
        if data:
            return self.query(self.path, data, update=True)
        return


    ## Return interface list as a dict obj
    ##  - primary key:    hostname, not device name (eg. 'minami3', not 'minami3 (1)')
    ##  - secondary key:  interface name (eg. ge-0/0/0)
    ##  - value:          NetBox interface object
    def fetch_interfaces(self, ctx, use_cache=False):
        all_interfaces = None
        hastag = lambda i, t: "tags" in i and t in i["tags"]
        hasrole = lambda i, r: ctx.devices[i["device"]["name"]]["role"] == r

        if use_cache:
            if self.all_interfaces is not None:
                return self.all_interfaces
            all_interfaces, _ = self.load(self.path)

        if all_interfaces is None:
            all_interfaces, _ = self.query(ctx, self.path)

        self.all_interfaces = {}
        for interface in all_interfaces:
            interface["tags"] = [tag["slug"] for tag in interface["tags"]]

            dev_name = interface["device"]["name"]
            hostname = ctx.devices[dev_name]["hostname"]

            is_empty_irb = interface["name"] == "irb" and interface["mode"] is None
            if is_empty_irb:
                continue  # ignored. these interfaces should have been fixed by nbck module beforehand

            is_upstream = hastag(interface, Slug.Tag.Upstream)

            interface |= {
                "is_ansible_target": ctx.devices[dev_name]["is_ansible_target"],
                "is_10mbps":         interface["speed"] == 10 * 1000,
                "is_100mbps":        interface["speed"] == 100 * 1000,
                "is_1gbps":          interface["speed"] == 1000 * 1000,
                "is_10gbps":         interface["speed"] == 10000 * 1000,
                "is_storm_5m":       hasrole(interface, Slug.Role.CoreSW) and hastag(interface, Slug.Tag.Storm5M),
                "is_bpdu_filtered":  hasrole(interface, Slug.Role.CoreSW) and hastag(interface, Slug.Tag.BPDUFilter),
                "is_deploy_target":  interface["type"]["value"] in self.allowed_types,
                "is_lag_member":     interface["lag"] is not None,
                "is_lag_parent":     interface["type"]["value"] == "lag",
                "is_poe":            hastag(interface, Slug.Tag.PoE),
                "is_protected":      hastag(interface, Slug.Tag.Protect),
                "is_to_ap":          hasrole(interface, Slug.Role.EdgeSW) and hastag(interface, Slug.Tag.Wifi),
                "is_to_core":        hasrole(interface, Slug.Role.EdgeSW) and hastag(interface, Slug.Tag.EdgeUpstream),
                "is_to_edge":        hasrole(interface, Slug.Role.CoreSW) and hastag(interface, Slug.Tag.CoreDownstream),
                "is_upstream":       is_upstream,
                "is_utp":            interface["type"]["value"] in self.allowed_types_ethernet_utp,
                "is_physical":       interface["type"]["value"] in self.allowed_types_ethernet,
                "is_irb":            interface["name"][:4] == "irb.",
                "is_rspan":          interface["name"] == "rspan",
                "is_enabled":        interface["enabled"] or is_upstream,
                "is_phy_uplink":     False,  # updated in fetch_lag_members()
                "lag_parent_name":   None,
                "role":              ctx.devices[interface["device"]["name"]]["role"],
                "region":            ctx.devices[interface["device"]["name"]]["region"],
                "mtu":               interface["mtu"],  # None or integer (eg. 9000)
            }

            if interface["is_lag_member"]:
                interface["lag_parent_name"] = interface["lag"]["name"]

            ## Object key definitions
            ##  - "*_vlanid*" is the VLAN object ID used NetBox internally
            ##  - "*_vid*" is the actual VLAN ID (1..4094)

            all_vlanids = []
            all_vids = []

            interface |= {
                "tagged_vlanids":  None,
                "tagged_vids":     None,
                "untagged_vlanid": None,
                "untagged_vid":    None,
                "native_vid":      None,
            }

            vlan_mode = interface["mode"]
            if vlan_mode is not None:
                vlan_mode = vlan_mode["value"].lower()  # or vlan_mode is 'None' going to the else-block

            if vlan_mode == "access" and interface["untagged_vlan"] is not None:
                interface |= {
                    "vlan_mode":       "access",
                    "untagged_vlanid": interface["untagged_vlan"]["id"],
                    "untagged_vid":    interface["untagged_vlan"]["vid"],
                    "is_trunk_all":    False,
                }
                all_vlanids.append(interface["untagged_vlanid"])
                all_vids.append(interface["untagged_vid"])

                ## use vlan name for interface description if it is empty
                vlan_name = self.lookup_vlan_name(interface["untagged_vlan"]["id"], ctx)
                if interface["description"] == "" and vlan_name is not None:
                    interface["description"] = vlan_name

            elif vlan_mode == "tagged" and len(interface["tagged_vlans"]) > 0:
                interface |= {
                    "vlan_mode":       "trunk",  # rephrase to juniper/cisco style
                    "tagged_vlanids":  [v["id"] for v in interface["tagged_vlans"]],
                    "tagged_vids":     [v["vid"] for v in interface["tagged_vlans"]],
                    "is_trunk_all":    False,
                }
                all_vlanids.extend(interface["tagged_vlanids"])
                all_vids.extend(interface["tagged_vids"])

                if interface["untagged_vlan"] is not None:
                    interface["native_vid"] = interface["untagged_vlan"]["vid"]
                    all_vlanids.append(interface["untagged_vlan"]["id"])
                    all_vids.append(interface["untagged_vlan"]["vid"])

            elif vlan_mode == "tagged-all" or is_upstream:
                interface |= {
                    "vlan_mode":       "trunk",
                    "is_trunk_all":    True,
                }

            ## ignore conditions other than the above
            else:
                interface |= {
                    "vlan_mode":       None,
                    "is_trunk_all":    False,
                }

            interface |= {
                "all_vlanids": sorted(list(set(all_vlanids))),
                "all_vids":    sorted(list(set(all_vids))),
            }

            ## for cisco edge
            manufacturer = ctx.devices[interface["device"]["name"]]["device_type"]["manufacturer"]["slug"]
            if manufacturer == Slug.Manufacturer.Cisco:
                packed_size = 20
                absent_vids = [vid for vid in range(1, 4095) if vid not in all_vids]
                interface["absent_vids"] = [absent_vids[i:i+packed_size] for i in range(0, len(absent_vids), packed_size)]

            addr4, addr6 = self.lookup_interface_address(interface["id"], ctx)
            interface |= {
                "addresses4": addr4,
                "addresses6": addr6,
            }

            self.all_interfaces.setdefault(hostname, {})[interface["name"]] = interface

        ctx.interfaces = self.all_interfaces
        return self.all_interfaces


    ## Return LAG interface list as a dict obj
    ##  - primary key:    hostname, not device name (eg. minami3)
    ##  - secondary key:  parent interface (eg. ae1)
    ##  - value:          list of child interfaces (eg. [et-0/1/0, et-0/1/1])
    def fetch_lag_members(self, ctx):
        lag_members = {}

        if self.all_interfaces is None:
            self.fetch_interfaces()

        for hostname, interfaces in self.all_interfaces.items():
            lag_members[hostname] = {}

            for interface in interfaces.values():
                if not interface["is_lag_member"]:
                    continue

                p_name = interface["lag_parent_name"]
                is_protected = interface["is_protected"] | interfaces[p_name]["is_protected"]  # Does any interface has 'Protect' tag?

                interface["is_protected"] = interfaces[p_name]["is_protected"] = is_protected  # Sync all children with their parent
                interface["is_phy_uplink"] = interfaces[p_name]["is_upstream"]

                lag_members[hostname].setdefault(p_name, []).append(interface["name"])

        return lag_members


    ## Return VLAN list as a dict obj
    ##  - key:   hostname, not device name (eg. minami3)
    ##  - value: list of vlan object
    def fetch_vlans(self, ctx):
        all_used_vlanids = {}
        regions = {}
        roles = {}
        used_vlans = {}
        mgmt_vlans = {}

        mgmt_vlan_tags = {
            Slug.Role.CoreSW: {
                Slug.Region.Ookayama: Slug.Tag.MgmtVlanCoreOokayama,
                Slug.Region.Tamachi:  Slug.Tag.MgmtVlanCoreOokayama,
                Slug.Region.Suzukake: Slug.Tag.MgmtVlanCoreSuzukake,
            },
            Slug.Role.EdgeSW: {
                Slug.Region.Ookayama: Slug.Tag.MgmtVlanEdgeOokayama,
                Slug.Region.Tamachi:  Slug.Tag.MgmtVlanEdgeOokayama,
                Slug.Region.Suzukake: Slug.Tag.MgmtVlanEdgeSuzukake,
            },
        }

        if self.all_interfaces is None:
            self.fetch_interfaces()

        irb_vids, rspan_vids = [], []

        for hostname, interfaces in self.all_interfaces.items():
            used_vlanids = []

            for interface in interfaces.values():
                used_vlanids.extend(interface["all_vlanids"])

                if interface["is_irb"]:
                    irb_vids.extend(interface["all_vids"])
                if interface["is_rspan"]:
                    rspan_vids.extend(interface["all_vids"])

                regions[hostname] = interface["region"]
                roles[hostname] = interface["role"]

            all_used_vlanids[hostname] = list(set(used_vlanids))

        for hostname, used_vlanids in all_used_vlanids.items():
            region = regions[hostname]
            role = roles[hostname]

            for vlanid, vlan in ctx.vlans.items():
                is_in_use = vlanid in used_vlanids
                is_switch = role in mgmt_vlan_tags.keys()
                is_for_mgmt = is_switch and mgmt_vlan_tags[role][region] in vlan["tags"]

                vlan |= {
                    "is_for_irb":   vlan["vid"] in irb_vids,
                    "is_for_rspan": vlan["vid"] in rspan_vids,
                }

                if is_for_mgmt:
                    mgmt_vlans[hostname] = vlan

                if is_in_use:
                    used_vlans.setdefault(hostname, []).append(vlan)

            if hostname in used_vlans:
                used_vlans[hostname].sort(key=lambda v: v["vid"])

        return used_vlans, mgmt_vlans


    def fetch_as_inventory(self, ctx, use_cache=False):
        all_interfaces = self.fetch_interfaces(ctx, use_cache=use_cache)
        all_lag_members = self.fetch_lag_members(ctx)  # following fetch_interfaces()
        used_vlans, mgmt_vlans = self.fetch_vlans(ctx)

        ansible_targets = [ device["hostname"] for device in ctx.devices.values() if device["is_ansible_target"] ]

        target_interfaces = {
            hostname: {
                name: interface
                for name, interface in interfaces.items() if not interface["is_protected"]
            }
            for hostname, interfaces in all_interfaces.items()
        }

        target_lag_members = {
            hostname: {
                parent: children
                for parent, children in lag_members.items() if parent in target_interfaces[hostname]  # missing parent means protected parent
            }
            for hostname, lag_members in all_lag_members.items()
        }

        return {
            hostname: {
                "interfaces":  target_interfaces[hostname],   # key: interface name, value: interface object
                "lag_members": target_lag_members[hostname],  # key: parent name, value: list of members' name
                "vlans":       used_vlans[hostname],          # list of extended VLAN object
                "mgmt_vlan":   mgmt_vlans[hostname],          # a VLAN object
            }
            for hostname in all_interfaces.keys() if hostname in ansible_targets
        }

