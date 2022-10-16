from jinja2 import FileSystemLoader, Environment
import os
import json

from tn4.cli.base import CommandBase


class Config(CommandBase):
    def __init__(self, args):
        self.flg_use_cache        = args.use_cache
        self.flg_inventory        = args.inventory
        self.flg_debug            = args.debug
        self.outdir               = args.DIR_PATH
        self.custom_template_path = args.template
        self.inventory_json = f"{self.outdir}/inventory.json"
        self.fetch_inventory_opts  = [
            args.hosts,   args.no_hosts,
            args.areas,   args.no_areas,
            args.roles,   args.no_roles,
            args.vendors, args.no_vendors,
            args.tags,    args.no_tags,
            args.use_cache
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
            config = []

            for template in self.templates[hostvar["manufacturer"]][hostvar["role"]]:
                try:
                    raw = template.render(hostvar)
                except Exception as e:
                    ip = hostvar["ansible_host"]
                    self.console.log(f"[red bold]An exception occurred while rendering {host} ({ip}). Skipped.")
                    self.console.log(f"[red bold dim]{e}")
                else:
                    config.append(ignore_empty_lines(raw))

            self.configs[host] = "\n".join(config)


    def exec(self):
        self.fetch_inventory(*self.fetch_inventory_opts, debug=self.flg_debug)

        if self.flg_inventory:
            with self.console.status(f"[green]Exporting raw inventory..."):
                with open(self.inventory_json, "w") as fd:
                    json.dump(self.inventory, fd, indent=4, sort_keys=True, ensure_ascii=False)
                self.console.log(f"[yellow]Exporting inventory finished at {self.inventory_json}")
            return 0

        with self.console.status(f"[green]Rendering configs..."):
            self.render()
            self.console.log(f"[yellow]Rendering configs finished")

        with self.console.status(f"[green]Exporting rendered configs..."):
            for host in self.configs:
                cfg = f"{self.outdir}/{host}.cfg"
                with open(cfg, "w") as fd:
                    fd.write(self.configs[host])
            self.console.log(f"[yellow]Exporting rendered configs finished at {self.outdir}")

        return 0
