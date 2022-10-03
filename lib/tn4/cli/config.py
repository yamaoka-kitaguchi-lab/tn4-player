from tn4.cli.base import CommandBase


class Config(CommandBase):
    def __init__(self, args, use_cache=False):
        self.use_cache=use_cache
        self.fetch_inventory(hosts=args.hosts, no_hosts=args.no_hosts,
                             areas=args.areas, no_areas=args.no_areas,
                             roles=args.roles, no_roles=args.no_roles, use_cache=self.use_cache)


    def exec(self, stdout=False):
        print(self.inventory["_meta"]["hostvars"].keys())

