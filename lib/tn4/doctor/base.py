from functools import reduce
import operator


class NetBoxObjectBase:
    def __init__(self, nb_objs):
        self.all = nb_objs


    def __with_key(self, keylst, *values):
        matched = []
        matched_ids = []

        for obj in self.all.values():
            for value in values:
                obj_values = reduce(operator.getitem, keylst, obj)
                if value in obj_values and obj["id"] not in matched_ids:
                    matched.append(obj)

        return matched


    def with_names(self, *names):
        return self.__with_key(["name"], *names)


    def with_tags(self, *tags):
        return self.__with_key(["tags"], *tags)


class Vlans(NetBoxObjectBase):
    def __init__(self, nb_objs):
        super().__init__(nb_objs)

        if type(nb_objs) == dict:
            self.vids = [ obj["vid"] for obj in nb_objs.values() ]

        if type(nb_objs) == list:
            self.vids = [ obj["vid"] for obj in nb_objs ]


    def with_vids(self, *vids):
        objs = sorted(super().__with_key(["vid"], *vids), key=lambda v: v["vid"], reverse=False)
        return Vlans(objs)


    def with_groups(self, *group_slugs):
        objs = sorted(super().__with_key(["group", "slug"], *group_slugs), key=lambda v: v["vid"], reverse=False)
        return Vlans(objs)


    def with_tags(self, *tags):
        objs = sorted(super().with_tags(*tags), key=lambda v: v["vid"], reverse=False)
        return Vlans(objs)


class Devices(NetBoxObjectBase):
    def __init__(self, nb_objs):
        super().__init__(nb_objs)
        self.hostnames = [ obj["name"] for obj in nb_objs.values() ]


    def with_hostnames(self, *hostnames):
        objs = sorted(super().with_names(*hostnames), key=lambda d: d["name"], reverse=False)
        return Devices(objs)


    def with_sites(self, *sites):
        objs = sorted(super().__with_key(["site", "slug"], *sites), key=lambda d: d["name"], reverse=False)
        return Devices(objs)


class Interfaces(NetBoxObjectBase):
    def __init__(self, nb_objs):
        super().__init__(nb_objs)


class Base:
    def __init__(self):
        self.nb_vlans      = None
        self.nb_devices    = None
        self.nb_interfaces = None


    def is_equal(self, s, t, **keys):
        for k in keys:
            if s[k] != t[k]:
                return False
        return True
