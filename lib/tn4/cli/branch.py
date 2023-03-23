import os
import sys

from tn4.cli.base import CommandBase
from tn4.doctor.branch import BranchInfo, Branch


class BranchVlan(CommandBase):
    def __init__(self, args):
        self.flg_add    = args.add
        self.flg_delete = args.delete
        self.branch     = Branch(self.ctx, self.nb.cli)

        if self.flg_add:
            self.branch_info = BranchInfo(
                args.vlan_name,
                args.cidr_prefix, args.vrrp_master_ip, args.vrrp_backup_ip, args.vrrp_vip,
                args.cidr_prefix6, args.vrrp_master_ip6, args.vrrp_backup_ip6, args.vrrp_vip6,
            )

        if self.flg_delete:
            self.branch_info = BranchInfo(args.vlan_name)
            self.branch.set_tn4_branch_id(self.branch_info)


    def exec_add(self):
        self.branch.update_vlan(self.branch_info)
        self.branch.add_prefix(self.branch_info)
        self.branch.add_ip_address(self.branch_info)


    def exec_delete(self):
        self.branch.delete_vlan(self.branch_info)
        self.branch.delete_prefix(self.branch_info)
        self.branch.delete_ip_address(self.branch_info)


    def exec(self):
        if self.flg_add:
            return self.exec_add()

        if self.flg_delete:
            return self.exec_delete()

