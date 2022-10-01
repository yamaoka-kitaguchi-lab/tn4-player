from tn4.netbox.base import ClientBase


class Vlans(ClientBase):
    path = "/ipam/vlans/"

    def __init__(self):
        super().__init__()
        self.all_vlans = None


    ## Return VLANs as a nested dict object
    ##  - primary key:   VLAN Group ID (NetBox internal ID)
    ##  - secondary key: VID (1..4094)
    ##  - value:         VLAN object
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
            groupid = str(vlan["group"]["id"])
            vid = str(vlan["vid"])
            self.all_vlans.setdefault(groupid, {})[vid] = vlan

        ctx.vlans = self.all_vlans
        return self.all_vlans


    def fetch_all(self, ctx, use_cache=False):
        return {
            "vlans": self.fetch_vlans(ctx, use_cache=use_cache),
        }

