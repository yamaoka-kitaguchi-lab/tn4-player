
class BranchInfo:
    def __init__(self, vlan_name, prefix_v4, vrrp_master_v4, vrrp_backup_v4, vrrp_vip_v4,
                 prefix_v6=None, vrrp_master_v6=None, vrrp_backup_v6=None, vrrp_vip_v6=None):
        self.vlan_name       = vlan_name
        self.prefix_v4       = prefix_v4
        self.prefix_v6       = prefix_v6
        self.vrrp_master_v4  = vrrp_master_v4
        self.vrrp_master_v6  = vrrp_master_v6
        self.vrrp_backup_v4  = vrrp_backup_v4
        self.vrrp_backup_v6  = vrrp_backup_v6
        self.vrrp_vip_v4     = vrrp_vip_v4
        self.vrrp_vip_v6     = vrrp_vip_v6

        self.tn4_branch_id   = None


class Branch:
    def __init__(self, ctx, nb_client):
        self.ctx = ctx
        self.cli = nb_client


    def add_vlan(self, branch_info):
        pass


    def delete_vlan(self, vlan_name):
        pass

