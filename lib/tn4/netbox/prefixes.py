from tn4.netbox.base import ClientBase


class Prefixes(ClientBase):
    path = "/ipam/prefixes/"

    def __init__(self):
        super().__init__()
        self.all_prefixes = None


    def delete(self, ctx, prefixid):
        return self.query(ctx, f"{self.path}{str(prefixid)}/", delete=True)


    def delete_by_custom_fields(self, ctx, cf):
        for prefix in self.grep_by_custom_fields(ctx, cf):
            self.delete(ctx, prefix["id"])


    def create(self, ctx, prefix, **kwargs):
        data = [{
            "prefix": prefix,
            "status": "active",
            **{
                key: kwargs[key]
                for key in ["tags", "description", "vlan", "role", "custom_fields"] if key in kwargs
            }
        }]

        return self.query(ctx, self.path, data)


    def grep_by_custom_fields(self, ctx, cf):
        if self.all_prefixes is None:
            self.fetch_prefixes(ctx)

        prefixes = []

        for prefix in self.all_prefixes.values():
            matched = True
            for cf_key in cf.keys():
                if cf_key not in prefix["custom_fields"]:
                    matched = False
                    break
                if prefix["custom_fields"][cf_key] != cf[cf_key]:
                    matched = False
                    break

            if matched:
                prefixes.append(prefix)

        return prefixes


    def fetch_prefixes(self, ctx, use_cache=False):
        all_prefixes = None

        if use_cache:
            if self.all_prefixes is not None:
                return self.all_prefixes
            all_prefixes, _ = self.load(self.path)

        if all_prefixes is None:
            all_prefixes, _ = self.query(ctx, self.path)

        self.all_prefixes = {}
        for prefix in all_prefixes:
            self.all_prefixes[prefix["id"]] = prefix

        ctx.prefixes = self.all_prefixes
        return self.all_prefixes


    def fetch_as_inventory(self, ctx, use_cache=False):
        self.fetch_prefixes(ctx, use_cache=use_cache)

