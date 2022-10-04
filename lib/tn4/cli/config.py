from tn4.cli.base import CommandBase


class Config(CommandBase):
    def __init__(self, args):
        self.use_cache=args.use_cache
        self.fetch_inventory(hosts=args.hosts, no_hosts=args.no_hosts, areas=args.areas, no_areas=args.no_areas,
                             roles=args.roles, no_roles=args.no_roles, vendors=args.vendors, no_vendors=args.no_vendors,
                             tags=args.tags, no_tags=args.no_tags, use_cache=self.use_cache)


    def exec(self, stdout=False):
        print(len(self.inventory["_meta"]["hostvars"].keys()))
        print(self.inventory["_meta"]["hostvars"].keys())

