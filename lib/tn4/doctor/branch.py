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

        self.vlan_id         = None  # netbox VLAN object id
        self.vlan_vid        = None  # 802.1Q vlanid
        self.cidr_len_v4     = None
        self.cidr_len_v6     = None
        self.fhrp_group_id   = None  # netbox FHRP Group object id


class Branch:
    def __init__(self, ctx, nb_client, branch_info, is_new_branch=True):
        self.ctx  = ctx
        self.cli  = nb_client
        self.info = branch_info

        for vlan in self.cli.vlans.all_vlans.values():
            if vlan["name"] == self.info.vlan_name:
                 self.info.vlan_id  = vlan["id"]
                 self.info.vlan_vid = vlan["vid"]

        if self.info.vlan_vid is not None:
            vlan = self.cli.vlans.all_vlans[self.info.vlan_id]

            if vlan["custom_fields"][NB_BRANCH_ID_KEY] is not None:
                self.info.tn4_branch_id = vlan["custom_fields"][NB_BRANCH_ID_KEY]
            else:
                s  = self.info.vlan_name.strip().replace(' ', '_')
                s += '%' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
                self.info.tn4_branch_id = f"{s}"

        self.info.cidr_len_v4 = self.info.prefix_v4.split('/')[-1]
        self.info.cidr_len_v6 = self.info.prefix_v6.split('/')[-1]


    def __is_ok_or_not(self, code):
        if 200 <= code < 300:
            return True

        return False


    def validate_branch_info(self):
        # todo: check if any item already exist
        return


    def commit_branch_id(self):
        res, code = self.cli.vlans.update_custom_fields(self.ctx, self.info.vlan_id, **{
            NB_BRANCH_ID_KEY: self.info.tn4_branch_id
        })

        is_ok = self.__is_ok_or_not(code)

        if is_ok:
            result = [{ "URL": res[0]["url"] if len(res) > 0 else None }]
        else:
            result = [{ "Error": code }]

        return result, is_ok


    def add_branch_prefixes(self):
        results, is_all_ok = [], True

        for prefix in [ self.info.prefix_v4, self.info.prefix_v6 ]:
            if prefix is None:
                continue

            res, code = self.cli.prefixes.create(self.ctx, prefix, **{
                "role":          Slug.Role.Branch,
                "vlan":          { "id": self.info.vlan_id },
                "description":   "",
                "tags":          [],
                "custom_fields": { NB_BRANCH_ID_KEY: self.info.tn4_branch_id },
            })

            is_all_ok &= self.__is_ok_or_not(code)

            if not is_all_ok:
                results += [{ "Prefix": prefix, "Error": code }]
                return results, is_all_ok

            results += [{ "Prefix": prefix, "URL": res[0]["url"] if len(res) > 0 else None }]

        return results, is_all_ok


    def add_vrrp_group(self):
        res, code = self.cli.fhrp_groups.create(self.ctx, self.info.vrrp_group_id, **{
            "description":   "",
            "tags":          [],
            "custom_fields": { NB_BRANCH_ID_KEY: self.info.tn4_branch_id },
        })

        is_ok = self.__is_ok_or_not(code)

        if is_ok:
            result = [{ "VRRP Group": self.info.vrrp_group_id,
                        "URL": res[0]["url"] if len(res) > 0 else None }]
            self.info.fhrp_group_id = res[0]["id"]

        else:
            result = [{ "VRRP Group": self.info.vrrp_group_id, "Code": code }]

        return result, is_ok


    def add_vrrp_ip_address(self, address, cidr_len, tag_slug, fhrp_group_id=None):
        address += f"/{cidr_len}"

        request = {
            "description":   "",
            "tags":          [{ "slug": tag_slug }],
            "role":          Slug.Role.VRRP,
            "custom_fields": { NB_BRANCH_ID_KEY: self.info.tn4_branch_id },
        }

        if fhrp_group_id is not None:
            request |= {
                "assigned_object_type": "ipam.fhrpgroup",
                "assigned_object_id":   fhrp_group_id
            }

        res, code = self.cli.addresses.create(self.ctx, address, **request)

        is_ok   = self.__is_ok_or_not(code)

        if is_ok:
            result  = [{ "Address": address, "URL": res[0]["url"] if len(res) > 0 else None }]
        else:
            result = [{ "Address": address, "Error": code }]

        return result, is_ok


    def add_vrrp_ip_addresses(self):
        results, is_all_ok = [], True

        result, is_ok = self.add_vrrp_ip_address(
            self.info.vrrp_vip_v4, self.info.cidr_len_v4, Slug.Tag.VRRPVIP, self.info.fhrp_group_id
        )

        results += result

        if not is_ok:
            return results, is_ok

        if self.info.vrrp_vip_v6:
            result, is_ok = self.add_vrrp_ip_address(
                self.info.vrrp_vip_v6, self.info.cidr_len_v6, Slug.Tag.VRRPVIP, self.info.fhrp_group_id
            )

            is_all_ok &= is_ok
            results += result

            if not is_all_ok:
                return results, is_all_ok

        bulk_args =  [
            ( self.info.vrrp_master_v4, self.info.cidr_len_v4, Slug.Tag.VRRPMaster ),
            ( self.info.vrrp_backup_v4, self.info.cidr_len_v4, Slug.Tag.VRRPBackup ),
        ]

        if self.info.vrrp_master_v6 is not None:
            bulk_args += [( self.info.vrrp_master_v6, self.info.cidr_len_v6, Slug.Tag.VRRPMaster )]

        if self.info.vrrp_backup_v6 is not None:
            bulk_args += [( self.info.vrrp_backup_v6, self.info.cidr_len_v6, Slug.Tag.VRRPBackup )]


        for args in bulk_args:
            result, is_ok = self.add_vrrp_ip_address(*args)

            is_all_ok &= is_ok
            results += result

            if not is_all_ok:
                return results, is_all_ok

        return results, is_all_ok



    def delete_vlan(self):
        self.cli.vlans.delete_by_name(branch_info.vlan_name)


    def delete_prefix(self):
        # todo: delete prefix object from custom_fields
        pass


    def delete_ip_address(self):
        # todo: delete ip address object from custom_fields
        pass
