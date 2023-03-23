from tn4.netbox.base import ClientBase


class Addresses(ClientBase):
    path = "/ipam/ip-addresses/"

    def __init__(self):
        super().__init__()
        self.all_addresses = None


    def delete(self, ctx, address_id):
        return self.query(ctx, f"{self.path}{str(address_id)}/", delete=True)


    def delete_by_custom_field(self, ctx, cf):
        rt = 0

        if self.addresses is None:
            self.fetch_addresses(ctx)

        cf_keys = cf.keys()
        for address in self.addresses:
            matched = True
            for cf_key in cf_keys:
                if cf_key not in address["custom_fields"]:
                    matched = False
                    break
                if address["custom_fields"][cf_key] == cf[cf_key]:
                    matched = False
                    break

            if matched:
                rt += self.delete(ctx, address["id"])

        return rt


    def create(self, ctx, address, **kwargs):
        family = 4 if "." in prefix else 6

        data = [{
            "address": address,
            "family": family,
            "status": "active",
            **{
                key: kwargs[key]
                for key in ["tags", "description", "custom_fields"] if key in kwargs
            }
        }]

        return self.query(ctx, self.path, data, update=True)


    def fetch_addresses(self, ctx, use_cache=False):
        all_addresses = None

        if use_cache:
            if self.all_addresses is not None:
                return self.all_addresses
            all_addresses, _ = self.load(self.path)

        if all_addresses is None:
            all_addresses, _ = self.query(ctx, self.path)

        self.all_addresses = []
        for address in all_addresses:
            address["tags"] = [tag["slug"] for tag in address["tags"]]
            self.all_addresses.append(address)

        ctx.addresses = self.all_addresses
        return self.all_addresses


    def fetch_as_inventory(self, ctx, use_cache=False):
        self.fetch_addresses(ctx, use_cache=use_cache)

