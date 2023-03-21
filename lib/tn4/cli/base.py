from collections import OrderedDict
from pprint import pprint
from rich.console import Console
from yaml import safe_load
import copy
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

    inventory_path   = ANSIBLE_INVENTORY
    workdir_path     = ANSIBLE_WORKDIR
    main_task_path   = f"{ANSIBLE_PROJECT}/tn4.yml"
    ansible_cfg_path = f"{ANSIBLE_WORKDIR}/ansible.cfg"
    group_vars_path  = f"{ANSIBLE_INVENTORY}/group_vars/all/ansible.yml"

    template_paths = {
        Slug.Manufacturer.Cisco: {
            Slug.Role.EdgeSW: [
                f"{ANSIBLE_ROLES}/cisco/templates/edge.cfg.j2",
                #f"{ANSIBLE_ROLES}/cisco/templates/overwrite.cfg.j2",
            ]
        },
        Slug.Manufacturer.Juniper: {
            Slug.Role.EdgeSW: [
                f"{ANSIBLE_ROLES}/juniper/templates/edge.cfg.j2",
                #f"{ANSIBLE_ROLES}/juniper/templates/edge_overwrite.cfg.j2"
            ],
            Slug.Role.CoreSW: [
                f"{ANSIBLE_ROLES}/juniper/templates/core.cfg.j2",
                #f"{ANSIBLE_ROLES}/juniper/templates/core_overwrite.cfg.j2"
            ]
        }
    }


    ## CAUTION: filter_hosts() and fetch_inventory() are TIGHT coupling
    def filter_hosts(self, hosts=[], no_hosts=[], areas=[], no_areas=[], roles=[], no_roles=[],
                     vendors=[], no_vendors=[], tags=[], no_tags=[]):
        flatten = lambda x: [z for y in x for z in (flatten(y) if hasattr(y, '__iter__') and not isinstance(y, str) else (y,))]

        hostnames = []
        target_hosts = set()
        area_to_hosts, role_to_hosts, vendor_to_hosts, tag_to_hosts = {}, {}, {}, {}

        for hostname, hostvar in self.nb_inventory["_meta"]["hosts"].items():
            hostnames.append(hostname)
            area_to_hosts.setdefault(hostvar["region"], []).append(hostname)
            area_to_hosts.setdefault(hostvar["sitegp"], []).append(hostname)
            role_to_hosts.setdefault(hostvar["role"], []).append(hostname)
            vendor_to_hosts.setdefault(hostvar["manufacturer"], []).append(hostname)

            for tag in hostvar["device_tags"]:
                tag_to_hosts.setdefault(tag, []).append(hostname)

        typos = []
        for host in [*hosts, *no_hosts]:
            if host not in hostnames:
                typos.append(host)

        for area in [*areas, *no_areas]:
            if area not in area_to_hosts:
                typos.append(area)

        for role in [*roles, *no_roles]:
            if role not in role_to_hosts:
                typos.append(role)

        for vendor in [*vendors, *no_vendors]:
            if vendor not in vendor_to_hosts:
                typos.append(vendor)

        for tag in [*tags, *no_tags]:
            if tag not in tag_to_hosts:
                typos.append(tag)

        if len(typos) > 0:
            self.console.log("[red bold]Aborted. Your condition may contain NetBox undefined keywords. Typos?")
            self.console.log(f"[red dim]{', '.join(typos)}")
            sys.exit(1)

        target_hosts |= set(hosts)

        if len(target_hosts) == 0:
            target_hosts |= set(self.nb_inventory["_meta"]["hosts"].keys())

        target_hosts -= set(no_hosts)

        if areas:
            target_hosts &= set(flatten([ area_to_hosts[area] for area in areas ]))
        if no_areas:
            target_hosts -= set(flatten([ area_to_hosts[no_area] for no_area in no_areas ]))
        if roles:
            target_hosts &= set(flatten([ role_to_hosts[role] for role in roles ]))
        if no_roles:
            target_hosts -= set(flatten([ role_to_hosts[no_role] for no_role in no_roles ]))
        if vendors:
            target_hosts &= set(flatten([ vendor_to_hosts[vendor] for vendor in vendors ]))
        if no_vendors:
            target_hosts -= set(flatten([ vendor_to_hosts[no_vendor] for no_vendor in no_vendors ]))
        if tags:
            target_hosts &= set(flatten([ tag_to_hosts[tag] for tag in tags ]))
        if no_tags:
            target_hosts -= set(flatten([ tag_to_hosts[no_tag] for no_tag in no_tags ]))

        self.role_to_hosts = role_to_hosts
        return sorted(list(target_hosts))  # type conversion: set to list


    def fetch_inventory(self, hosts=[], no_hosts=[], areas=[], no_areas=[], roles=[], no_roles=[],
                        vendors=[], no_vendors=[], tags=[], no_tags=[],
                        netbox_url=None, netbox_token=None, use_cache=False, debug=False, fetch_all=False):
        nb = NetBox(url=netbox_url, token=netbox_token)

        self.console.log(f"[yellow dim]NetBox API endpoint: {nb.ctx.endpoint}")
        self.console.log(f"[yellow dim]NetBox API token:    {nb.ctx.token}")

        m = "Fetching the latest inventory from NetBox, this may take a while..."
        if use_cache:
            m = "Loading local cache and rebuilding inventory, this usually takes less than few seconds..."
        annotation = "[green bold dim]using cache" if use_cache else ""

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
            self.nb_inventory = nb.fetch_inventory(fetch_all=fetch_all)
            self.console.log(f"[yellow]Building Titanet4 inventory completed")

        target_hosts = self.filter_hosts(hosts, no_hosts, areas, no_areas,
                                         roles, no_roles, vendors, no_vendors, tags, no_tags)

        self.ansible_common_vars = {}
        with open(self.group_vars_path) as fd:
            self.ansible_common_vars |= safe_load(fd)

        self.inventory = {
            **{
                role: {
                    "hosts": { h: {} for h in hosts if h in target_hosts }
                }
                for role, hosts in self.role_to_hosts.items()
            },
            "_meta": {
                "hosts": OrderedDict({
                    host: self.nb_inventory["_meta"]["hosts"][host]
                    for host in target_hosts
                })
            }
        }

        n_target_hosts = len(target_hosts)
        if n_target_hosts > 0:
            self.console.log(f"[yellow]Found {n_target_hosts} hosts")
            self.console.log(f"[yellow dim]{', '.join(target_hosts)}")
        else:
            self.console.log("[red bold]No hosts found. Check the typos of your condition or devices' tags on NetBox")
            sys.exit(1)

        self.nb     = nb
        self.nbdata = copy.deepcopy(nb.nbdata)
        self.ctx    = copy.deepcopy(nb.ctx)

        self.ctx.interfaces = {
            hostname: interfaces
            for hostname, interfaces in self.ctx.interfaces.items() if hostname in target_hosts
        }

        return True
