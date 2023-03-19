from pprint import pprint
from collections import OrderedDict
from datetime import datetime
import time
import os

from tn4.cli.base import CommandBase
from tn4.doctor.diagnose import Diagnose
from tn4.doctor.repair import InterfaceRepair


class Doctor(CommandBase):
    def __init__(self, args):
        self.netbox_url         = args.netbox_url
        self.netbox_token       = args.netbox_token

        self.flg_diagnosis_only = args.diagnosis_only
        self.flg_force_repair   = args.force_repair
        self.flg_use_cache      = args.use_cache
        self.flg_debug          = args.debug

        self.fetch_inventory_opts = [
            args.hosts,   args.no_hosts,
            args.areas,   args.no_areas,
            args.roles,   args.no_roles,
            args.vendors, args.no_vendors,
            args.tags,    args.no_tags,
        ]

        n = datetime.now()
        ts = n.strftime("%Y-%m-%d@%H-%M-%S")
        self.snapshot_basedir = f"{self.workdir_path}/project/snapshots/config.{ts}"


    def exec(self):
        ok = self.fetch_inventory(
            *self.fetch_inventory_opts,
            netbox_url=self.netbox_url, netbox_token=self.netbox_token,
            use_cache=self.flg_use_cache, debug=self.flg_debug
        )

        if not ok:
            return 100

        diag = Diagnose(self.ctx)

        with self.console.status(f"[green]Scanning NetBox and checking consistency..."):
            diag.check_tag_to_tag_consistency()
            self.console.log(f"[yellow]Checked inter-tag consistency")

            diag.check_and_clear_interface()
            self.console.log(f"[yellow]Checked obsoleted interfaces")

            diag.check_wifi_tag_consistency()
            self.console.log(f"[yellow]Checked 'Wi-Fi' tag consistency")

            diag.check_hosting_tag_consistency()
            self.console.log(f"[yellow]Checked 'Hosting' tag consistency")

            diag.check_vlan_group_consistency()
            self.console.log(f"[yellow]Checked VLAN group consistency")

            diag.check_and_remove_empty_irb()
            self.console.log(f"[yellow]Checked empty irb")

            diag.check_edge_core_consistency()
            self.console.log(f"[yellow]Checked Edge/Core consistency")

            diag.check_master_slave_tag_consistency()
            self.console.log(f"[yellow]Checked Master/Slave consistency")

        if self.flg_diagnosis_only:
            return 0

        device_karte, interface_karte = diag.summarize()

        #pprint(device_karte.dump(), sort_dicts=True)  # debug
        pprint(interface_karte.dump(), sort_dicts=True)  # debug
        #pprint(interface_karte.dump()["tamachi"], sort_dicts=True)  # debug

        return 0
