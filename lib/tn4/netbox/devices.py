from tn4.netbox.base import ClientBase
from tn4.netbox.slug import Slug

import re


class Devices(ClientBase):
    path = "/dcim/devices/"

    def __init__(self):
        super().__init__()
        self.all_devices = None


    def fetch_devices(self, ctx, use_cache=False):
        all_devices = None

        if use_cache:
            if self.all_devices is not None:
                return self.all_devices
            all_devices, _ = self.load(self.path)

        if all_devices is None:
            all_devices, _ = self.query(ctx, self.path)

        self.all_devices = {}
        for device in all_devices:
            device["tags"] = [tag["slug"] for tag in device["tags"]]
            dev_site = device["site"]["slug"]

            wifi_o1_area = [ Slug.SiteGroup.OokayamaNorth, Slug.SiteGroup.OokayamaWest,
                             Slug.SiteGroup.Midorigaoka, Slug.SiteGroup.Tamachi ]
            wifi_o2_area = [ Slug.SiteGroup.OokayamaEast, Slug.SiteGroup.OokayamaSouth,
                             Slug.SiteGroup.Ishikawadai ]

            if dev_site in ctx.sites:
                dev_sitegp = ctx.sites[dev_site]["group"]["slug"]
                if dev_sitegp in wifi_o1_area:
                    device["wifi_group"] = "O1"
                elif dev_sitegp in wifi_o2_area:
                    device["wifi_group"] = "O2"
                else:
                    device["wifi_group"] = "S"

            mgmt_ip = device["primary_ip"]["address"]
            if mgmt_ip is not None:
                mgmt_ip = mgmt_ip.split("/")[0]

            device |= {
                "hostname":          device["name"],
                "region":            ctx.sites[device["site"]["slug"]]["region"]["slug"],
                "is_test_device":    Slug.Tag.Test in device["tags"],
                "is_vc_member":      False,
                "vc_chassis_number": 0,
            }

            ## For stacked edge SWs
            if device["device_role"]["slug"] == Slug.Role.EdgeSW:
                r = re.match("([\w|-]+) \((\d+)\)", device["name"])  # hostname regex pattern
                if r is not None:
                    device |= {
                        "hostname":          r.group(1),  # device hostname: "minami3 (1)" -> "minami3"
                        "is_vc_member":      True,
                        "vc_chassis_number": r.group(2),  # chassis number: "minami3 (1)" -> "1"
                    }

            self.all_devices[device["name"]] = device

        ctx.devices = self.all_devices
        return self.all_devices


    def fetch_as_inventory(self, ctx, use_cache=False):
        devices = self.fetch_devices(ctx, use_cache=use_cache)
        return {
            "_hostnames": devices.keys(),
            "_roles":     [ d["device_role"] for d in devices.values() ],
            **{
                hostname: {
                    "manufacturer":    device["device_type"]["manufacturer"]["slug"],  # manufacturer slug
                    "region":          device["region"],                               # region slug
                    "is_test_device":  device["is_test_device"],                       # whethre or not having 'Test' tag
                    "mgmt_ip_address": device["mgmt_ip"],                              # device ip address without mask, or 'None'
                }
                for hostname, device in devices.items()
            }
        }

