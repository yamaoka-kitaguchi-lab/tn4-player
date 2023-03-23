import random
import string


class BranchInfo:
    def __init__(self, vlan_name,
                 prefix_v4=None, vrrp_master_v4=None, vrrp_backup_v4=None, vrrp_vip_v4=None,
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

        self.tn4_branch_id   = self.__generate_tn4_branch_id(vlan_name)


    def __generate_tn4_branch_id(self, vlan_name):
        s  = vlan_name.strip().replace(' ', '_')
        s += '%' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
        return f"{s}"


class Branch:
    def __init__(self, ctx, nb_client):
        self.ctx = ctx
        self.cli = nb_client


    def get_tn4_branch_id(self, branch_info):
        for vlan in self.cli.vlans.all_vlans:
            if vlan["name"] == branch_info.vlan_name:
                if "tn4_branch_id" in vlan["custom_fields"]:
                     branch_info.tn4_branch_id = vlan["custom_fields"]["tn4_branch_id"]
                     return True
                else:
                    return False
        return False


    def update_vlan(self, branch_info):
        # todo: update tag
        # todo: update custom_fields
        pass


    def delete_vlan(self, branch_info):
        self.cli.vlans.delete_by_name(branch_info.vlan_name)


    def add_prefix(self, branch_info):
        # todo: add prefix with tags, custom_fields
        pass


    def delete_prefix(self, branch_info):
        # todo: delete prefix object from custom_fields
        pass


    def add_ip_address(self, branch_info):
        # todo: add ip address with tags, custom_fields
        pass


    def delete_ip_address(self, branch_info):
        # todo: delete ip address object from custom_fields
        pass
