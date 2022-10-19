from ansible_runner import run
from pprint import pprint
import time
import os

from tn4.cli.base import CommandBase


class Deploy(CommandBase):
    def __init__(self, args):
        self.flg_use_cache         = args.use_cache
        self.flg_dryrun            = args.dryrun
        self.flg_debug             = args.debug
        self.custom_template_path  = args.template
        self.verbosity             = args.v
        self.fetch_inventory_opts  = [
            args.hosts,   args.no_hosts,
            args.areas,   args.no_areas,
            args.roles,   args.no_roles,
            args.vendors, args.no_vendors,
            args.tags,    args.no_tags,
            args.use_cache,
        ]


    def append_ansible_common_vars(self):
        self.ansible_common_vars |= {
            "commit_confirm_sec": 0,
            "is_dryrun":          self.flg_dryrun,
            "is_quiet":           self.verbosity is None,
            "is_debug":           self.flg_debug,
            "is_overwrite":       self.custom_template_path is not None,
            "overwrite_j2_path":  self.custom_template_path,
        }

        for host in self.inventory["_meta"]["hosts"].values():
            host |= self.ansible_common_vars


    def exec(self):
        self.fetch_inventory(*self.fetch_inventory_opts, debug=self.flg_debug)
        self.append_ansible_common_vars()

        run_opts = {
            "inventory":          self.inventory,
            "private_data_dir":   self.project_path,
            "project_dir":        self.project_path,
            "playbook":           self.main_task_path,
            "verbosity":          self.verbosity,
            "envvars": {
                "ANSIBLE_CONFIG": self.ansible_cfg_path,
            },
        }

        results = None
        annotation = "[red bold](DRYRUN)" if self.flg_dryrun else ""
        start_at = time.time()

        ## workaround: https://github.com/ansible/ansible-runner/issues/702
        hosts_json = f"{self.inventory_path}/hosts.json"
        os.path.exists(hosts_json) and os.remove(hosts_json)

        if self.custom_template_path is None:
            self.console.log(f"[yellow]Provisioning Titanet4 with Ansible Runner... {annotation}")
        else:
            self.console.log(f"[yellow]Provisioning Titanet4 with Ansible Runner using custom template... {annotation}")

        print("\n"*1)  # terminal margin
        results = run(**run_opts)
        print("\n"*1)  # terminal margin

        et = round(time.time() - start_at, 1)
        self.console.log(f"[yellow]Ansible Runner finished in {et} sec.")

        return 0
