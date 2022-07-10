from tn4.netbox.base import ClientBase
from tn4.netbox.slug import Slug


class Vlans(ClientBase):
    path = '/ipam/vlans/'

    def __init__(self):
        super().__init__()
        self.all_vlans = {}

    def get_vlans(self, ctx):
        all_vlans = self.query(ctx, path)

        for vlan in all_vlans:
            vlan["tags"] = [tag["slug"] for tag in vlan["tags"]]
            self.all_vlans[str(vlan["id"])] = vlan

        return self.all_vlans

