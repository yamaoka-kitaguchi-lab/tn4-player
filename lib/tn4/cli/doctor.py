from collections import OrderedDict
from datetime import datetime
from pprint import pprint
from rich import box
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table
import os
import sys
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


    def __flatten_num_string(self, nstr):
        l = []
        for n in nstr.split():
            if "-" in n:
                a, b = map(int, n.split("-"))
                l.extend([i for i in range(a,b+1)])
            else:
                l.append(int(n))
        return l


    def show_karte_and_ask(self, *unsorted_all_kartes, target_hosts=[],
                           use_panel=False, skip_confirm=False, again=False):
        all_kartes = [
            *[ k for k in unsorted_all_kartes if k.hostname in target_hosts and k.desired_state is not None ],
            *[ k for k in unsorted_all_kartes if k.hostname in target_hosts and k.desired_state is None ],
        ]

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

        print()
        if use_panel:
            self.console.print(Panel.fit(table, title="Device Interface Karte"))
        else:
            self.console.print(table)

        indices = [ i+1 for i, k in enumerate(all_kartes) if k.desired_state is not None ]

        print()
        if skip_confirm:
            with self.console.status("[bold]Performing force repair in 5 seconds..."):
                time.sleep(5)

        else:
            nstr = Prompt.ask("[green]Interfaces to skip repairing (eg: 1 3 5-9)")
            print()

            skipped_indices = self.__flatten_num_string(nstr)
            target_indices  = list(set(indices) - set(skipped_indices))
            target_kartes   = [ k for i, k in enumerate(all_kartes) if i+1 in target_indices ]
            annot_kartes    = [ k for k in all_kartes if k.desired_state is None ]

            if len(target_indices) < len(indices):
                m = ', '.join(map(str, skipped_indices))
                self.console.log(f"[yellow]Omitted the following from the above list: [dim]{m}")
                return self.show_karte_and_ask(*target_kartes, *annot_kartes, use_panel=use_panel, again=True)

            is_confirmed = Confirm.ask(
                f"[green]You are about to repair [bold yellow]{len(target_kartes)}[/bold yellow] interfaces. Continue?",
                default=False
            )
            print()

            if not is_confirmed:
                self.console.log("[yellow]Aborted, bye.")
                sys.exit(0)

        return target_kartes


    def exec(self):
        ok = self.fetch_inventory(
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

        hosts  = self.filter_hosts(*self.fetch_inventory_opts)
        kartes = self.cap.diagnose.summarize()
        kartes = self.show_karte_and_ask(*kartes, target_hosts=hosts,
                                         use_panel=False, skip_confirm=self.flg_force_repair)


        #with self.console.status(f"[green]Repairing..."):
        #    for karte in kartes:
        #        cap.repair.by_karte(karte)



        return 0
