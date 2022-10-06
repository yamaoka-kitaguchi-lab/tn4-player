from jinja2 import FileSystemLoader, Environment
import os
import sys
import json
import time

from tn4.cli.base import CommandBase


class Config(CommandBase):
    def __init__(self, args):
        self.flg_use_cache        = args.use_cache
        self.flg_inventory        = args.inventory
        self.outdir               = args.DIR_PATH
        self.custom_template_path = args.template
        self.inventory_json = f"{self.outdir}/inventory.json"
        self.fetch_inventory_opt = [
            args.hosts, args.no_hosts, args.areas, args.no_areas, args.roles, args.no_roles,
            args.vendors, args.no_vendors, args.tags, args.no_tags, args.use_cache
        ]


    def load_templates(self, trim_blocks):
        self.templates = {}

        for manufacturer in self.template_paths.keys():
            for role, paths in self.template_paths[manufacturer].items():
                if self.custom_template_path is not None:
                    paths = [ self.custom_template_path ]

                for path in paths:
                    l = FileSystemLoader(os.path.dirname(path))
                    e = Environment(loader=l, trim_blocks=trim_blocks)
                    t = e.get_template(os.path.basename(path))
                    self.templates.setdefault(manufacturer, {}).setdefault(role, []).append(t)


    def render(self, trim_blocks=False):
        self.load_templates(trim_blocks)
        self.configs = {}
        ignore_empty_lines = lambda s: "\n".join([l for l in s.split("\n") if l != ""])

        for host, hostvar in self.inventory["_meta"]["hostvars"].items():
            for template in self.templates[hostvar["manufacturer"]][hostvar["role"]]:
                try:
                    raw = template.render(hostvar)
                except Exception as e:
                    ip = hostvar["ansible_host"]
                    self.console.log(f"[red bold]An exception occurred while rendering {host} ({ip}). Skipped.")
                    self.console.log(f"[red bold dim]{e}")
                else:
                    self.configs[host] = ignore_empty_lines(raw)


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

        self.render()

        for host in self.configs:
            cfg = f"{self.outdir}/{host}.cfg"
            with open(cfg, "w") as fd:
                fd.write(self.configs[host])

