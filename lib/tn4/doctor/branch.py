import random
import string


from tn4.netbox.slug import Slug


NB_BRANCH_ID_KEY = "tn4_branch_id"  # Custom Field's attribtue


class BranchInfo:
    def __init__(self, vlan_name, vrrp_group_id,
                 prefix_v4=None, vrrp_master_v4=None, vrrp_backup_v4=None, vrrp_vip_v4=None,
                 prefix_v6=None, vrrp_master_v6=None, vrrp_backup_v6=None, vrrp_vip_v6=None):
        self.vlan_name       = vlan_name
        self.vrrp_group_id   = vrrp_group_id

        self.prefix_v4       = prefix_v4
        self.prefix_v6       = prefix_v6
        self.vrrp_master_v4  = vrrp_master_v4
        self.vrrp_master_v6  = vrrp_master_v6
        self.vrrp_backup_v4  = vrrp_backup_v4
        self.vrrp_backup_v6  = vrrp_backup_v6
        self.vrrp_vip_v4     = vrrp_vip_v4
        self.vrrp_vip_v6     = vrrp_vip_v6

        self.tn4_branch_id   = None

        self.vlan_id         = None  # netbox vlan object id
        self.vlan_vid        = None  # 802.1Q vlanid
        self.vrrp_vip_ids    = []


class Branch:
    def __init__(self, ctx, nb_client, branch_info, is_new_branch=True):
        self.ctx  = ctx
        self.cli  = nb_client
        self.info = branch_info

        for vlan in self.cli.vlans.all_vlans:
            if vlan["name"] == branch_info.vlan_name:
                 self.info.vlan_id  = vlan["id"]
                 self.info.vlan_vid = vlan["vid"]

        if self.info.vlan_vid is not None:
            vlan = self.cli.vlans.all_vlans[self.info.vlan_id]
            if NB_BRANCH_ID_KEY in vlan["custom_fields"]:
                self.info.tn4_branch_id = vlan["custom_fields"][NB_BRANCH_ID_KEY]
            else:
                s  = vlan_name.strip().replace(' ', '_')
                s += '%' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
                self.info.tn4_branch_id = f"{s}"


    def __is_ok_or_not(self, code):
        if 200 <= code < 300:
            return True

        return False


    def validate_branch_info(self):
        # todo: check if any item already exist


    def commit_branch_id(self):
        _, code = self.cli.vlans.update_custom_fields(self.ctx, self.info.vlan_id, {
            NB_BRANCH_ID_KEY: self.info.tn4_branch_id
        })

        return self.__is_ok_or_not(code)


    def add_prefix(self):
        is_all_ok = True

        for prefix in [ self.info.prefix_v4, self.info.prefix_v6 ]:
            if prefix is None:
                continue

            _, code = self.cli.prefix.create(self.ctx, prefix, {
                "role":          { "slug": Slug.Role.Branch },
                "vlan":          { "id": self.info.vlan_id },
                "description":   "",
                "tags":          [],
                "custom_fields": { NB_BRANCH_ID_KEY: self.info.tn4_branch_id },
            })

            is_all_ok &= self.__is_ok_or_not(code)

        return is_all_ok


    def add_ip_address(self):
        is_all_ok = True

        for address in [ self.info.vrrp_vip_v4, self.info.vrrp_vip_v6 ]:
            if address is None:
                continue

            if self.cli.addresses.all_addresses:

            res, code = self.cli.address.create(self.ctx, address, {
                "description":   "",
                "tags":          [{ "slug": Slug.Tag.VRRPVIP }],
                "role":          { "slug": Slug.Role.VIP },
                "custom_fields": { NB_BRANCH_ID_KEY: self.info.tn4_branch_id },
            })

            is_ok &= self.__is_ok_or_not(code)

            if is_ok:
                self.vrrp_vip_ids.append(res["id"])

            is_all_ok &= is_ok


        for address in [ self.info.vrrp_master_v4, self.info.vrrp_master_v4 ]:
            if address is None:
                continue

            _, code = self.cli.address.create(self.ctx, address, {
                "description":   "",
                "tags":          [{ "slug": Slug.Tag.VRRPMaster }],
                "role":          { "slug": Slug.Role.VRRP },
                "custom_fields": { NB_BRANCH_ID_KEY: self.info.tn4_branch_id },
            })

            is_all_ok &= self.__is_ok_or_not(code)


        for address in [ self.info.vrrp_backup_v4, self.info.vrrp_backup_v6 ]:
            if address is None:
                continue

            _, code = self.cli.address.create(self.ctx, address, {
                "description":   "",
                "tags":          [{ "slug": Slug.Tag.VRRPBackup }],
                "role":          { "slug": Slug.Role.VRRP },
                "custom_fields": { NB_BRANCH_ID_KEY: self.info.tn4_branch_id },
            })

            is_all_ok &= self.__is_ok_or_not(code)

        return is_all_ok


    def add_fhrp_group(self):
        is_all_ok = True

        for address in [ self.info.vrrp_vip_v4, self.info.vrrp_vip_v6 ]:
            if address is None:
                continue

            vip_id  = self.vrrp_vip_ids.pop()
            _, code = self.cli.fhrp_groups.create(self.ctx, self.vrrp_vip_ids, {
                "description":   "",
                "tags":          [],
                "ip_addresses":  [{ "id": vip_id }],
                "custom_fields": { NB_BRANCH_ID_KEY: self.info.tn4_branch_id },
            })

            is_all_ok &= self.__is_ok_or_not(code)

        return is_all_ok






    def delete_vlan(self):
        self.cli.vlans.delete_by_name(branch_info.vlan_name)


    def delete_prefix(self):
        # todo: delete prefix object from custom_fields
        pass


    def delete_ip_address(self):
        # todo: delete ip address object from custom_fields
        pass
