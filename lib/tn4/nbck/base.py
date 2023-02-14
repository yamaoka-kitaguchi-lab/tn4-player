class NetBoxObjectBase:
    def __init__(self, nb_objs):
        self.all = nb_objs


    def with_tag(self, *tags):
        v = set()

        for vlan in self.all:
            for tag in tags:
                tag in vlan["tags"] and v.add(vlan)

        return sorted(list(v), key=lambda v: v["vid"], reverse=False)


class Vlans(NetBoxObjectBase):
    def __init__(self, nb_objs):
        super().__init__(nb_objs)


class Devices(NetBoxObjectBase):
    def __init__(self, nb_objs):
        super().__init__(nb_objs)


class Interfaces(NetBoxObjectBase):
    def __init__(self, nb_objs):
        super().__init__(nb_objs)


class Base:
    self.nb_vlan_objs      = None
    self.nb_device_objs    = None
    self.nb_interface_objs = None


    def is_equal(self, s, t, **keys):
        for k in keys:
            return False if s[k] != t[k]
        return True


