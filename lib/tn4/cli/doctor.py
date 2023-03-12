from pprint import pprint
import time
import os

from tn4.cli.base import CommandBase
from tn4.doctor.diagnose import Diagnose


class Deploy(CommandBase):
    def __init__(self, args):
        self.flg_diagnosis_only    = args.diagnosis_only
        self.flg_force_repair      = args.force_repair
        self.flg_debug             = args.debug

        n = datetime.now()
        ts = n.strftime("%Y-%m-%d@%H-%M-%S")
        self.snapshot_basedir = f"{self.workdir_path}/project/snapshots/config.{ts}"


    def exec(self):
        ok = self.fetch_inventory(debug=self.flg_debug)
        if not ok:
            return 100

        self.console.log(f"[yellow]Hi")

        return 0
