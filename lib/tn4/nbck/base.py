from functools import reduce
import operator


class Condition(Flag):
    DONTCARE  = auto()
    IS        = auto()
    INCLUDE   = auto()
    INCLUDED  = auto()
    EXCLUDE   = auto()
    CONFLICT  = auto()


class ConditionalValue:
    def __init__(self, value=None, condition=Condition.DONTCARE):
        self.value     = value
        self.condition = condition


    def __add__(self, other):
        conflicted = False

        conflicted |= self.condition == Condition.IS and (
            other.condition == Condition.IS       and self.value != other.value
            or
            other.condition == Condition.INCLUDE  and other.value not in self.value  # need fix
            or
            other.condition == Condition.INCLUDED and self.value not in other.value  # need fix
            or
            other.condition == Condition.EXCLUDE  and self.value in other.value  # need fix
        )

        conflicted |= self.condition == Condition.INCLUDE and (
            other.condition == Condition.IS       and self.value not in other.value  # need fix
            or
            other.condition == Condition.INCLUDED and self.value not in other.value  # need fix
            or
            other.condition == Condition.EXCLUDE  and self.value in other.value  # need fix
        )

        conflicted |= self.condition == Condition.INCLUDED and (
            other.condition == Condition.IS       and self.value not in other.value  # need fix
            or
            other.condition == Condition.INCLUDE  and other.value not in self.value  # need fix
        )

        conflicted |= self.condition == Condition.EXCLUDE and (
            other.condition == Condition.IS       and other.value not in self.value  # need fix
            or
            other.condition == Condition.INCLUDE  and other.value not in self.value  # need fix
        )

        if conflicted:
            self.value     = None
            self.condition = Condition.CONFLICT


class NetBoxObjectBase:
    def __init__(self, nb_objs):
        self.all = nb_objs
        self.oids = [ obj["id"] for obj in nb_objs ]


    def __with_key(self, keylst, *values):
        matched = set()

        for obj in self.all:
            for value in values:
                obj_values = reduce(operator.getitem, keylst, obj)
                value in obj_values and matched.add(obj)

        return list(matched)


    def with_names(self, *names):
        return self.__with_key(["name"], *names)


    def with_tags(self, *tags):
        return self.__with_key(["tag"], *names)


class Vlans(NetBoxObjectBase):
    def __init__(self, nb_objs):
        super().__init__(nb_objs)
        self.vids = [ obj["vid"] for obj in nb_objs ]


    def with_vids(self, *vids):
        objs = sorted(super().__with_key(["vid"], *vids), key=lambda v: v["vid"], reverse=False)
        return Vlans(objs)


    def with_groups(self, *group_slugs):
        objs = sorted(super().__with_key(["group", "slug"], *group_slugs), key=lambda v: v["vid"], reverse=False)
        return Vlans(objs)


    def with_tags(self, *tags):
        objs = sorted(super().with_tags(*tags), key=lambda v: v["vid"], reverse=False))
        return Vlans(objs)


class Devices(NetBoxObjectBase):
    def __init__(self, nb_objs):
        super().__init__(nb_objs)
        self.hostnames = [ obj["name"] for obj in nb_objs ]


    def with_hostnames(self, *hostnames):
        objs = sorted(super().with_names(*hostnames), key=lambda d: d["name"], reverse=False))
        return Devices(objs)


    def with_sites(self, *sites):
        objs = sorted(super().__with_key(["site", "slug"], *sites), key=lambda d: d["name"], reverse=False)
        return Devices(objs)


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
