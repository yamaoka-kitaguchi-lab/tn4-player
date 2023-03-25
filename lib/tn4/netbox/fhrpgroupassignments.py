from tn4.netbox.base import ClientBase


class FhrpGroupAssignments(ClientBase):
    path = "/ipam/fhrp-group-assignments/"

    def __init__(self):
        super().__init__()
        self.all_fhrp_group_assignments = None


    def delete(self, ctx, fhrp_group_assignment_id):
        return self.query(ctx, f"{self.path}{str(fhrp_group_assignment_id)}/", delete=True)


    def delete_by_custom_fields(self, ctx, cf):
        if self.fhrp_group_assignment_ids is None:
            self.fetch_fhrp_group_assignments(ctx)

        cf_keys = cf.keys()
        for fhrp_group_assignment in self.fhrp_group_assignments:
            matched = True
            for cf_key in cf_keys:
                if cf_key not in fhrp_group_assignment["custom_fields"]:
                    matched = False
                    break
                if fhrp_group_assignment["custom_fields"][cf_key] == cf[cf_key]:
                    matched = False
                    break

            if matched:
                self.delete(ctx, fhrp_group_assignment["id"])


    def create(self, ctx, fhrp_group_id, interface_id, priority=1, **kwargs):
        data = [{
            "priority":       priority,
            "group":          fhrp_group_id,  # netbox object id
            "interface_type": "dcim.interface",
            "interface_id":   interface_id,
            **{
                key: kwargs[key]
                for key in [ "custom_fields" ] if key in kwargs
            }
        }]

        return self.query(ctx, self.path, data)


    def fetch_fhrp_group_assignments(self, ctx, use_cache=False):
        all_fhrp_group_assignments = None

        if use_cache:
            if self.all_fhrp_group_assignments is not None:
                return self.all_fhrp_group_assignments
            all_fhrp_group_assignments, _ = self.load(self.path)

        if all_fhrp_group_assignments is None:
            all_fhrp_group_assignments, _ = self.query(ctx, self.path)

        self.all_fhrp_group_assignments = {}
        for fhrp_group_assignment in all_fhrp_group_assignments:
            self.all_fhrp_group_assignments[fhrp_group_assignment["id"]] = fhrp_group_assignment

        ctx.fhrp_group_assignments = self.all_fhrp_group_assignments
        return self.all_fhrp_group_assignments


    def fetch_as_inventory(self, ctx, use_cache=False):
        self.fetch_fhrp_group_assignments(ctx, use_cache=use_cache)

