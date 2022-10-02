from tn4.netbox.base import ClientBase


class Sites(ClientBase):
    path = "/dcim/sites/"

    def __init__(self):
        super().__init__()
        self.all_sites = None


    def fetch_sites(self, ctx, use_cache=False):
        all_sites = None

        if use_cache:
            if self.all_sites is not None:
                return self.all_sites
            all_sites, _ = self.load(self.path)

        if all_sites is None:
            all_sites, _ = self.query(ctx, self.path)

        self.all_sites = {}
        for site in all_sites:
            self.all_sites[site["slug"]] = site

        ctx.sites = self.all_sites
        return self.all_sites


    def fetch_as_inventory(self, ctx, use_cache=False):
        return {
            "sites": self.fetch_sites(ctx, use_cache=use_cache)
        }

