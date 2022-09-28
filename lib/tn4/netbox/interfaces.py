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


    def fetch_all(self, use_cache=True):
        if use_cache and self.all_interfaces:
            return self.all_interfaces  # early return

        hastag = lambda i, t: "tags" in t and t in i["tags"]
        hasrole = lambda i, r: "device_role" in i and "slug" in i["device_role"] and i["device_role"]["slug"] == r

        all_interfaces = self.query(self.path)
        for interface in all_interfaces:
            interface["tags"] = [tag["slug"] for tag in interface["tags"]]

            dev_name = interface["device"]["name"]
            int_name = interface["name"]
            if dev_name in self.all_devices:
                for k in ["device_role", "wifi_mgmt_vlanid", "wifi_vlanids", "hostname", "is_vc_member", "vc_chassis_number"]:
                    interface[k] = self.all_devices[dev_name][k]

            interface["is_deploy_target"] = interface["type"]["value"] in self.allowed_types
            interface["is_lag_parent"] = interface["type"]["value"] == "lag"
            interface["is_lag_member"] = interface["lag"] is not None
            interface["is_utp"] = interface["type"]["value"] in self.allowed_types_ethernet_utp
            interface["is_to_core"] = hasrole(interface, Slug.Role.EdgeSW) and hastag(interface, Slug.Tag.EdgeUpstream)
            interface["is_to_edge"] = hasrole(interface, Slug.Role.Core) and hastag(interface, Slug.Tag.CoreDownstream)
            interface["is_to_ap"] = hasrole(interface, Slug.Role.EdgeSW) and hastag(interface, Slug.Tag.Wifi)


            ## IMPORTANT: Object key definitions
            ##  - "*_vlanid" is the VLAN object ID used NetBox internally
            ##  - "*_vid" is the actual VLAN ID (1..4094)

            all_vlan_ids = []
            all_vids = []
            interface["tagged_vlanids"] = None
            interface["tagged_vids"] = None
            interface["untagged_vlanid"] = None
            interface["untagged_vid"] = None

            if interface["tagged_vlans"] is not None:
                interface["tagged_vlanids"] = [v["id"] for v in interface["tagged_vlans"]]
                interface["tagged_vids"] = [v["vid"] for v in interface["tagged_vlans"]]
                all_vlan_ids.extend(interface["tagged_vlanids"])
                all_vids.extend(interface["tagged_vids"])

            if interface["untagged_vlan"] is not None:
                interface["untagged_vlanid"] = interface["untagged_vlan"]["id"]
                interface["untagged_vid"] = interface["untagged_vlan"]["vid"]
                all_vlan_ids.append(interface["untagged_vlanid"])
                all_vids.append(interface["untagged_vid"])

            interface["all_vlanids"] = list(set(all_vlan_ids))
            interface["all_vids"] = list(set(all_vids))

            self.all_interfaces.setdefault(dev_name, {})[int_name] = interface
        return self.all_interfaces



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
