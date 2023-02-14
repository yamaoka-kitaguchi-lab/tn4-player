from enum import Flag, auto


class StateBase:
    def __init__(self, nb_object=None):
        self.nb_object = nb_object


    def has(self, flag):
        return flag in self.nb_object


    def has_tag(self, tag):
        return tag in self.nb_object["tags"]


class VlanState(StateBase):
    def __init__(self, nb_object=None):
        super().__init__(nb_object)


class DeviceState:
    def __init__(self, nb_object=None):
        super().__init__(nb_object)


class InterfaceState:
    is_enabled          = None
    description         = None
    tags                = None
    is_tagged_vlan_mode = None
    tagged_vids         = None  # 802.1q VLAN IDs
    untagged_vid        = None

    def __init__(self, nb_object=None):
        super().__init__(nb_object)
        self.is_enabled  = nb_object["enabled"]
        self.description = nb_object["description"]
        self.tags        = nb_object["tags"]

        try:
            self.is_tagged_vlan_mode = nb_object["mode"]["value"] == "tagged"
        except KeyError:
            self.is_tagged_vlan_mode = False

        self.tagged_vids  = set(nb_object["tagged_vids"])
        self.untagged_vid = nb_object["untagged_vid"]


class Category(Flag):
    CREATE = auto()
    UPDATE = auto()
    DELETE = auto()


class NbckReport:
    category      = None
    current_state = None
    desired_state = None
    argument      = None
    message       = None

