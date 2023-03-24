from tn4.netbox.base import ClientBase


class Addresses(ClientBase):
    path = "/ipam/ip-addresses/"

    def __init__(self):
        super().__init__()
        self.all_addresses = None


    def delete(self, ctx, address_id):
        return self.query(ctx, f"{self.path}{str(address_id)}/", delete=True)


    def delete_by_custom_fields(self, ctx, cf):
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
                self.delete(ctx, address["id"])


    def create(self, ctx, address, **kwargs):
        keys = ["role", "tags", "description", "assigned_object_type", "assigned_object_id", "custom_fields"]
        data = [{
            "address": address,
            "status":  "active",
            **{
                key: kwargs[key]
                for key in keys if key in kwargs
            }
        }]

        return self.query(ctx, self.path, data)


    def assign_to_interface(self, ctx, addr_id, iface_id):
        data = [{
            "assigned_object_type": "dcim.interface",
            "assigned_object_id":   iface_id,
        }]

        return self.query(ctx, self.path, data)


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

