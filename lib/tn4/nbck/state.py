class InterfaceState:
    is_enabled          = None
    description         = None
    tags                = None
    is_tagged_vlan_mode = None
    tagged_vlanids      = None  # NetBox object IDs
    untagged_vlanid     = None  # NetBox object IDs
    tagged_vids         = None  # 802.1q VLAN IDs
    untagged_vid        = None
