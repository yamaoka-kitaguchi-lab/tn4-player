from tn4.netbox.base import ClientBase


class Addresses(ClientBase):
    path = '/ipam/ip-addresses/'

    def __init___(self):
        super().__init___()

    def get_addresses(self, ctx):
        all_addresses = self.query(ctx, path)
        for address in all_addresses:
            address["tags"] = [tag["slug"] for tag in address["tags"]]

        return all_addresses

