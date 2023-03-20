from collections import OrderedDict
from datetime import datetime
from pprint import pprint
from rich import box
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table
import os
import time

from tn4.cli.base import CommandBase
from tn4.netbox.slug import Slug
from tn4.doctor.diagnose import Diagnose
from tn4.doctor.repair import Repair


class Capability:
    def __init__(self, ctx, nbcli):
        self.diagnose = Diagnose(ctx)
        self.repair   = Repair(ctx, nbcli)

        self.oid_to_vid = {}

        for vlan in self.diagnose.nb_vlans.all.values():
            v = str(vlan["vid"])
            if vlan["group"]["slug"] != Slug.VLANGroup.Titanet:
                v += "!"
            self.oid_to_vid[vlan["id"]] = v


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


    def show_karte_and_ask(self, *all_kartes, use_panel=False, skip_confirm=False):
        table = Table(show_header=True, header_style="bold white")
        table.box = box.SIMPLE

        table.add_column("#",           style="dim")
        table.add_column("Device",      style="bold")
        table.add_column("Interface",   style="bold")
        table.add_column("Current",     style="magenta")
        table.add_column("Desired",     style="green")
        table.add_column("Arguments",   style="cyan")
        table.add_column("Annotations", style="dim")

        for i, karte in enumerate(all_kartes):
            r =  [ str(i+1) if karte.desired_state is not None else "" ]
            r += [ karte.hostname ]
            r += [ "-" if karte.ifname is None else karte.ifname ]
            r += [ "-" if karte.current_state is None else karte.current_state.to_rich(self.cap.oid_to_vid) ]
            r += [ "-" if karte.desired_state is None else karte.desired_state.to_rich(self.cap.oid_to_vid) ]
            r += [ "-" if karte.arguments is None else "\n".join(karte.arguments) ]
            r += [ "-" if karte.annotations is None else "\n".join(map(str, karte.annotations)) ]

            table.add_row(*r)

            if i < len(all_kartes)-1:
                table.add_row()

        if use_panel:
            self.console.print(Panel.fit(table, title="Device Interface Karte"))
        else:
            self.console.print(table)


        return all_kartes


    def exec(self):
        ok = self.fetch_inventory(
            *self.fetch_inventory_opts,
            netbox_url=self.netbox_url, netbox_token=self.netbox_token,
            use_cache=self.flg_use_cache, debug=self.flg_debug, fetch_all=True
        )

        if not ok:
            return 100

        self.cap = Capability(self.ctx, self.nb.cli)

        with self.console.status(f"[green]Scanning NetBox and checking consistency..."):

            self.cap.diagnose.check_exclusive_tag_conflict()
            self.console.log(f"[yellow]Checked exclusive tag")

            self.cap.diagnose.check_and_clear_incomplete_interfaces()
            self.console.log(f"[yellow]Checked incomplete interfaces")

            self.cap.diagnose.check_and_clear_obsoleted_interfaces()
            self.console.log(f"[yellow]Checked obsoleted interfaces")

            self.cap.diagnose.check_wifi_tag_consistency()
            self.console.log(f"[yellow]Checked 'Wi-Fi' tag consistency")

            self.cap.diagnose.check_hosting_tag_consistency()
            self.console.log(f"[yellow]Checked 'Hosting' tag consistency")

            self.cap.diagnose.check_vlan_group_consistency()
            self.console.log(f"[yellow]Checked VLAN group consistency")

            self.cap.diagnose.check_and_remove_empty_irb()
            self.console.log(f"[yellow]Checked empty irb")

            self.cap.diagnose.check_edge_core_consistency()
            self.console.log(f"[yellow]Checked Edge/Core consistency")

            self.cap.diagnose.check_master_slave_tag_consistency()
            self.console.log(f"[yellow]Checked Master/Slave consistency")

        if self.flg_diagnosis_only:
            return 0

        all_kartes = self.cap.diagnose.summarize()
        kartes = self.show_karte_and_ask(*all_kartes, use_panel=True, skip_confirm=False)


        #with self.console.status(f"[green]Repairing..."):
        #    for karte in kartes:
        #        cap.repair.by_karte(karte)



        return 0
