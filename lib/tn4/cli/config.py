import jinja2
import os
import sys
import json
import time

from tn4.cli.base import CommandBase


class Config(CommandBase):
    def __init__(self, args):
        self.flg_use_cache = args.use_cache
        self.flg_inventory = args.inventory
        self.outdir = args.DIR_PATH
        self.fetch_inventory_opt = [
            args.hosts, args.no_hosts, args.areas, args.no_areas, args.roles, args.no_roles,
            args.vendors, args.no_vendors, args.tags, args.no_tags, args.use_cache
        ]
        self.inventory_json = f"{self.outdir}/inventory.json"


    def render():
        pass


    def exec(self):
        m = "Fetching the latest inventory from NetBox, this may take a while..."
        if self.flg_use_cache:
            m = "Loading the cache and rebuilding inventory, this usually takes less than few seconds..."

        with self.console.status(f"[yellow]{m}"):
            start_at = time.time()
            self.fetch_inventory(*self.fetch_inventory_opt)
            rt = round(time.time() - start_at, 1)
            self.console.log(f"[yellow]Building Titanet4 inventory finished in {rt} sec")

        hosts = self.inventory["_meta"]["hostvars"].keys()
        self.console.log(f"[yellow]Found {len(hosts)} hosts")
        self.console.log(f"[yellow dim]{', '.join(hosts)}")

        if self.flg_inventory:
            with self.console.status(f"[yellow]Exporting raw inventory..."):
                with open(self.inventory_json, "w") as fd:
                    json.dump(self.inventory, fd, indent=4, sort_keys=True, ensure_ascii=False)
                self.console.log(f"[yellow]Exporting inventory finished at {self.inventory_json}")
            return 0

