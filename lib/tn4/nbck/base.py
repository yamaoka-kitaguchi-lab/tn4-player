from functools import reduce
import operator


class NetBoxObjectBase:
    def __init__(self, nb_objs):
        self.all = nb_objs


    def __with_key(self, keylst, *values):
        matched = set()

        for obj in self.all:
            for value in values:
                if value in reduce(operator.getitem, keylst, obj):
                    matched.add(obj)

        return list(matched)


    def with_names(self, *names):
        return self.__with_key(["name"], *names)


    def with_tags(self, *tags):
        return self.__with_key(["tag"], *names)


class Vlans(NetBoxObjectBase):
    def __init__(self, nb_objs):
        super().__init__(nb_objs)


    def with_tags(self, *tags):
        return sorted(super().with_tags(*tags), key=lambda v: v["vid"], reverse=False))


class Devices(NetBoxObjectBase):
    def __init__(self, nb_objs):
        super().__init__(nb_objs)


    def with_sites(self, *sites):
        return sorted(super().__with_key(["site", "slug"], *sites), key=lambda d: d["name"], reverse=False)


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


