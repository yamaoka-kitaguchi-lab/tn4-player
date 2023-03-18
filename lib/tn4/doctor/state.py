from enum import Flag, auto


class StateBase:
    def __init__(self, nb_object=None):
        self.nb_object = nb_object


    def has(self, flag):
        return flag in self.nb_object and self.nb_object[flag]


    def has_tag(self, tag):
        return tag in self.nb_object["tags"]


    def is_equal(self, state, attrs=[]):
        if len(attrs) == 0:
            attrs = [ k for k in self.__dict__.keys() if k[:2] != "__" and k[-2:] != "__" ]

        for attr in attrs:
            if getattr(self, attr) != getattr(state, attr):
                return False
        return True


    def dump(self):
        ignored = ["dump", "has", "has_tag", "is_equal", "nb_object"]

        return sorted({
            k: v
            for k, v in self.__dict__.items() if k not in ignored
        })


class VlanState(StateBase):
    def __init__(self, nb_object=None):
        super().__init__(nb_object)


class DeviceState(StateBase):
    def __init__(self, nb_object=None):
        super().__init__(nb_object)


class InterfaceState(StateBase):
    def __init__(self, nb_object=None):
        super().__init__(nb_object)
        self.is_enabled     = nb_object["enabled"]
        self.description    = nb_object["description"]
        self.tags           = nb_object["tags"]
        self.tagged_oids    = nb_object["tagged_vlanids"]   # NB object ID
        self.untagged_oid   = nb_object["untagged_vlanid"]  # NB object ID

        if "native_vlanid" in nb_object:
            self.untagged_oid = nb_object["native_vlanid"]  # NB object ID

        self.interface_mode = None
        if nb_object["mode"] is not None:
            self.interface_mode = nb_object["mode"]["value"]  # "access", "tagged", or "tagged-all"

