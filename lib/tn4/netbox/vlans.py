from tn4.netbox.base import ClientBase
from tn4.netbox.slug import Slug


class Vlans(ClientBase):
    path = "/ipam/vlans/"
    titech_vlan_group_id = 2

    def __init__(self):
        super().__init__()
        self.all_vlans = None


    def delete(self, ctx, vlanid):
        return self.query(ctx, f"{self.path}{str(vlanid)}/", delete=True)


    def custom_update(self, ctx, vlanid, **kwargs):
        data = [{
            "id":            vlanid,
            "custom_fields": kwargs
        }]

        return self.query(ctx, self.path, data, update=True)


    ## Return all VLANs as a dict object
    ##  - key:   VLAN object ID (NetBox internal ID)
    ##  - value: VLAN object
    def fetch_vlans(self, ctx, use_cache=False):
        all_vlans = None

        if use_cache:
            if self.all_vlans is not None:
                return self.all_vlans
            all_vlans, _ = self.load(self.path)

        if all_vlans is None:
            all_vlans, _ = self.query(ctx, self.path)

        self.all_vlans = {}
        for vlan in all_vlans:
            vlan["tags"] = [tag["slug"] for tag in vlan["tags"]]
            vlan["is_protected"] = Slug.Tag.Protect in vlan["tags"]
            self.all_vlans[vlan["id"]] = vlan

        ctx.vlans = self.all_vlans
        return self.all_vlans


    ## Return Titech VLANs as a dict object
    ##  - key:   VID (1..4094)
    ##  - value: VLAN object
    def fetch_titech_vlans(self, ctx, use_cache=False):
        if self.all_vlans is None:
            self.fetch_vlans(ctx, use_cache=use_cache)

        groupid = str(self.titech_vlan_group_id)
        titech_vlans = {}

        for vlan in self.all_vlans.values():
            if vlan["group"]["id"] != self.titech_vlan_group_id:
                titech_vlans[vlan["vid"]] = vlan

        return titech_vlans


    def fetch_as_inventory(self, ctx, use_cache=False):
        self.fetch_titech_vlans(ctx, use_cache=use_cache)

