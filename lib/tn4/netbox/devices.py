from tn4.netbox.base import ClientBase
from tn4.netbox.slug import Slug


class Devices(ClientBase):
    path = "/dcim/devices/"

    def __init__(self):
        super().__init__()


    def fetch_all(self, ctx):
        all_devices = self.query(ctx, self.path)

        for device in all_devices:
            device["tags"] = [tag["slug"] for tag in device["tags"]]
            dev_site = device["site"]["slug"]
            dev_sitegp = ctx.sites[dev_site]["group"]["slug"]

            wifi_o1_area = [ Slug.SiteGroup.OokayamaNorth, Slug.SiteGroup.OokayamaWest,
                             Slug.SiteGroup.Midorigaoka, Slug.SiteGroup.Tamachi ]
            wifi_o2_area = [ Slug.SiteGroup.OokayamaEast, Slug.SiteGroup.OokayamaSouth,
                             Slug.SiteGroup.Ishikawadai ]

            if dev_site in self.all_sites:
                if dev_sitegp in wifi_o1_area:
                    device["wifi_mgmt_vlanid"] = self.wifi_mgmt_vlanid_o1
                    device["wifi_vlanids"]     = self.wifi_vlanids_o
                elif dev_sitegp in wifi_o2_area:
                    device["wifi_mgmt_vlanid"] = self.wifi_mgmt_vlanid_o2
                    device["wifi_vlanids"]     = self.wifi_vlanids_o
                else:
                    device["wifi_mgmt_vlanid"] = self.wifi_mgmt_vlanid_s
                    device["wifi_vlanids"]     = self.wifi_vlanids_s

            device["hostname"] = device["name"]
            device["is_vc_member"] = False
            device["vc_chassis_number"] = 0

            ## For stacked edge SWs
            if device["device_role"]["slug"] == Slug.Role.EdgeSW:
                r = re.match("([\w|-]+) \((\d+)\)", device["name"])  # hostname regex pattern
                if r is not None:
                    device["hostname"] = r.group(1)           # device hostname: "minami3 (1)" -> "minami3"
                    device["is_vc_member"] = True
                    device["vc_chassis_number"] = r.group(2)  # chassis number: "minami3 (1)" -> "1"

            self.all_devices[device["name"]] = device

        return self.all_devices
