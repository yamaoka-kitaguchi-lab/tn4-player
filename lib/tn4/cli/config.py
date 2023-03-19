from jinja2 import FileSystemLoader, Environment
import os
import json

from tn4.cli.base import CommandBase


class Config(CommandBase):
    def __init__(self, args):
        self.__args                = vars(args)
        self.outdir                = args.private_dir
        self.inventory_json        = f"{self.outdir}/inventory.json"

        self.custom_template_path  = args.custom_j2_path
        self.flg_debug             = args.debug
        self.flg_inventory         = args.as_inventory
        self.flg_remote_fetch      = args.remote_fetch
        self.flg_use_cache         = args.use_cache
        self.fetch_inventory_opts  = [
            args.hosts,   args.no_hosts,
            args.areas,   args.no_areas,
            args.roles,   args.no_roles,
            args.vendors, args.no_vendors,
            args.tags,    args.no_tags,
        ]


    def remote_fetch(self):
        from argparse import Namespace
        from tn4.cli.deploy import Deploy

        deploy_opt = self.__args
        deploy_opt |= dict(
            dryrun=True,           # actually not effective but for safety
            commit_confirm_min=1,  # same as above
            overwrite_j2_path=None,
            v=None,
        )
        deploy = Deploy(Namespace(**deploy_opt))
        deploy.snapshot_basedir = self.outdir
        deploy.flg_fetch_only = True

        return deploy.exec()


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

        for host, hostvar in self.inventory["_meta"]["hosts"].items():
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
        if self.flg_remote_fetch:
            return self.remote_fetch()

        ok = self.fetch_inventory(
            *self.fetch_inventory_opts,
            netbox_url=self.netbox_url, netbox_token=self.netbox_token,
            use_cache=self.flg_use_cache, debug=self.flg_debug
        )

        if not ok:
            return 100

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
