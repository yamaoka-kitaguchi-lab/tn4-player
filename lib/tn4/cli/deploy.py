from ansible_runner import run
from datetime import datetime
from pprint import pprint
import time
import os

from tn4.cli.base import CommandBase


class Deploy(CommandBase):
    def __init__(self, args):
        self.netbox_url            = args.netbox_url
        self.netbox_token          = args.netbox_token
        self.flg_use_cache         = args.use_cache
        self.flg_dryrun            = args.dryrun
        self.flg_early_exit        = args.early_exit
        self.flg_debug             = args.debug
        self.custom_template_path  = args.overwrite_j2_path
        self.commit_confirm_min    = 0 if args.commit_confirm_min is None else args.commit_confirm_min
        self.verbosity             = args.v
        self.fetch_inventory_opts  = [
            args.hosts,   args.no_hosts,
            args.areas,   args.no_areas,
            args.roles,   args.no_roles,
            args.vendors, args.no_vendors,
            args.tags,    args.no_tags,
        ]

        self.flg_fetch_only = False

        n = datetime.now()
        ts = n.strftime("%Y-%m-%d@%H-%M-%S")
        self.snapshot_basedir = f"{self.workdir_path}/project/snapshots/config.{ts}"


    def append_ansible_common_vars(self):
        self.ansible_common_vars |= {
            "commit_confirm_min": self.commit_confirm_min,
            "is_debug":           self.flg_debug,
            "is_dryrun":          self.flg_dryrun,
            "is_fetch_only":      self.flg_fetch_only,
            "is_overwrite":       self.custom_template_path is not None,
            "is_quiet":           self.verbosity is None or self.verbosity < 2,
            "overwrite_j2_path":  self.custom_template_path,
            "snapshot_basedir":   self.snapshot_basedir,
        }

        for host in self.inventory["_meta"]["hosts"].values():
            host |= self.ansible_common_vars


    def exec(self):
        ok = self.fetch_inventory(
            *self.fetch_inventory_opts,
            netbox_url=self.netbox_url, netbox_token=self.netbox_token,
            use_cache=self.flg_use_cache, debug=self.flg_debug
        )

        if not ok:
            return 100

        if self.flg_early_exit:
            self.console.log(f"[yellow]Bye.")
            return 0

        self.append_ansible_common_vars()

        run_opts = {
            "inventory":          self.inventory,
            "private_data_dir":   self.workdir_path,
            "project_dir":        self.workdir_path,
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

        os.makedirs(self.snapshot_basedir, exist_ok=True)

        if self.custom_template_path is not None:
            self.console.log(f"[yellow]Ready to provisioning Titanet4 with Ansible Runner using custom template... {annotation}")

        elif self.flg_fetch_only:
            self.console.log(f"[yellow]Ready to gather current configs with Ansible Runner...")

        else:
            self.console.log(f"[yellow]Ready to provisioning Titanet4 with Ansible Runner... {annotation}")

        print("\n"*0)  # terminal margin
        results = run(**run_opts)
        print("\n"*1)  # terminal margin

        et = round(time.time() - start_at, 1)
        self.console.log(f"[yellow]Ansible Runner finished in {et} sec.")

        return 0
