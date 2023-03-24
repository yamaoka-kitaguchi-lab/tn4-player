from tn4.netbox.base import ClientBase


class FhrpGroups(ClientBase):
    path = "/ipam/fhrp-groups/"

    def __init__(self):
        super().__init__()
        self.all_fhrp_groups = None


    def delete(self, ctx, fhrp_group_id):
        return self.query(ctx, f"{self.path}{str(fhrp_group_id)}/", delete=True)


    def delete_by_custom_fields(self, ctx, cf):
        if self.fhrp_group_ids is None:
            self.fetch_fhrp_groups(ctx)

        cf_keys = cf.keys()
        for fhrp_group in self.fhrp_groups:
            matched = True
            for cf_key in cf_keys:
                if cf_key not in fhrp_group["custom_fields"]:
                    matched = False
                    break
                if fhrp_group["custom_fields"][cf_key] == cf[cf_key]:
                    matched = False
                    break

            if matched:
                self.delete(ctx, fhrp_group["id"])


    def create(self, ctx, fhrp_group_id, protocol="vrrp3", **kwargs):
        data = [{
            "protocol": protocol,
            "group_id": fhrp_group_id,
            **{
                key: kwargs[key]
                for key in ["tags", "description", "custom_fields"] if key in kwargs
            }
        }]

        return self.query(ctx, self.path, data, update=True)


    def fetch_fhrp_groups(self, ctx, use_cache=False):
        all_fhrp_groups = None

        if use_cache:
            if self.all_fhrp_groups is not None:
                return self.all_fhrp_groups
            all_fhrp_groups, _ = self.load(self.path)

        if all_fhrp_groups is None:
            all_fhrp_groups, _ = self.query(ctx, self.path)

        self.all_fhrp_groups = {}
        for fhrp_group in all_fhrp_groups:
            self.all_fhrp_groups[fhrp_group["id"]] = fhrp_group

        ctx.fhrp_groups = self.all_fhrp_groups
        return self.all_fhrp_groups


    def fetch_as_inventory(self, ctx, use_cache=False):
        self.fetch_fhrp_groups(ctx, use_cache=use_cache)

