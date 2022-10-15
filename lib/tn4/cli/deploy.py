import ansible_runner as ansible
import time

from tn4.cli.base import CommandBase


class Deploy(CommandBase):
    def __init__(self, args):
        self.flg_use_cache        = args.use_cache
        self.flg_dryrun           = args.dryrun
        self.flg_debug            = args.debug
        self.custom_template_path = args.template
        self.fetch_inventory_opt = [
            args.hosts, args.no_hosts, args.areas, args.no_areas, args.roles, args.no_roles,
            args.vendors, args.no_vendors, args.tags, args.no_tags, args.use_cache
        ]


    def exec(self):
        self.fetch_inventory(*self.fetch_inventory_opt, debug=self.flg_debug)

        self.console.log(f"[yellow]Calling Ansible Runner...")
        start_at = time.time()

        ansible.run(inventory=self.inventory, playbook="")

        elapsed = round(time.time()-start_at, 2)
        self.console.log(f"[yellow]Ansible Runner finished in {elapsed} sec.")
        return 0
