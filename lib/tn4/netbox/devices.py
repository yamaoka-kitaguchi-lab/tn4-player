from tn4.netbox.base import ClientBase
from tn4.netbox.slug import Slug


class Devices(ClientBase):
    path = '/dcim/devices/'

    def __init__(self):
        super().__init__()

    def fetch_all(self, ctx):
        all_devices = self.query(ctx, self.path)

        for device in all_devices:
            device["tags"] = [tag["slug"] for tag in device["tags"]]
            dev_site = device["site"]["slug"]
            dev_sg = ctx.sites[dev_site]["group"]["slug"]

            if dev_site in self.all_sites:
                if dev_sg in [Slug.site_group_ookayama_north, Slug.site_group_ookayama_west, Slug.site_group_midorigaoka, Slug.site_group_tamachi]:
                    device["wifi_mgmt_vlanid"] = self.wifi_mgmt_vlanid_o1
                    device["wifi_vlanids"] = self.wifi_vlanids_o
                elif dev_sg in [Slug.site_group_ookayama_east, Slug.site_group_ookayama_south, Slug.site_group_ishikawadai]:
                    device["wifi_mgmt_vlanid"] = self.wifi_mgmt_vlanid_o2
                    device["wifi_vlanids"] = self.wifi_vlanids_o
                else:
                    device["wifi_mgmt_vlanid"] = self.wifi_mgmt_vlanid_s
                    device["wifi_vlanids"] = self.wifi_vlanids_s

            device["hostname"] = device["name"]
            device["is_vc_member"] = False
            device["vc_chassis_number"] = 0
            if device["device_role"]["slug"] == Slug.role_edge_sw:
                hostname_reg = re.match("([\w|-]+) \((\d+)\)", device["name"])
                if hostname_reg is not None:
                    device["hostname"] = hostname_reg.group(1)
                    device["is_vc_member"] = True
                    device["vc_chassis_number"] = hostname_reg.group(2)

            self.all_devices[device["name"]] = device
    return self.all_devices
