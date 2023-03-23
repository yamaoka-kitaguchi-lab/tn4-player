import os
import sys

from tn4.cli.base import CommandBase
from tn4.doctor.branch import BranchInfo, Branch


class BranchVlan(CommandBase):
    def __init__(self, args):
        self.flg_add    = args.add
        self.flg_delete = args.delete


    def exec_add(self):
        pass


    def exec_delete(self):
        pass


    def exec(self):
        if self.flg_add:
            return self.exec_add()

        if self.flg_delete:
            return self.exec_delete()

