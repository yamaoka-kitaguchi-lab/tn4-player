import jinja2
import os
import sys
import time

from tn4.cli.base import CommandBase


class Config(CommandBase):
    def __init__(self, args):
        self.use_cache=args.use_cache
        self.fetch_inventory_opt = [
            args.hosts, args.no_hosts, args.areas, args.no_areas, args.roles, args.no_roles,
            args.vendors, args.no_vendors, args.tags, args.no_tags, args.use_cache
        ]


    def exec(self, stdout=False):
        start_at = time.time()

        with self.console.status("Loading, this may take a while..."):
            self.fetch_inventory(*self.fetch_inventory_opt)
            self.console.log("Loaded inventory")

        print(len(self.inventory["_meta"]["hostvars"].keys()))
        print(self.inventory["_meta"]["hostvars"].keys())

