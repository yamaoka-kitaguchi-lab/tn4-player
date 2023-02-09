class InterfaceState:
    is_enabled          = None
    description         = None
    tags                = None
    is_tagged_vlan_mode = None
    tagged_vlanids      = None  # NetBox object IDs
    untagged_vlanid     = None  # NetBox object IDs
    tagged_vids         = None  # 802.1q VLAN IDs
    untagged_vid        = None

    def __init__(self, nb_interface_obj=None):
        self.is_enabled          = nb_interface_obj["enabled"]
        self.description         = nb_interface_obj["description"]
        self.tags                = nb_interface_obj["tags"]

        try:
            self.is_tagged_vlan_mode = nb_interface_obj["mode"]["value"] == "tagged"
        except KeyError:
            self.is_tagged_vlan_mode = False

        self.tagged_vlanids  = nb_interface_obj["tagged_vlanids"]
        self.untagged_vlanid = nb_interface_obj["untagged_vlanid"]
        self.tagged_vids  = nb_interface_obj["tagged_vids"]
        self.untagged_vid = nb_interface_obj["untagged_vid"]

