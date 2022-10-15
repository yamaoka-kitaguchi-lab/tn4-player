import ansible_runner as ansible
import time

from tn4.cli.base import CommandBase


class Deploy(CommandBase):
    def __init__(self, args):
        self.flg_use_cache         = args.use_cache
        self.flg_dryrun            = args.dryrun
        self.flg_debug             = args.debug
        self.custom_template_path  = args.template
        self.fetch_inventory_opts  = [
            args.hosts, args.no_hosts, args.areas, args.no_areas, args.roles, args.no_roles,
            args.vendors, args.no_vendors, args.tags, args.no_tags, args.use_cache
        ]


    def exec(self):
        self.fetch_inventory(*self.fetch_inventory_opts, debug=self.flg_debug)

        runner_opts = {
            "inventory":        self.inventory,
            "private_data_dir": self.ANSIBLE_WORKDIR,
            "project_dir":      self.ANSIBLE_WORKDIR,
            "playbook":         self.main_task_path,
            "check":            self.flg_dryrun,
            "envvars": {
                "ANSIBLE_CONFIG": self.ANSIBLE_WORKDIR + "/ansible.cfg",
            },
        }

        results = None
        annotation = "[red bold](DRYRUN)" if self.flg_dryrun else ""
        start_at = time.time()

        if self.custom_template_path is None:
            self.console.log(f"[yellow]Provisioning Titanet4 with Ansible Runner... {annotation}")
            results = ansible.run(**runner_opt)
        else:
            self.console.log(f"[yellow]Provisioning Titanet4 with Ansible Runner using custom template... {annotation}")
            results = ansible.run(**runner_opt)

        et = round(time.time()-start_at, 1)
        self.console.log(f"[yellow]Ansible Runner finished in {et} sec.")

        return 0
