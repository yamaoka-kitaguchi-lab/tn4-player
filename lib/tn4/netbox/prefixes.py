from tn4.netbox.base import ClientBase


class Prefixes(ClientBase):
    path = "/ipam/prefixes/"

    def __init__(self):
        super().__init__()
        self.all_prefixes = None


    def fetch_prefixes(self, ctx, use_cache=False):
        all_prefixes = None

        if use_cache:
            if self.all_prefixes is not None:
                return self.all_prefixes
            all_prefixes, _ = self.load(self.path)

        if all_prefixes is None:
            all_prefixes, _ = self.query(ctx, self.path)

        self.all_prefixes = {}
        for site in all_prefixes:
            self.all_prefixes[site["slug"]] = site

        ctx.prefixes = self.all_prefixes
        return self.all_prefixes


    def fetch_as_inventory(self, ctx, use_cache=False):
        self.fetch_prefixes(ctx, use_cache=use_cache)

