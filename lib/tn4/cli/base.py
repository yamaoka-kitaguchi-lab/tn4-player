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
    def fetch_inventory(self, hosts=[], no_hosts=[], areas=[], no_areas=[], roles=[], no_roles=[]):
        inventory = dynamic_inventory()

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

        hostnames = list(set(includes) - set(excludes))
