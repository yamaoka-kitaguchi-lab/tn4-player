class Slug:
    class Manufacturer:
        Cisco = "cisco"
        Juniper = "juniper"

    class Role:
        CoreSW = "core_sw"
        EdgeSW = "edge_sw"

    class Region:
        Ookayama = "ookayama"
        Suzukake = "suzukake"
        Tamachi  = "tamachi"

    class SiteGroup:
        Ishikawadai    = "ishikawadai"
        Midorigaoka    = "midorigaoka"
        OokayamaEast   = "ookayama-e"
        OokayamaNorth  = "ookayama-n"
        OokayamaSouth  = "ookayama-s"
        OokayamaWest   = "ookayama-w"
        Tamachi        = "tamachi"

    class Tag:
        Ansible                = "ansible"
        BPDUFilter             = "bpdu-filter"
        CoreDownstream         = "downlink"
        CoreMaster             = "mclag-master-core"
        CoreOokayamaMaster     = "mclag-master-co"
        CoreOokayamaSlave      = "mclag-slave-co"
        CoreSlave              = "mclag-slave-core"
        CoreSuzukakeMaster     = "mclag-master-cs"
        CoreSuzukakeSlave      = "mclag-slave-cs"
        EdgeUpstream           = "uplink"
        MgmtVlanBorderOokayama = "mgmt-vlan-bo"
        MgmtVlanBorderSuzukake = "mgmt-vlan-bs"
        MgmtVlanCoreOokayama   = "mgmt-vlan-co"
        MgmtVlanCoreSuzukake   = "mgmt-vlan-cs"
        MgmtVlanEdgeOokayama   = "mgmt-vlan-eo"
        MgmtVlanEdgeSuzukake   = "mgmt-vlan-es"
        PoE                    = "poe"
        Protect                = "protect"
        Rspan                  = "rspan"
        Storm5M                = "storm-5m"
        Test                   = "test"
        Upstream               = "uplink"
        VlanOokayama           = "vlan-o"
        VlanSuzukake           = "vlan-s"
        Wifi                   = "wifi"
        WifiMgmtVlanOokayama1  = "wlan-mgmt-vlan-o1"
        WifiMgmtVlanOokayama2  = "wlan-mgmt-vlan-o2"
        WifiMgmtVlanSuzukake   = "wlan-mgmt-vlan-s"
