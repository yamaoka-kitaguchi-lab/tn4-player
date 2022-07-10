    def get_all_vlans(self, use_cache=True):
        if not use_cache or not self.all_vlans:
            all_vlans = self.query("/ipam/vlans/")
            for vlan in all_vlans:
                vlan["tags"] = [tag["slug"] for tag in vlan["tags"]]
                if Slug.tag_mgmt_vlan_edge_ookayama in vlan["tags"]:
                    self.mgmt_vlanid_eo = vlan["id"]
                if Slug.tag_mgmt_vlan_edge_suzukake in vlan["tags"]:
                    self.mgmt_vlanid_es = vlan["id"]
                if Slug.tag_mgmt_vlan_core_ookayama in vlan["tags"]:
                    self.mgmt_vlanid_co = vlan["id"]
                if Slug.tag_mgmt_vlan_core_suzukake in vlan["tags"]:
                    self.mgmt_vlanid_cs = vlan["id"]

                if Slug.tag_wifi_mgmt_vlan_ookayama1 in vlan["tags"]:
                    self.wifi_mgmt_vlanid_o1 = vlan["id"]
                if Slug.tag_wifi_mgmt_vlan_ookayama2 in vlan["tags"]:
                    self.wifi_mgmt_vlanid_o2 = vlan["id"]
                if Slug.tag_wifi_mgmt_vlan_suzukake in vlan["tags"]:
                    self.wifi_mgmt_vlanid_s = vlan["id"]
                if Slug.tag_wifi in vlan["tags"] and vlan["status"]["value"] == "active":
                    if Slug.tag_vlan_ookayama in vlan["tags"]:
                        self.wifi_vlanids_o.append(vlan["id"])
                    if Slug.tag_vlan_suzukake in vlan["tags"]:
                        self.wifi_vlanids_s.append(vlan["id"])

                self.all_vlans[str(vlan["id"])] = vlan
        return self.all_vlans
