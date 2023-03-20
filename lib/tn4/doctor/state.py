from enum import Flag, auto


class StateBase:
    def __init__(self, nb_object=None):
        self.nb_object = nb_object


    def has(self, flag):
        return flag in self.nb_object and self.nb_object[flag]


    def has_tag(self, tag):
        return tag in self.nb_object["tags"]


    def is_equal(self, state, attrs=[]):
        ignored = [ "nb_object", "is_lag_member" ]
        if len(attrs) == 0:
            attrs = [ k for k in self.__dict__.keys() if k not in ignored ]

        for attr in attrs:
            v1, v2 = getattr(self, attr), getattr(state, attr)

            if list in [ type(v1), type(v2) ]:
                v1 = set() if v1 is None else set(v1)
                v2 = set() if v2 is None else set(v2)

            if v1 != v2:
                return False

        return True


    def dump(self):
        ignored = ["dump", "has", "has_tag", "is_equal", "nb_object"]

        return {
            k: v if type(v) is not list else sorted(v)
            for k, v in self.__dict__.items() if k not in ignored
        }


class VlanState(StateBase):
    def __init__(self, nb_object=None):
        super().__init__(nb_object)


class DeviceState(StateBase):
    def __init__(self, nb_object=None):
        super().__init__(nb_object)


    def to_rich(self, *args):
        return "-"


class InterfaceState(StateBase):
    def __init__(self, nb_object=None):
        super().__init__(nb_object)
        self.is_enabled   = nb_object["enabled"]
        self.tags         = nb_object["tags"]
        self.tagged_oids  = nb_object["tagged_vlanids"]   # NB object ID
        self.untagged_oid = nb_object["untagged_vlanid"]  # NB object ID

        self.is_lag_member = nb_object["is_lag_member"]

        self.description = nb_object["description"]
        if self.description == '':
            self.description = None

        if "native_vlanid" in nb_object:
            self.untagged_oid = nb_object["native_vlanid"]  # NB object ID

        self.interface_mode = None
        if nb_object["mode"] is not None:
            self.interface_mode = nb_object["mode"]["value"]  # "access", "tagged", or "tagged-all"


    def to_rich(self, oid_to_vid):
        resolver = lambda *oids: sorted([ oid_to_vid[oid] for oid in oids ])

        enabled = "Y" if self.is_enabled else "N"
        mode    = "-" if self.interface_mode is None else self.interface_mode
        vlan_t  = "-" if self.tagged_oids is None else ", ".join(resolver(*self.tagged_oids))
        vlan_u  = "-" if self.untagged_oid is None else resolver(self.untagged_oid)[0]
        tags    = "-" if len(self.tags) == 0 else ", ".join(self.tags)
        desc    = "-" if self.description is None else self.description

        return "\n".join([
            f"[bold]Enabled:[/bold] {enabled}",
            f"[bold]Mode:   [/bold] {mode}",
            f"[bold]VLAN(U):[/bold] {vlan_u}",
            f"[bold]VLAN(T):[/bold] {vlan_t}",
            f"[bold]Tags:   [/bold] {tags}",
            f"[bold]Desc:   [/bold] {desc}",
        ])

