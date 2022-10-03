from pprint import pprint
import jinja2
import os
import sys
import time

CURDIR             = os.path.dirname(__file__)
ANSIBLE_PRODUCTION = os.path.join(CURDIR, "../../../inventories/production")
sys.path.append(ANSIBLE_PRODUCTION)

from netbox import dynamic_inventory


class CommandBase:
    def fetch_inventory(self, hosts=[], no_hosts=[], areas=[], no_areas=[], roles=[], no_roles=[], use_cache=False):
        inventory = dynamic_inventory(use_cache=use_cache)

        hostnames = []
        includes, excludes = [], []
        region_to_hosts, role_to_hosts = {}, {}
        for hostname, hostvar in inventory["_meta"]["hostvars"].items():
            region_to_hosts.setdefault(hostvar["region"], []).append(hostname)
            role_to_hosts.setdefault(hostvar["role"], []).append(hostname)

        includes.extend(hosts)
        excludes.extend(hosts)

        for area in areas:
            includes.extend(region_to_hosts[area])

        for no_area in no_areas:
            excludes.extend(region_to_hosts[no_area])

        for role in roles:
            includes.extend(region_to_hosts[role])

        for no_role in no_roles:
            excludes.extend(region_to_hosts[no_role])

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

