class NetBoxObjectBase:
    def __init__(self, nb_objs):
        self.all = nb_objs


    def __with_key(self, keystr, *values):
        matched = set()

        for obj in self.all:



    def with_names(self, *names):
        return self.__with_key("name", *names)



    def with_tags(self, *tags):
        o = set()

        for obj in self.all:
            for tag in tags:
                tag in obj["tags"] and o.add(obj)

        return list(o)


class Vlans(NetBoxObjectBase):
    def __init__(self, nb_objs):
        super().__init__(nb_objs)


    def with_tags(self, *tags):
        return sorted(super().with_tags(*tags), key=lambda v: v["vid"], reverse=False))


class Devices(NetBoxObjectBase):
    def __init__(self, nb_objs):
        super().__init__(nb_objs)


    def with_sites(self, *sites):
        d = set()

        for device in self.all:
            for site in sites:
                site == device["site"]["slug"] and d.add(device)

        return sorted(list(d), key=lambda d: d["name"], reverse=False)


class Interfaces(NetBoxObjectBase):
    def __init__(self, nb_objs):
        super().__init__(nb_objs)


class Base:
    self.nb_vlans      = None
    self.nb_devices    = None
    self.nb_interfaces = None


    def is_equal(self, s, t, **keys):
        for k in keys:
            return False if s[k] != t[k]
        return True


