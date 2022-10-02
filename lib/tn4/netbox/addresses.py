from tn4.netbox.base import ClientBase


class Addresses(ClientBase):
    path = "/ipam/ip-addresses/"

    def __init__(self):
        super().__init__()
        self.all_addresses = None


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
        return {
            "addresses": self.fetch_addresses(ctx, use_cache=use_cache),
        }

