from tn4.netbox.base import ClientBase


class Prefixes(ClientBase):
    path = "/ipam/prefixes/"

    def __init__(self):
        super().__init__()
        self.all_prefixes = None


    def delete(self, ctx, prefixid):
        return self.query(ctx, f"{self.path}{str(prefixid)}/", delete=True)


    def delete_by_custom_fields(self, ctx, cf):
        if self.prefixes is None:
            self.fetch_prefixes(ctx)

        cf_keys = cf.keys()
        for prefix in self.prefixes:
            matched = True
            for cf_key in cf_keys:
                if cf_key not in prefix["custom_fields"]:
                    matched = False
                    break
                if prefix["custom_fields"][cf_key] == cf[cf_key]:
                    matched = False
                    break

            if matched:
                self.delete(ctx, prefix["id"])


    def create(self, ctx, prefix, **kwargs):
        family = 4 if "." in prefix else 6

        data = [{
            "prefix": prefix,
            "family": family,
            "status": "active",
            **{
                key: kwargs[key]
                for key in ["tags", "description", "vlans", "custom_fields"] if key in kwargs
            }
        }]

        return self.query(ctx, self.path, data, update=True)


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

