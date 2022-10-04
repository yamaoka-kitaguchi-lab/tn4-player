from rich.console import Console
import os
import sys

CURDIR             = os.path.dirname(__file__)
ANSIBLE_PRODUCTION = os.path.join(CURDIR, "../../../inventories/production")
sys.path.append(ANSIBLE_PRODUCTION)

from tn4.netbox.slug import Slug
from netbox import dynamic_inventory


class CommandBase:
    console = Console(log_time_format="%Y-%m-%dT%H:%M:%S")


    def fetch_inventory(self, hosts=[], no_hosts=[], areas=[], no_areas=[], roles=[], no_roles=[],
                        vendors=[], no_vendors=[], tags=[], no_tags=[], use_cache=False):
        inventory = dynamic_inventory(use_cache=use_cache)

        hostnames = []
        includes, excludes = [], []
        area_to_hosts, role_to_hosts, vendor_to_hosts, tag_to_hosts = {}, {}, {}, {}

        for hostname, hostvar in inventory["_meta"]["hostvars"].items():
            area_to_hosts.setdefault(hostvar["region"], []).append(hostname)
            area_to_hosts.setdefault(hostvar["sitegp"], []).append(hostname)
            role_to_hosts.setdefault(hostvar["role"], []).append(hostname)
            vendor_to_hosts.setdefault(hostvar["manufacturer"], []).append(hostname)

            for tag in hostvar["device_tags"]:
                tag_to_hosts.setdefault(tag, []).append(hostname)

        includes.extend(hosts)
        excludes.extend(no_hosts)

        for area in areas:
            includes.extend(area_to_hosts[area])

        for no_area in no_areas:
            excludes.extend(area_to_hosts[no_area])

        for role in roles:
            includes.extend(role_to_hosts[role])

        for no_role in no_roles:
            excludes.extend(role_to_hosts[no_role])

        for vendor in vendors:
            includes.extend(vendor_to_hosts[vendor])

        for no_vendor in no_vendors:
            excludes.extend(vendor_to_hosts[no_vendor])

        for tag in tags:
            includes.extend(tag_to_hosts[tag])

        for no_tag in no_tags:
            excludes.extend(tag_to_hosts[no_tag])

        if len(includes) == 0:
            includes = inventory["_meta"]["hostvars"].keys()

        target_hosts = list(set(includes) - set(excludes))

        self.inventory = {
            **{
                role: {
                    "hosts": [ h for h in hosts if h in target_hosts ]
                }
                for role, hosts in role_to_hosts.items()
            },
            "_meta": {
                "hostvars": {
                    host: inventory["_meta"]["hostvars"][host]
                    for host in target_hosts
                }
            }
        }

