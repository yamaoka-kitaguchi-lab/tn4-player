from rich.console import Console
import os
import sys
import time

CURDIR            = os.path.dirname(__file__)
ANSIBLE_WORKDIR   = os.path.join(CURDIR, "../../..")
ANSIBLE_INVENTORY = os.path.join(CURDIR, "../../../inventory")
ANSIBLE_PROJECT   = os.path.join(CURDIR, "../../../project")
ANSIBLE_ROLES     = os.path.join(CURDIR, "../../../project/roles")
sys.path.append(ANSIBLE_INVENTORY)

from tn4.netbox.slug import Slug
from netbox import NetBox


class CommandBase:
    console = Console(log_time_format="%Y-%m-%dT%H:%M:%S")

    project_path     = ANSIBLE_WORKDIR
    main_task_path   = f"{ANSIBLE_PROJECT}/main.yml"
    ansible_cfg_path = f"{ANSIBLE_WORKDIR}/ansible.cfg"

    template_paths = {
        Slug.Manufacturer.Cisco: {
            Slug.Role.EdgeSW: [
                f"{ANSIBLE_ROLES}/cisco/templates/edge.cfg.j2",
                f"{ANSIBLE_ROLES}/cisco/templates/overwrite.cfg.j2",
            ]
        },
        Slug.Manufacturer.Juniper: {
            Slug.Role.EdgeSW: [
                f"{ANSIBLE_ROLES}/juniper/templates/edge.cfg.j2",
                f"{ANSIBLE_ROLES}/juniper/templates/edge_overwrite.cfg.j2"
            ],
            Slug.Role.CoreSW: [
                f"{ANSIBLE_ROLES}/juniper/templates/core.cfg.j2",
                f"{ANSIBLE_ROLES}/juniper/templates/core_overwrite.cfg.j2"
            ]
        }
    }


    def fetch_inventory(self, hosts=[], no_hosts=[], areas=[], no_areas=[], roles=[], no_roles=[],
                        vendors=[], no_vendors=[], tags=[], no_tags=[], use_cache=False, debug=False):
        nb = NetBox()

        m = "Fetching the latest inventory from NetBox, this may take a while..."
        if use_cache:
            m = "Loading local cache and rebuilding inventory, this usually takes less than few seconds..."
        annotation = "[red bold dim]using cache" if use_cache else ""

        with self.console.status(f"[green]{m}"):
            start_at = time.time()
            nb.cli.sites.fetch_as_inventory(nb.ctx, use_cache=use_cache)
            et = round(time.time() - start_at, 1)
            self.console.log(f"[yellow]Loading finished from {nb.cli.sites.path} in {et} sec {annotation}")

            start_at = time.time()
            nb.cli.vlans.fetch_as_inventory(nb.ctx, use_cache=use_cache)
            et = round(time.time() - start_at, 1)
            self.console.log(f"[yellow]Loading finished from {nb.cli.vlans.path} in {et} sec {annotation}")

            start_at = time.time()
            nb.cli.addresses.fetch_as_inventory(nb.ctx, use_cache=use_cache)
            et = round(time.time() - start_at, 1)
            self.console.log(f"[yellow]Loading finished from {nb.cli.addresses.path} in {et} sec {annotation}")

            start_at = time.time()
            devices = nb.cli.devices.fetch_as_inventory(nb.ctx, use_cache=use_cache)
            et = round(time.time() - start_at, 1)
            self.console.log(f"[yellow]Loading finished from {nb.cli.devices.path} in {et} sec {annotation}")

            start_at = time.time()
            interfaces = nb.cli.interfaces.fetch_as_inventory(nb.ctx, use_cache=use_cache)
            et = round(time.time() - start_at, 1)
            self.console.log(f"[yellow]Loading finished from {nb.cli.interfaces.path} in {et} sec {annotation}")

            nb.nbdata = nb.cli.merge_inventory(devices, interfaces)
            inventory = nb.fetch_inventory()
            self.console.log(f"[yellow]Building Titanet4 inventory completed")

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

        self.console.log(f"[yellow]Found {len(target_hosts)} hosts")
        self.console.log(f"[yellow dim]{', '.join(target_hosts)}")
